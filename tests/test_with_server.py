import os
import shlex
import signal
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
CODEX_HELPER = ROOT / "distributions/codex/skills/browser-workflows/scripts/with_server.py"
CLAUDE_HELPER = ROOT / "distributions/claude/skills/webapp-testing/scripts/with_server.py"


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


if __name__ == "__main__":
    unittest.main()
