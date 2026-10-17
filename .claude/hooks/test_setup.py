"""Tests for setup.sh: how it installs the python3, node, and go runtimes."""
from pathlib import Path

import pytest

SETUP = Path(__file__).resolve().parents[2] / "setup.sh"


@pytest.mark.parametrize("manager, calls", [
    ("brew", ["brew upgrade python3", "brew upgrade node", "brew upgrade go"]),
    ("apt-get", [
        "sudo apt-get install -y python3 python3-pip",
        "sudo apt-get install -y nodejs npm",
        "sudo apt-get install -y golang-go",
    ]),
    ("yum", [
        "sudo yum install -y python3 python3-pip",
        "sudo yum install -y nodejs npm",
        "sudo yum install -y golang",
    ]),
])
def test_setup_with_package_manager_installs_each_runtime_with_it(
    tool_stubs, manager: str, calls: list
):
    tool_stubs.set_system("Darwin" if manager == "brew" else "Linux")
    tool_stubs.add(manager)
    tool_stubs.add("sudo")
    tool_stubs.run_script(SETUP)
    assert set(calls) <= set(tool_stubs.calls())


@pytest.mark.parametrize("system, messages", [
    ("Darwin", [
        "SKIP: Homebrew not found. Install from https://brew.sh/"
        " or Python from https://www.python.org/",
        "SKIP: Homebrew not found. Install from https://brew.sh/"
        " or Node.js from https://nodejs.org/",
        "SKIP: Homebrew not found. Install from https://brew.sh/"
        " or Go from https://go.dev/dl/",
    ]),
    ("Linux", [
        "SKIP: No supported package manager found."
        " Install Python from https://www.python.org/",
        "SKIP: No supported package manager found."
        " Install Node.js from https://nodejs.org/",
        "SKIP: No supported package manager found. Install Go from https://go.dev/dl/",
    ]),
    ("FreeBSD", [
        "SKIP: Unsupported OS: FreeBSD. Install Python from https://www.python.org/",
        "SKIP: Unsupported OS: FreeBSD. Install Node.js from https://nodejs.org/",
        "SKIP: Unsupported OS: FreeBSD. Install Go from https://go.dev/dl/",
    ]),
])
def test_setup_without_package_manager_names_where_to_get_each_runtime(
    tool_stubs, system: str, messages: list
):
    tool_stubs.set_system(system)
    result = tool_stubs.run_script(SETUP)
    assert set(messages) <= set(result.stderr.splitlines())


def test_setup_with_runtime_upgrade_failing_installs_it_instead(tool_stubs):
    # An upgrade of a formula that is not installed fails; the install that
    # follows provides the runtime.
    formulas = ["python3", "pipx", "node", "go"]
    provides = {f"install {name}": [name] for name in formulas}
    tool_stubs.add("brew", status=1, provides=provides)
    tool_stubs.run_script(SETUP)
    calls = tool_stubs.calls()
    assert {"brew install python3", "brew install node", "brew install go"} <= set(calls)
