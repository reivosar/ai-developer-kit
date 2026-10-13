"""Shared fixture: stand-in commands for tests that run the kit's shell scripts."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hook_lib  # noqa: E402

# Every stand-in is this one program. What it does comes from the settings
# file named after it, so a tool that an installer provides later can be
# described before it exists.
_STAND_IN = f"""#!{sys.executable}
import json
import shutil
import sys
from pathlib import Path

stand_in = Path(sys.argv[0])
home = stand_in.parent.parent
arguments = " ".join(sys.argv[1:])
settings_file = home / "settings" / (stand_in.name + ".json")
settings = json.loads(settings_file.read_text()) if settings_file.exists() else {{}}
if not settings.get("silent"):
    with open(home / "calls.log", "a") as log:
        log.write((stand_in.name + " " + arguments).strip() + "\\n")
# pytest lists --cov-branch in its help once the pytest-cov plugin exists.
if stand_in.with_name(stand_in.name + "-cov").exists():
    print("--cov-branch")
print(settings.get("output", ""))
provided_commands = settings.get("provides", {{}}).get(arguments, [])
for provided in provided_commands:
    shutil.copy(stand_in, stand_in.with_name(provided))
# A call that provides a command succeeded; any other call ends with status.
sys.exit(0 if provided_commands else settings.get("status", 0))
"""


class ToolStubs:
    """A PATH holding only stand-in commands, which record how they are called."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.commands = home / "bin"
        self.commands.mkdir(parents=True)
        (home / "settings").mkdir()
        self.set_system("Darwin")

    def configure(self, name: str, **settings: object) -> None:
        """Describe a command that is not on PATH until something provides it."""
        settings_file = self.home / "settings" / f"{name}.json"
        settings_file.write_text(json.dumps(settings))

    def add(self, name: str, **settings: object) -> None:
        """Put a command on PATH.

        provides maps an argument string to the commands that call creates,
        status is the exit code, and output is what the command prints.
        """
        self.configure(name, **settings)
        command = self.commands / name
        command.write_text(_STAND_IN)
        command.chmod(0o755)

    def set_system(self, system: str) -> None:
        self.add("uname", output=system, silent=True)

    def calls(self) -> list[str]:
        log = self.home / "calls.log"
        return log.read_text().splitlines() if log.exists() else []

    def run_script(
        self, script: Path, *arguments: str, **environment: str
    ) -> subprocess.CompletedProcess:
        """Run a shell script that can see nothing but the stand-ins."""
        command = [shutil.which("bash"), str(script), *arguments]
        return subprocess.run(
            command, capture_output=True, text=True,
            env={"PATH": str(self.commands), **environment},
        )


@pytest.fixture(autouse=True)
def records_outside_the_project(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Send each test's hook records and rate state to a temporary directory.

    A hook that a test starts inherits the two variables, so no test writes
    to the project's own .claude/logs or .claude/rate-state.json.
    """
    scratch = tmp_path_factory.mktemp("hook-records")
    monkeypatch.setenv("HOOK_RECORDS_DIR", str(scratch / "logs"))
    monkeypatch.setenv("RATE_STATE_FILE", str(scratch / "rate-state.json"))
    hook_lib.remember_session({})
    return scratch


@pytest.fixture
def tool_stubs(tmp_path: Path) -> ToolStubs:
    stubs = ToolStubs(tmp_path / "stand-ins")
    # The scripts start each other through "env bash", so the real shell is
    # the one command that has to stay reachable.
    (stubs.commands / "bash").symlink_to(shutil.which("bash"))
    return stubs
