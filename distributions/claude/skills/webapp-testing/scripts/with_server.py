#!/usr/bin/env python3
"""Start servers, wait for readiness, run a command, and clean up."""

import argparse
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time


LOG_EXCERPT_BYTES = 4096


def read_log_excerpt(log_file):
    """Return the tail of a server log without assuming valid UTF-8 output."""
    log_file.flush()
    size = log_file.seek(0, os.SEEK_END)
    log_file.seek(max(0, size - LOG_EXCERPT_BYTES))
    excerpt = log_file.read().decode("utf-8", errors="replace").strip()
    return excerpt or "(server log was empty)"


def port_is_accepting(port):
    """Return whether the launched local server is accepting connections."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False


def port_can_be_bound(port):
    """Return whether an exclusive IPv4 loopback bind succeeds."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def wait_for_server(process, port, log_file, timeout=30):
    """Wait for a port while also detecting a server that exits early."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        returncode = process.poll()
        if returncode is not None:
            excerpt = read_log_excerpt(log_file)
            raise RuntimeError(
                f"Server for port {port} exited with code {returncode} before becoming ready.\n"
                f"Server log excerpt:\n{excerpt}"
            )
        if port_is_accepting(port):
            return
        time.sleep(0.1)

    returncode = process.poll()
    if returncode is not None:
        detail = f"exited with code {returncode} before becoming ready"
    else:
        detail = f"did not open its port within {timeout}s"
    excerpt = read_log_excerpt(log_file)
    raise RuntimeError(
        f"Server for port {port} {detail}.\nServer log excerpt:\n{excerpt}"
    )


def start_server(command, log_file):
    """Start a server in an isolated process group with file-backed output."""
    options = {}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    return subprocess.Popen(
        command,
        shell=True,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        **options,
    )


def stop_server(process):
    """Terminate and reap a server process tree on POSIX and Windows."""
    if os.name == "nt":
        ctrl_break = getattr(subprocess, "CTRL_BREAK_EVENT", None)
        try:
            if ctrl_break is None:
                process.terminate()
            else:
                process.send_signal(ctrl_break)
        except ProcessLookupError:
            pass
        except (OSError, ValueError):
            try:
                process.terminate()
            except ProcessLookupError:
                pass
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait()
    else:
        if os.name != "nt":
            try:
                os.killpg(process.pid, 0)
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a command with one or more servers")
    parser.add_argument(
        "--server",
        action="append",
        dest="servers",
        required=True,
        help="Server command (can be repeated)",
    )
    parser.add_argument(
        "--port",
        action="append",
        dest="ports",
        type=int,
        required=True,
        help="Port for each server (must match --server count)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds per server (default: 30)",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run after the servers are ready",
    )
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("no command specified to run")
    if len(args.servers) != len(args.ports):
        parser.error("the number of --server and --port arguments must match")
    return args


def main(argv=None):
    args = parse_args(argv)
    started = []
    try:
        for index, (command, port) in enumerate(zip(args.servers, args.ports), start=1):
            if not port_can_be_bound(port):
                raise RuntimeError(
                    f"Port {port} is already occupied; stop the existing service or choose another port."
                )
            print(f"Starting server {index}/{len(args.servers)}: {command}")
            log_file = tempfile.TemporaryFile(prefix="with-server-", mode="w+b")
            try:
                process = start_server(command, log_file)
            except Exception:
                log_file.close()
                raise
            started.append((process, log_file))
            print(f"Waiting for server on port {port}...")
            wait_for_server(process, port, log_file, timeout=args.timeout)
            print(f"Server ready on port {port}")

        print(f"\nAll {len(started)} server(s) ready")
        print(f"Running: {' '.join(args.command)}\n")
        return subprocess.run(args.command, check=False).returncode
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        print(f"\nStopping {len(started)} server(s)...")
        for index, (process, log_file) in enumerate(started, start=1):
            try:
                stop_server(process)
                print(f"Server {index} stopped")
            finally:
                log_file.close()
        print("All servers stopped")


if __name__ == "__main__":
    raise SystemExit(main())
