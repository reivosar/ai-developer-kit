"""Tests for static-analysis.sh: whole-project checks run in each file's project.

go vet, tsc, and cargo clippy check a whole module, so each runs once in the
nearest directory above a file that holds go.mod, tsconfig.json, or
Cargo.toml, not in whatever directory the script was started from.
"""
from pathlib import Path

SCRIPT = Path(__file__).parent / "static-analysis.sh"


def _source(directory: Path, name: str, marker: str = "") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    if marker:
        (directory / marker).write_text("\n")
    source = directory / name
    source.write_text("\n")
    return source


def _go_stubs(tool_stubs) -> None:
    for name in ["go", "gofmt", "revive"]:
        tool_stubs.add(name)


def _vet_calls(tool_stubs) -> list[str]:
    return [call for call in tool_stubs.calls() if " vet " in f"{call} "]


def test_static_analysis_with_go_files_in_one_module_vets_it_once(
    tmp_path: Path, tool_stubs
):
    module = tmp_path / "services" / "orders"
    first = _source(module, "orders.go", "go.mod")
    second = _source(module / "store", "store.go")
    _go_stubs(tool_stubs)
    result = tool_stubs.run_script(SCRIPT, str(first), str(second))
    assert result.returncode == 0, result.stderr
    assert _vet_calls(tool_stubs) == [f"go -C {module} vet ./..."]


def test_static_analysis_with_go_files_in_two_modules_vets_each(
    tmp_path: Path, tool_stubs
):
    orders = _source(tmp_path / "orders", "orders.go", "go.mod")
    billing = _source(tmp_path / "billing", "billing.go", "go.mod")
    _go_stubs(tool_stubs)
    tool_stubs.run_script(SCRIPT, str(orders), str(billing))
    assert _vet_calls(tool_stubs) == [
        f"go -C {tmp_path / 'orders'} vet ./...",
        f"go -C {tmp_path / 'billing'} vet ./...",
    ]


def test_static_analysis_with_go_file_outside_any_module_vets_the_file(
    tmp_path: Path, tool_stubs
):
    source = _source(tmp_path, "main.go")
    _go_stubs(tool_stubs)
    tool_stubs.run_script(SCRIPT, str(source))
    assert f"go vet {source}" in tool_stubs.calls()


def test_static_analysis_with_typescript_project_checks_that_project(
    tmp_path: Path, tool_stubs
):
    project = tmp_path / "web"
    source = _source(project / "src", "order.ts")
    (project / "tsconfig.json").write_text("{}\n")
    tool_stubs.add("tsc")
    tool_stubs.add("biome")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert f"tsc --noEmit -p {project}" in tool_stubs.calls()


def test_static_analysis_with_typescript_project_keeps_build_info_outside_it(
    tmp_path: Path, tool_stubs
):
    project = tmp_path / "web"
    source = _source(project, "order.ts", "tsconfig.json")
    home = tmp_path / "home"
    tool_stubs.add("tsc")
    tool_stubs.add("biome")
    tool_stubs.run_script(SCRIPT, str(source), HOME=str(home))
    cache = home / ".cache" / "ai-developer-kit" / "tsc"
    build_info = cache / (str(project).replace("/", "_") + ".tsbuildinfo")
    assert (
        f"tsc --noEmit -p {project} --incremental --tsBuildInfoFile {build_info}"
        in tool_stubs.calls()
    )


def test_static_analysis_with_typescript_file_outside_any_project_checks_the_file(
    tmp_path: Path, tool_stubs
):
    source = _source(tmp_path, "order.ts")
    tool_stubs.add("tsc")
    tool_stubs.add("biome")
    tool_stubs.run_script(SCRIPT, str(source))
    assert f"tsc --noEmit {source}" in tool_stubs.calls()


def _crate_source(directory: Path) -> Path:
    source = _source(directory / "src", "lib.rs")
    (directory / "Cargo.toml").write_text("\n")
    return source


def _clippy(crate: Path) -> str:
    return (
        f"cargo clippy --manifest-path {crate}/Cargo.toml"
        " --all-targets --quiet -- -D warnings -D missing_docs"
        " -D clippy::missing_errors_doc -D clippy::missing_panics_doc"
        " -D clippy::missing_safety_doc"
    )


def test_static_analysis_with_rust_file_in_crate_runs_clippy_on_its_manifest(
    tmp_path: Path, tool_stubs
):
    source = _crate_source(tmp_path / "orders")
    tool_stubs.add("cargo")
    tool_stubs.add("cargo-clippy")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == [_clippy(tmp_path / "orders")]


def test_static_analysis_with_clippy_finding_exits_1(tmp_path: Path, tool_stubs):
    source = _crate_source(tmp_path)
    tool_stubs.add("cargo", status=1)
    tool_stubs.add("cargo-clippy")
    assert tool_stubs.run_script(SCRIPT, str(source)).returncode == 1


def test_static_analysis_with_clippy_missing_installs_the_component(
    tmp_path: Path, tool_stubs
):
    source = _crate_source(tmp_path)
    tool_stubs.add("cargo")
    tool_stubs.add("rustup", provides={"component add clippy": ["cargo-clippy"]})
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert tool_stubs.calls() == ["rustup component add clippy", _clippy(tmp_path)]


def test_static_analysis_with_rust_file_outside_any_crate_says_it_was_not_checked(
    tmp_path: Path, tool_stubs
):
    source = _source(tmp_path, "scratch.rs")
    tool_stubs.add("cargo")
    tool_stubs.add("cargo-clippy")
    result = tool_stubs.run_script(SCRIPT, str(source))
    assert result.returncode == 0, result.stderr
    assert f"{source} belongs to no Cargo package" in result.stderr
    assert tool_stubs.calls() == []
