"""test_sloc.py: tests for fprime.util.sloc"""

import csv
import json
from pathlib import Path

import pytest

from fprime.fbuild.types import MissingBuildCachePath
from fprime.util.sloc import (
    CATEGORY_CMAKE,
    CATEGORY_CPP,
    CATEGORY_CPP_AC,
    CATEGORY_CPP_UT,
    CATEGORY_FPP,
    OTHER_MODULE_NAME,
    classify,
    count_autocoded,
    SlocReport,
    count_files,
    discover_modules,
    is_build_cache,
    is_ut_file,
    registers_module,
    render_csv,
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
    """Counts accumulate per module into categories with section totals"""
    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    by_name = {module.name: module for module in modules}
    my_module = by_name["MyModule"]
    assert my_module.category(CATEGORY_CPP).files == 1  # source.cpp
    assert my_module.category(CATEGORY_FPP).files == 1  # model.fpp
    assert my_module.category(CATEGORY_CMAKE).files == 1  # CMakeLists.txt
    assert my_module.category(CATEGORY_CPP_UT).files == 1  # test/ut/tester.cpp
    assert my_module.category(CATEGORY_CPP).code == 2
    assert my_module.category(CATEGORY_FPP).code == 2
    assert my_module.cpp_total() == 2 + 2  # code + UT code
    section = report.section_totals("project")
    assert section.total_files() == 8  # 5 sources + 3 CMakeLists.txt
    assert section.category(CATEGORY_CPP_UT).files == 1
    grand = report.grand_totals()
    assert grand.total_code() == section.total_code()
    assert "C++" in report.languages


def test_classify():
    """Language-to-category classification"""
    assert classify("FPP", True, False) == "FPP"
    assert classify("CMake", False, False) == "CMake"
    assert classify("C++", False, False) == "C/C++"
    assert classify("C", True, False) == "C/C++ UT"
    assert classify("C++", False, True) == "C/C++ AC"
    assert classify("C++", True, True) == "C/C++ AC UT"
    assert classify("Python", False, False) == "Python"


def test_rendering(tmp_path, capsys):
    """Table, markdown, JSON, and CSV renderings include modules and totals"""
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
    csv_path = tmp_path / "sloc.csv"
    render_csv(report, csv_path)
    rows = list(csv.reader(csv_path.open()))
    assert rows[0][:2] == ["Section", "Module"]
    assert [row[1] for row in rows[1:]] == [
        OTHER_MODULE_NAME,
        "MyDeployment",
        "MyModule",
        "TOTAL [project]",
    ]
    assert all(row[0] == "project" for row in rows[1:])


def test_helpers(tmp_path):
    """is_build_cache and is_ut_file helpers"""
    root = make_project(tmp_path)
    assert is_build_cache(root / "build-fprime-automatic-native")
    assert not is_build_cache(root / "MyModule")
    module = root / "MyModule"
    assert is_ut_file(module / "test" / "ut" / "tester.cpp", module)
    assert not is_ut_file(module / "source.cpp", module)


class FakeBuild:
    """Minimal stand-in for fprime.fbuild.builder.Build: a build cache with per-module dirs"""

    def __init__(self, build_dir: Path, cached: dict):
        self.build_dir = build_dir
        self.cached = cached

    def get_build_cache_path(self, context: Path) -> Path:
        if context in self.cached:
            return self.cached[context]
        raise MissingBuildCachePath(f"no cache for {context}")


def test_partial_autocode_cache(tmp_path):
    """Modules without a build cache directory report AC as unknown, not zero"""
    root = make_project(tmp_path)
    cache = root / "build-fprime-automatic-native"
    module_cache = cache / "MyModule"
    module_cache.mkdir()
    (module_cache / "CompComponentAc.cpp").write_text(CPP_SOURCE)
    (module_cache / "CompTesterBase.cpp").write_text(CPP_SOURCE)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=sorted(modules, key=lambda module: module.name))
    count_files(file_owners, report.languages)
    by_name = {module.name: module for module in modules}
    build = FakeBuild(cache, {by_name["MyModule"].path: module_cache})
    count_autocoded(build, report.modules, report.languages)
    assert by_name["MyModule"].ac_counted is True
    assert by_name["MyModule"].category(CATEGORY_CPP_AC).files == 1
    assert by_name["MyModule"].category("C/C++ AC UT").files == 1
    assert by_name["MyDeployment"].ac_counted is False
    assert by_name[OTHER_MODULE_NAME].ac_counted is None
    assert report.ac_counted() and report.ac_missing() == ["MyDeployment"]
    assert "partial" in report.ac_note()
    markdown = render_markdown(report)
    assert "| MyDeployment | 2 | 0 | 2 | 2 | - | 0 | - | 2 | 0 | 4 |" in markdown
    assert "| MyModule | 6 | 2 | 6 | 2 | 2 | 2 | 2 | 8 | 0 | 16 |" in markdown
    assert "partial" in markdown
    parsed = json.loads(render_json(report))
    assert parsed["autocode_missing"] == ["MyDeployment"]
    modules_json = parsed["sections"]["project"]["modules"]
    assert modules_json["MyDeployment"]["autocode_counted"] is False
    assert modules_json["MyModule"]["autocode_counted"] is True


def test_no_autocode_cache(tmp_path):
    """Without any build cache autocode is not attempted and AC columns are unknown"""
    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    count_autocoded(FakeBuild(None, {}), report.modules, report.languages)
    assert all(module.ac_counted is None for module in report.modules)
    assert not report.ac_counted() and report.ac_note() is None
    assert '"autocode_counted": false' in render_json(report)
