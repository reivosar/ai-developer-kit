"""Tests for install-tool.sh: a missing kit tool is installed, nothing else."""
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent
INSTALLER = HOOKS_DIR / "install-tool.sh"
SETUP = HOOKS_DIR.parents[1] / "setup.sh"
KIT_TOOLS = [
    "pipx", "npm", "go", "flake8", "yamllint", "pytest", "pytest-cov", "tsc",
    "markdownlint", "biome", "cargo-clippy", "cargo-llvm-cov",
]


def test_install_tool_with_list_option_prints_every_kit_tool(tool_stubs):
    result = tool_stubs.run_script(INSTALLER, "--list")
    assert result.stdout.split() == KIT_TOOLS
    assert result.returncode == 0


def test_install_tool_without_arguments_exits_2(tool_stubs):
    result = tool_stubs.run_script(INSTALLER)
    assert result.returncode == 2
    assert "Usage" in result.stderr


def test_install_tool_with_unknown_name_exits_2_and_installs_nothing(tool_stubs):
    tool_stubs.add("pipx", provides={"install flake8": ["flake8"]})
    result = tool_stubs.run_script(INSTALLER, "flake8", "prettier")
    assert result.returncode == 2
    assert "prettier is not a tool this kit installs" in result.stderr
    assert tool_stubs.calls() == []


def test_install_tool_with_tool_already_present_installs_nothing(tool_stubs):
    tool_stubs.add("pipx")
    tool_stubs.add("flake8")
    result = tool_stubs.run_script(INSTALLER, "flake8")
    assert result.returncode == 0
    assert tool_stubs.calls() == []


@pytest.mark.parametrize("tool", ["flake8", "yamllint", "pytest"])
def test_install_tool_with_missing_python_tool_installs_it_with_pipx(
    tool_stubs, tool: str
):
    tool_stubs.add("pipx", provides={f"install {tool}": [tool]})
    result = tool_stubs.run_script(INSTALLER, tool)
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"pipx install {tool}"]


def test_install_tool_with_pipx_missing_on_macos_installs_pipx_first(tool_stubs):
    tool_stubs.configure("pipx", provides={"install flake8": ["flake8"]})
    tool_stubs.add("brew", provides={"install pipx": ["pipx"]})
    result = tool_stubs.run_script(INSTALLER, "flake8")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == ["brew install pipx", "pipx install flake8"]


@pytest.mark.parametrize(
    "tool, package",
    [
        ("tsc", "typescript"),
        ("markdownlint", "markdownlint-cli"),
        ("biome", "@biomejs/biome"),
    ],
)
def test_install_tool_with_missing_node_tool_installs_its_npm_package(
    tool_stubs, tool: str, package: str
):
    tool_stubs.add("npm", provides={f"install -g {package} --quiet": [tool]})
    result = tool_stubs.run_script(INSTALLER, tool)
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"npm install -g {package} --quiet"]


@pytest.mark.parametrize(
    "tool, formula", [("npm", "node"), ("go", "go"), ("pipx", "pipx")]
)
def test_install_tool_with_missing_runtime_on_macos_installs_it_with_brew(
    tool_stubs, tool: str, formula: str
):
    tool_stubs.add("brew", provides={f"install {formula}": [tool]})
    result = tool_stubs.run_script(INSTALLER, tool)
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"brew install {formula}"]


@pytest.mark.parametrize(
    "tool, packages",
    [("npm", "nodejs npm"), ("go", "golang-go"), ("pipx", "pipx")],
)
def test_install_tool_with_missing_runtime_on_linux_installs_it_with_apt(
    tool_stubs, tool: str, packages: str
):
    install = f"-n apt-get install -y {packages}"
    tool_stubs.set_system("Linux")
    tool_stubs.add("apt-get")
    tool_stubs.add("sudo", provides={install: [tool]})
    result = tool_stubs.run_script(INSTALLER, tool)
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"sudo {install}"]


