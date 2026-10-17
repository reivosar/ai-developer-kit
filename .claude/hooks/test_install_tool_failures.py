"""Tests for install-tool.sh: an install that cannot be done is reported."""
from pathlib import Path

INSTALLER = Path(__file__).parent / "install-tool.sh"


def test_install_tool_when_install_command_fails_exits_1(tool_stubs):
    tool_stubs.add("pipx", status=1)
    result = tool_stubs.run_script(INSTALLER, "flake8")
    assert result.returncode == 1
    assert "could not install flake8" in result.stderr


def test_install_tool_when_installed_tool_is_not_on_path_exits_1(tool_stubs):
    tool_stubs.add("pipx")
    result = tool_stubs.run_script(INSTALLER, "flake8")
    assert result.returncode == 1
    assert "flake8 was installed but is not on PATH" in result.stderr


def test_install_tool_on_macos_without_brew_exits_1(tool_stubs):
    result = tool_stubs.run_script(INSTALLER, "go")
    assert result.returncode == 1
    assert "could not install go" in result.stderr


def test_install_tool_on_linux_without_package_manager_exits_1(tool_stubs):
    tool_stubs.set_system("Linux")
    result = tool_stubs.run_script(INSTALLER, "go")
    assert result.returncode == 1
    assert "could not install go" in result.stderr


def test_install_tool_on_unsupported_system_exits_1(tool_stubs):
    tool_stubs.set_system("FreeBSD")
    tool_stubs.add("brew", provides={"install go": ["go"]})
    result = tool_stubs.run_script(INSTALLER, "go")
    assert result.returncode == 1
    assert tool_stubs.calls() == []


def test_install_tool_with_one_failing_tool_still_installs_the_others(
    tool_stubs,
):
    tool_stubs.add("pipx", provides={"install yamllint": ["yamllint"]})
    result = tool_stubs.run_script(INSTALLER, "flake8", "yamllint")
    assert result.returncode == 1
    assert "pipx install yamllint" in tool_stubs.calls()
