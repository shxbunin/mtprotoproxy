from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.py"
PROXY_PATH = BASE_DIR / "mtprotoproxy.py"
ACTIVE_USERS_PATH = Path(os.getenv("PROXY_ACTIVE_USERS_FILE", "/runtime/active_users.json"))
WATCH_INTERVAL_SECONDS = int(os.getenv("PROXY_WATCH_INTERVAL_SECONDS", "5"))


def get_signature(path: Path):
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return stat.st_mtime_ns, stat.st_size


class ProxySupervisor:
    def __init__(self) -> None:
        self.child: subprocess.Popen | None = None
        self.stop_requested = False

    def start(self) -> None:
        self.child = subprocess.Popen(
            [sys.executable, str(PROXY_PATH), str(CONFIG_PATH)],
            cwd=BASE_DIR,
        )

    def stop(self) -> None:
        if self.child is None or self.child.poll() is not None:
            return

        self.child.terminate()
        try:
            self.child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait(timeout=5)

    def reload(self) -> None:
        if self.child is None or self.child.poll() is not None:
            return

        sigusr2 = getattr(signal, "SIGUSR2", None)
        if sigusr2 is not None:
            self.child.send_signal(sigusr2)
        else:
            self.stop()
            self.start()

    def handle_shutdown(self, signum, frame) -> None:
        self.stop_requested = True
        self.stop()


def main() -> int:
    supervisor = ProxySupervisor()

    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, supervisor.handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, supervisor.handle_shutdown)

    supervisor.start()
    signatures = {
        CONFIG_PATH: get_signature(CONFIG_PATH),
        ACTIVE_USERS_PATH: get_signature(ACTIVE_USERS_PATH),
    }

    while not supervisor.stop_requested:
        if supervisor.child is None:
            return 1

        exit_code = supervisor.child.poll()
        if exit_code is not None:
            return exit_code

        time.sleep(WATCH_INTERVAL_SECONDS)
        current_signatures = {
            CONFIG_PATH: get_signature(CONFIG_PATH),
            ACTIVE_USERS_PATH: get_signature(ACTIVE_USERS_PATH),
        }
        if current_signatures != signatures:
            signatures = current_signatures
            supervisor.reload()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
