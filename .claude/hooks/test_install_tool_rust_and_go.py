"""Tests for install-tool.sh: the Rust and Go tools."""
from pathlib import Path

import pytest

INSTALLER = Path(__file__).parent / "install-tool.sh"


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


def test_install_tool_with_toolchain_too_old_installs_the_release_cargo_names(
    tool_stubs,
):
    older = "install cargo-llvm-cov --version 0.6.15 --locked"
    tool_stubs.add("rustup")
    tool_stubs.add(
        "cargo", status=101, provides={older: ["cargo-llvm-cov"]},
        output="`cargo-llvm-cov 0.6.15` supports rustc 1.73",
    )
    result = tool_stubs.run_script(INSTALLER, "cargo-llvm-cov")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls()[1:] == ["cargo install cargo-llvm-cov", f"cargo {older}"]


def test_install_tool_when_cargo_names_no_older_release_exits_1(tool_stubs):
    tool_stubs.add("rustup")
    tool_stubs.add("cargo", status=101, output="error: failed to compile")
    result = tool_stubs.run_script(INSTALLER, "cargo-llvm-cov")
    assert result.returncode == 1
    assert "error: failed to compile" in result.stderr
    assert tool_stubs.calls()[1:] == ["cargo install cargo-llvm-cov"]


@pytest.mark.parametrize("tool", ["cargo-clippy", "cargo-llvm-cov"])
def test_install_tool_for_rust_tool_without_rustup_exits_1(tool_stubs, tool: str):
    result = tool_stubs.run_script(INSTALLER, tool)
    assert result.returncode == 1
    assert f"could not install {tool}" in result.stderr


def test_install_tool_with_revive_missing_on_macos_installs_it_with_brew(tool_stubs):
    tool_stubs.add("brew", provides={"install revive": ["revive"]})
    result = tool_stubs.run_script(INSTALLER, "revive")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == ["brew install revive"]


def test_install_tool_with_revive_missing_on_linux_builds_it_with_go(tool_stubs):
    tool_stubs.set_system("Linux")
    install = "install github.com/mgechev/revive@latest"
    tool_stubs.add("go", provides={install: ["revive"]})
    result = tool_stubs.run_script(INSTALLER, "revive")
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [f"go {install}"]