def test_install_tool_with_missing_runtime_on_linux_without_apt_uses_yum(
    tool_stubs,
):
    install = "-n yum install -y golang"
    tool_stubs.set_system("Linux")
    tool_stubs.add("yum")
    tool_stubs.add("sudo", provides={install: ["go"]})
    result = tool_stubs.run_script(INSTALLER, "go")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"sudo {install}"]


def test_install_tool_with_pipx_missing_on_linux_without_apt_uses_pip(tool_stubs):
    tool_stubs.set_system("Linux")
    tool_stubs.add("pip3", provides={"install --user pipx": ["pipx"]})
    result = tool_stubs.run_script(INSTALLER, "pipx")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == ["pip3 install --user pipx"]


def test_install_tool_with_coverage_plugin_missing_injects_it_into_pytest(
    tool_stubs,
):
    tool_stubs.add("pytest")
    tool_stubs.add(
        "pipx", provides={"inject pytest pytest-cov": ["pytest-cov"]}
    )
    result = tool_stubs.run_script(INSTALLER, "pytest-cov")
    assert result.returncode == 0, result.stderr
    assert "pipx inject pytest pytest-cov" in tool_stubs.calls()


def test_install_tool_with_pytest_and_plugin_missing_installs_pytest_first(
    tool_stubs,
):
    provides = {
        "install pytest": ["pytest"],
        "inject pytest pytest-cov": ["pytest-cov"],
    }
    tool_stubs.add("pipx", provides=provides)
    result = tool_stubs.run_script(INSTALLER, "pytest-cov")
    installs = [call for call in tool_stubs.calls() if call.startswith("pipx")]
    assert result.returncode == 0, result.stderr
    assert installs == ["pipx install pytest", "pipx inject pytest pytest-cov"]


@pytest.mark.parametrize(
    "tool, installed",
    [("pytest", ["pytest"]), ("pytest-cov", ["pytest", "pytest-cov"])],
)
def test_install_tool_inside_virtualenv_installs_pytest_package_with_pip(
    tool_stubs, tool: str, installed: list
):
    tool_stubs.add("python3", provides={f"-m pip install {tool}": installed})
    tool_stubs.add("pipx")
    result = tool_stubs.run_script(INSTALLER, tool, VIRTUAL_ENV="/project/.venv")
    assert result.returncode == 0, result.stderr
    assert f"python3 -m pip install {tool}" in tool_stubs.calls()
    assert not any(call.startswith("pipx") for call in tool_stubs.calls())


def test_install_tool_with_clippy_missing_adds_the_rustup_component(tool_stubs):
    tool_stubs.add("rustup", provides={"component add clippy": ["cargo-clippy"]})
    result = tool_stubs.run_script(INSTALLER, "cargo-clippy")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == ["rustup component add clippy"]


def test_install_tool_with_coverage_command_missing_installs_it_with_cargo(
    tool_stubs,
):
    tool_stubs.add("rustup")
    tool_stubs.add("cargo", provides={"install cargo-llvm-cov": ["cargo-llvm-cov"]})
    result = tool_stubs.run_script(INSTALLER, "cargo-llvm-cov")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [
        "rustup component add llvm-tools-preview",
        "cargo install cargo-llvm-cov",
    ]


@pytest.mark.parametrize("tool", ["cargo-clippy", "cargo-llvm-cov"])
def test_install_tool_for_rust_tool_without_rustup_exits_1(tool_stubs, tool: str):
    result = tool_stubs.run_script(INSTALLER, tool)
    assert result.returncode == 1
    assert f"could not install {tool}" in result.stderr


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


def test_setup_with_pytest_missing_installs_pytest_and_coverage_plugin(
    tool_stubs,
):
    provides = {
        "install pytest": ["pytest"],
        "inject pytest pytest-cov": ["pytest-cov"],
    }
    tool_stubs.add("brew")
    tool_stubs.add("npm")
    tool_stubs.add("pipx", provides=provides)
    result = tool_stubs.run_script(SETUP)
    assert result.returncode == 0, result.stderr
    assert "pipx install pytest" in tool_stubs.calls()
    assert "pipx inject pytest pytest-cov" in tool_stubs.calls()
