import importlib.util
import io
import os
import shlex
import signal
import socket
import subprocess
import sys
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CODEX_HELPER = ROOT / "distributions/codex/skills/browser-workflows/scripts/with_server.py"
CLAUDE_HELPER = ROOT / "distributions/claude/skills/webapp-testing/scripts/with_server.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("with_server_under_test", CODEX_HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unused_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def process_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def wait_for_process_exit(pid, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_exists(pid):
            return True
        time.sleep(0.05)
    return not process_exists(pid)


def force_stop(pid):
    if process_exists(pid):
        os.kill(pid, signal.SIGKILL)
        wait_for_process_exit(pid)


class WithServerIntegrationTest(unittest.TestCase):
    def run_helper(self, helper, server_script, port, child_command, timeout=3):
        server_command = f"{shlex.quote(sys.executable)} {shlex.quote(str(server_script))}"
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(helper),
                "--server",
                server_command,
                "--port",
                str(port),
                "--timeout",
                str(timeout),
                "--",
                *child_command,
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )

    def test_distributed_helpers_are_identical(self):
        self.assertEqual(CODEX_HELPER.read_bytes(), CLAUDE_HELPER.read_bytes())

    @unittest.skipUnless(os.name == "posix", "integration command uses POSIX shell quoting")
    def test_large_server_output_does_not_block_port_readiness_and_server_is_reaped(self):
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            pid_file = temp / "server.pid"
            child_marker = temp / "child-complete"
            port = unused_port()
            server_script = temp / "noisy_server.py"
            server_script.write_text(
                "import os\n"
                "import socket\n"
                "import sys\n"
                f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
                "sys.stdout.write('x' * (1024 * 1024 + 65536))\n"
                "sys.stdout.flush()\n"
                "listener = socket.socket()\n"
                "listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                f"listener.bind(('127.0.0.1', {port}))\n"
                "listener.listen()\n"
                "while True:\n"
                "    connection, _address = listener.accept()\n"
                "    connection.close()\n",
                encoding="utf-8",
            )
            child = [
                sys.executable,
                "-c",
                f"from pathlib import Path; Path({str(child_marker)!r}).write_text('done')",
            ]

            completed = self.run_helper(CODEX_HELPER, server_script, port, child)
            pid = int(pid_file.read_text(encoding="utf-8"))
            try:
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(child_marker.read_text(encoding="utf-8"), "done")
                self.assertTrue(wait_for_process_exit(pid), f"server process {pid} was not reaped")
            finally:
                force_stop(pid)

    @unittest.skipUnless(os.name == "posix", "integration command uses POSIX shell quoting")
    def test_early_server_exit_reports_return_code_and_log_excerpt(self):
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            server_script = temp / "failed_server.py"
            server_script.write_text(
                "import sys\n"
                "print('startup exploded', flush=True)\n"
                "raise SystemExit(7)\n",
                encoding="utf-8",
            )
            completed = self.run_helper(
                CODEX_HELPER,
                server_script,
                unused_port(),
                [sys.executable, "-c", "raise SystemExit(0)"],
                timeout=2,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("exited with code 7", completed.stderr)
            self.assertIn("startup exploded", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    @unittest.skipUnless(os.name == "posix", "integration command uses POSIX shell quoting")
    def test_child_status_is_propagated_and_server_is_cleaned_up(self):
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            pid_file = temp / "server.pid"
            port = unused_port()
            server_script = temp / "server.py"
            server_script.write_text(
                "import os\n"
                "import socket\n"
                f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
                "listener = socket.socket()\n"
                "listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                f"listener.bind(('127.0.0.1', {port}))\n"
                "listener.listen()\n"
                "while True:\n"
                "    connection, _address = listener.accept()\n"
                "    connection.close()\n",
                encoding="utf-8",
            )
            completed = self.run_helper(
                CODEX_HELPER,
                server_script,
                port,
                [sys.executable, "-c", "raise SystemExit(7)"],
            )
            pid = int(pid_file.read_text(encoding="utf-8"))
            try:
                self.assertEqual(completed.returncode, 7, completed.stderr)
                self.assertTrue(wait_for_process_exit(pid), f"server process {pid} was not reaped")
            finally:
                force_stop(pid)

    @unittest.skipUnless(os.name == "posix", "integration uses POSIX shell and signals")
    def test_early_exit_force_kills_stubborn_background_server(self):
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            pid_file = temp / "server.pid"
            port = unused_port()
            server_script = temp / "stubborn_server.py"
            server_script.write_text(
                "import os\n"
                "import signal\n"
                "import socket\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                f"open({str(pid_file)!r}, 'w').write(str(os.getpid()))\n"
                "listener = socket.socket()\n"
                "listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                f"listener.bind(('127.0.0.1', {port}))\n"
                "listener.listen()\n"
                "while True:\n"
                "    connection, _address = listener.accept()\n"
                "    connection.close()\n",
                encoding="utf-8",
            )
            server_command = (
                f"{shlex.quote(sys.executable)} {shlex.quote(str(server_script))} &"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CODEX_HELPER),
                    "--server",
                    server_command,
                    "--port",
                    str(port),
                    "--timeout",
                    "2",
                    "--",
                    sys.executable,
                    "-c",
                    "raise SystemExit(0)",
                ],
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            pid = int(pid_file.read_text(encoding="utf-8"))
            try:
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertTrue(wait_for_process_exit(pid), f"server process {pid} survived cleanup")
            finally:
                force_stop(pid)

    @unittest.skipUnless(os.name == "posix", "integration command uses POSIX shell quoting")
    def test_occupied_port_rejects_server_and_child_without_launching(self):
        with TemporaryDirectory() as temp_dir, socket.socket() as listener:
            temp = Path(temp_dir)
            server_marker = temp / "server-started"
            child_marker = temp / "child-started"
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            server_script = temp / "would_start.py"
            server_script.write_text(
                "import time\n"
                "from pathlib import Path\n"
                f"Path({str(server_marker)!r}).write_text('started')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            completed = self.run_helper(
                CODEX_HELPER,
                server_script,
                port,
                [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(child_marker)!r}).write_text('started')",
                ],
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn(f"Port {port} is already occupied", completed.stderr)
            self.assertFalse(server_marker.exists())
            self.assertFalse(child_marker.exists())

    @unittest.skipUnless(os.name == "posix", "integration command uses POSIX shell quoting")
    def test_bound_non_listening_port_rejects_server_and_child_without_launching(self):
        with TemporaryDirectory() as temp_dir, socket.socket() as owner:
            temp = Path(temp_dir)
            server_marker = temp / "server-started"
            child_marker = temp / "child-started"
            owner.bind(("127.0.0.1", 0))
            port = owner.getsockname()[1]
            server_script = temp / "would_start.py"
            server_script.write_text(
                "import time\n"
                "from pathlib import Path\n"
                f"Path({str(server_marker)!r}).write_text('started')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            completed = self.run_helper(
                CODEX_HELPER,
                server_script,
                port,
                [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(child_marker)!r}).write_text('started')",
                ],
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn(f"Port {port} is already occupied", completed.stderr)
            self.assertFalse(server_marker.exists())
            self.assertFalse(child_marker.exists())
            self.assertIn("Stopping 0 server(s)", completed.stdout)
            self.assertIn("All servers stopped", completed.stdout)

    @unittest.skipUnless(os.name == "posix", "SIGINT integration uses POSIX process signals")
    def test_interrupted_child_command_still_cleans_up_server(self):
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            server_pid_file = temp / "server.pid"
            child_pid_file = temp / "child.pid"
            port = unused_port()
            server_script = temp / "server.py"
            child_script = temp / "child.py"
            server_script.write_text(
                "import os\n"
                "import socket\n"
                f"open({str(server_pid_file)!r}, 'w').write(str(os.getpid()))\n"
                "listener = socket.socket()\n"
                "listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
                f"listener.bind(('127.0.0.1', {port}))\n"
                "listener.listen()\n"
                "while True:\n"
                "    connection, _address = listener.accept()\n"
                "    connection.close()\n",
                encoding="utf-8",
            )
            child_script.write_text(
                "import os\n"
                "import time\n"
                f"open({str(child_pid_file)!r}, 'w').write(str(os.getpid()))\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            server_command = f"{shlex.quote(sys.executable)} {shlex.quote(str(server_script))}"
            helper = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    str(CODEX_HELPER),
                    "--server",
                    server_command,
                    "--port",
                    str(port),
                    "--timeout",
                    "3",
                    "--",
                    sys.executable,
                    str(child_script),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not child_pid_file.exists():
                time.sleep(0.05)
            self.assertTrue(child_pid_file.exists(), "child command did not start")
            server_pid = int(server_pid_file.read_text(encoding="utf-8"))
            child_pid = int(child_pid_file.read_text(encoding="utf-8"))
            try:
                helper.send_signal(signal.SIGINT)
                self.assertNotEqual(helper.wait(timeout=10), 0)
                self.assertTrue(
                    wait_for_process_exit(server_pid),
                    f"server process {server_pid} survived helper interruption",
                )
            finally:
                if helper.poll() is None:
                    helper.kill()
                    helper.wait()
                force_stop(server_pid)
                force_stop(child_pid)

    def test_claude_instructions_resolve_installed_helper_without_changing_project_cwd(self):
        instructions = (
            ROOT / "distributions/claude/skills/webapp-testing/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "Resolve the absolute directory containing this `SKILL.md` file into `SKILL_ROOT`.",
            instructions,
        )
        self.assertIn("Keep the user's project as the current working directory.", instructions)
        self.assertIn('python3 "$SKILL_ROOT/scripts/with_server.py"', instructions)
        self.assertNotIn("python scripts/with_server.py", instructions)


class WithServerArgumentTest(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def parse_port(self, value):
        return self.helper.parse_args(
            ["--server", "serve", "--port", value, "--", "child"]
        )

    def test_port_boundaries_are_accepted(self):
        for value in ("1", "65535"):
            with self.subTest(value=value):
                self.assertEqual(self.parse_port(value).ports, [int(value)])

    def test_invalid_ports_are_rejected_by_argparse_without_traceback(self):
        for value in ("0", "-1", "65536", "not-an-integer"):
            with self.subTest(value=value):
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                    self.parse_port(value)
                output = stderr.getvalue()
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("port must be an integer from 1 to 65535", output)
                self.assertNotIn("Traceback", output)


class WithServerWindowsTest(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def test_windows_port_preflight_uses_exclusive_address_option(self):
        probe = mock.MagicMock()
        socket_context = mock.MagicMock()
        socket_context.__enter__.return_value = probe
        with mock.patch.object(self.helper.os, "name", "nt"), mock.patch.object(
            self.helper.socket,
            "SO_EXCLUSIVEADDRUSE",
            4,
            create=True,
        ), mock.patch.object(
            self.helper.socket,
            "socket",
            return_value=socket_context,
        ) as socket_constructor:
            port_can_be_bound = getattr(self.helper, "port_can_be_bound", None)
            self.assertTrue(callable(port_can_be_bound), "port preflight helper is missing")
            self.assertTrue(port_can_be_bound(8765))
        socket_constructor.assert_called_once_with(
            self.helper.socket.AF_INET,
            self.helper.socket.SOCK_STREAM,
        )
        probe.setsockopt.assert_called_once_with(
            self.helper.socket.SOL_SOCKET,
            4,
            1,
        )
        probe.bind.assert_called_once_with(("127.0.0.1", 8765))

    def test_windows_start_uses_new_process_group_creation_flag(self):
        process = mock.sentinel.process
        log_file = mock.sentinel.log_file
        with mock.patch.object(self.helper.os, "name", "nt"), mock.patch.object(
            self.helper.subprocess,
            "CREATE_NEW_PROCESS_GROUP",
            512,
            create=True,
        ), mock.patch.object(self.helper.subprocess, "Popen", return_value=process) as popen:
            self.assertIs(self.helper.start_server("serve", log_file), process)
        popen.assert_called_once_with(
            "serve",
            shell=True,
            stdout=log_file,
            stderr=self.helper.subprocess.STDOUT,
            creationflags=512,
        )

    def test_windows_stop_signals_group_and_falls_back_to_terminate(self):
        for signal_error in (None, OSError("no console group")):
            with self.subTest(signal_error=signal_error):
                process = mock.Mock(pid=42)
                process.send_signal.side_effect = signal_error
                with mock.patch.object(self.helper.os, "name", "nt"), mock.patch.object(
                    self.helper.subprocess,
                    "CTRL_BREAK_EVENT",
                    21,
                    create=True,
                ):
                    self.helper.stop_server(process)
                process.send_signal.assert_called_once_with(21)
                if signal_error is None:
                    process.terminate.assert_not_called()
                else:
                    process.terminate.assert_called_once_with()
                process.wait.assert_called_once_with(timeout=5)

    def test_windows_stop_kills_and_reaps_after_wait_timeout(self):
        process = mock.Mock(pid=42)
        process.wait.side_effect = [subprocess.TimeoutExpired("server", 5), None]
        with mock.patch.object(self.helper.os, "name", "nt"), mock.patch.object(
            self.helper.subprocess,
            "CTRL_BREAK_EVENT",
            21,
            create=True,
        ):
            self.helper.stop_server(process)
        process.send_signal.assert_called_once_with(21)
        process.kill.assert_called_once_with()
        self.assertEqual(
            process.wait.call_args_list,
            [mock.call(timeout=5), mock.call()],
        )

    def test_windows_startup_failure_still_stops_process_and_closes_log(self):
        process = mock.Mock(pid=42)
        log_file = mock.Mock()
        with mock.patch.object(self.helper.os, "name", "nt"), mock.patch.object(
            self.helper,
            "port_can_be_bound",
            return_value=True,
            create=True,
        ), mock.patch.object(
            self.helper.tempfile,
            "TemporaryFile",
            return_value=log_file,
        ), mock.patch.object(
            self.helper,
            "start_server",
            return_value=process,
        ), mock.patch.object(
            self.helper,
            "wait_for_server",
            side_effect=RuntimeError("startup failed"),
        ), mock.patch.object(self.helper, "stop_server") as stop:
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                result = self.helper.main(
                    ["--server", "serve", "--port", "8765", "--", "child"]
                )
        self.assertEqual(result, 1)
        stop.assert_called_once_with(process)
        log_file.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
