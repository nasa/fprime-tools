"""test_sloc.py: tests for fprime.util.sloc"""

from pathlib import Path

from fprime.util.sloc import (
    OTHER_MODULE_NAME,
    SlocReport,
    count_files,
    discover_modules,
    is_build_cache,
    is_ut_file,
    registers_module,
    render_json,
    render_markdown,
    render_table,
)

MODULE_CMAKE = """
register_fprime_module(
    MyModule
  SOURCES
    source.cpp
)
register_fprime_ut(
  UT_SOURCES test/ut/tester.cpp
)
"""
DEPLOYMENT_CMAKE = """
project(MyDeployment)
register_fprime_deployment()
"""
PLAIN_CMAKE = """
add_subdirectory(MyModule)
"""
CPP_SOURCE = """// A comment
int main() {

    return 0; // code
}
"""
FPP_SOURCE = """# A comment
@ An annotation
module MyModule {
    passive component Comp {
    }
}
"""


def make_project(tmp_path: Path) -> Path:
    """Create a synthetic project tree for testing"""
    root = tmp_path / "project"
    module = root / "MyModule"
    ut_dir = module / "test" / "ut"
    ut_dir.mkdir(parents=True)
    (root / "CMakeLists.txt").write_text(PLAIN_CMAKE)
    (root / "loose.cpp").write_text(CPP_SOURCE)
    (module / "CMakeLists.txt").write_text(MODULE_CMAKE)
    (module / "source.cpp").write_text(CPP_SOURCE)
    (module / "model.fpp").write_text(FPP_SOURCE)
    (ut_dir / "tester.cpp").write_text(CPP_SOURCE)
    deployment = root / "MyDeployment"
    deployment.mkdir()
    (deployment / "CMakeLists.txt").write_text(DEPLOYMENT_CMAKE)
    (deployment / "main.cpp").write_text(CPP_SOURCE)
    cache = root / "build-fprime-automatic-native"
    cache.mkdir()
    (cache / "CMakeCache.txt").write_text("")
    (cache / "generated.cpp").write_text(CPP_SOURCE)
    return root


def test_registers_module(tmp_path):
    """Module and deployment detection from CMakeLists.txt content"""
    root = make_project(tmp_path)
    assert registers_module(root / "MyModule" / "CMakeLists.txt") == (True, False)
    assert registers_module(root / "MyDeployment" / "CMakeLists.txt") == (True, True)
    assert registers_module(root / "CMakeLists.txt") == (False, False)


def test_discover_modules(tmp_path):
    """Modules discovered, files attributed, build caches skipped"""
    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    names = {module.name for module in modules}
    assert names == {"MyModule", "MyDeployment", OTHER_MODULE_NAME}
    deployments = [module for module in modules if module.is_deployment]
    assert [module.name for module in deployments] == ["MyDeployment"]
    owners = {
        str(path.relative_to(root)): module.name for path, module in file_owners.items()
    }
    assert owners["MyModule/source.cpp"] == "MyModule"
    assert owners["MyModule/test/ut/tester.cpp"] == "MyModule"
    assert owners["MyDeployment/main.cpp"] == "MyDeployment"
    assert owners["loose.cpp"] == OTHER_MODULE_NAME
    assert not any("build-fprime" in path for path in owners)


def test_counting_and_rollups(tmp_path):
    """Counts accumulate per module with UT separation and section totals"""
    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    by_name = {module.name: module for module in modules}
    my_module = by_name["MyModule"]
    assert my_module.counts.files == 2  # source.cpp + model.fpp
    assert my_module.ut_counts.files == 1  # test/ut/tester.cpp
    assert my_module.counts.code == 2 + 2  # cpp code lines + fpp code lines
    assert my_module.counts.comment == 1 + 2  # cpp comment + fpp comment/annotation
    flight, ut, _ = report.section_totals("project")
    assert flight.files == 4
    assert ut.files == 1
    grand_flight, grand_ut, _ = report.grand_totals()
    assert grand_flight.code == flight.code
    assert grand_ut.code == ut.code
    assert "C++" in report.languages


def test_rendering(tmp_path, capsys):
    """Table, markdown, and JSON renderings include modules and totals"""
    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=sorted(modules, key=lambda module: module.name))
    count_files(file_owners, report.languages)
    render_table(report)
    table = capsys.readouterr().out
    assert "MyModule" in table and "TOTAL [project]" in table
    markdown = render_markdown(report)
    assert "| Module |" in markdown and "MyDeployment" in markdown
    json_output = render_json(report)
    assert '"MyModule"' in json_output and '"totals"' in json_output


def test_helpers(tmp_path):
    """is_build_cache and is_ut_file helpers"""
    root = make_project(tmp_path)
    assert is_build_cache(root / "build-fprime-automatic-native")
    assert not is_build_cache(root / "MyModule")
    module = root / "MyModule"
    assert is_ut_file(module / "test" / "ut" / "tester.cpp", module)
    assert not is_ut_file(module / "source.cpp", module)
