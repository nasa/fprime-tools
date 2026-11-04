"""test_sloc.py: tests for fprime.util.sloc"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from fprime.fbuild.types import MissingBuildCachePath
from fprime.util.sloc import (
    AcStatus,
    Section,
    csv_safe_text,
    discover_all,
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
    add_sloc_parsers,
    find_context_module,
    SlocException,
    deployment_modules,
    ninja_link_tokens,
    read_submodule_paths,
    run_sloc,
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
    assert (
        grand.total_code() == 3 + 4 + 12
    )  # (non-module files) + MyDeployment + MyModule
    assert grand.total_code() == sum(module.total_code() for module in modules)
    assert "C++" in report.languages


def test_classify():
    """Language-to-category classification"""
    assert classify("FPP", is_ut=True, is_ac=False) == "FPP"
    assert classify("CMake", is_ut=False, is_ac=False) == "CMake"
    assert classify("C++", is_ut=False, is_ac=False) == "C/C++"
    assert classify("C", is_ut=True, is_ac=False) == "C/C++ UT"
    assert classify("C++", is_ut=False, is_ac=True) == "C/C++ AC"
    assert classify("C++", is_ut=True, is_ac=True) == "C/C++ AC UT"
    assert classify("Python", is_ut=False, is_ac=False) == "Python"


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
    """Minimal stand-in for fprime.fbuild.builder.Build: settings and per-module cache dirs"""

    def __init__(self, build_dir: Path, cached: dict, settings: dict = None):
        self.build_dir = build_dir
        self.cached = cached
        self.settings = settings or {}

    def get_settings(self, setting: str, default):
        return self.settings.get(setting, default)

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
    assert by_name["MyModule"].ac_status is AcStatus.COUNTED
    assert by_name["MyModule"].category(CATEGORY_CPP_AC).files == 1
    assert by_name["MyModule"].category("C/C++ AC UT").files == 1
    assert by_name["MyDeployment"].ac_status is AcStatus.MISSING
    assert by_name[OTHER_MODULE_NAME].ac_status is AcStatus.NOT_ATTEMPTED
    assert report.ac_counted() and report.ac_missing() == ["MyDeployment"]
    assert "partial" in report.ac_note()
    markdown = render_markdown(report)
    assert "| MyDeployment | 2 | 0 | 2 | 2 | - | 0 | - | 2 | 0 | 4 |" in markdown
    assert "| MyModule | 6 | 2 | 6 | 2 | 2 | 2 | 2 | 8 | 0 | 16 |" in markdown
    assert "partial" in markdown
    parsed = json.loads(render_json(report))
    assert parsed["autocode_missing"] == ["MyDeployment"]
    modules_json = parsed["sections"]["project"]["modules"]
    assert modules_json["MyDeployment"]["autocode"] == "missing"
    assert modules_json["MyModule"]["autocode"] == "counted"


def test_no_autocode_cache(tmp_path):
    """Without any build cache autocode is not attempted and AC columns are unknown"""
    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    count_autocoded(FakeBuild(None, {}), report.modules, report.languages)
    assert all(module.ac_status is AcStatus.NOT_ATTEMPTED for module in report.modules)
    assert not report.ac_counted() and report.ac_note() is None
    assert '"autocode_counted": false' in render_json(report)


def sloc_args(path: Path, **overrides) -> argparse.Namespace:
    """Parsed-argument namespace for run_sloc"""
    args = dict(
        path=path,
        recursive=False,
        include_submodules=False,
        markdown_report=None,
        json_report=None,
        csv_report=None,
    )
    args.update(overrides)
    return argparse.Namespace(**args)


def make_framework(tmp_path: Path) -> Path:
    """Create a minimal 'framework' tree beside the project"""
    framework = tmp_path / "fprime"
    framework.mkdir()
    (framework / "CMakeLists.txt").write_text("add_library(fw a.cpp)\n")
    (framework / "a.cpp").write_text(CPP_SOURCE)
    return framework


def test_run_sloc_contexts(tmp_path, capsys):
    """Module, project-root and --recursive contexts count the documented scope"""
    root = make_project(tmp_path)
    framework = make_framework(tmp_path)
    settings = {"framework_path": str(framework), "project_root": str(root)}
    no_cache = FakeBuild(None, {}, settings)

    assert run_sloc(no_cache, sloc_args(root / "MyModule"), {}, {}, []) == 0
    table = capsys.readouterr().out
    assert "MyModule" in table and "MyDeployment" not in table
    assert "[fprime]" not in table

    json_path = tmp_path / "out.json"
    csv_path = tmp_path / "out.csv"
    markdown_path = tmp_path / "out.md"
    arguments = sloc_args(
        root, json_report=json_path, csv_report=csv_path, markdown_report=markdown_path
    )
    assert run_sloc(no_cache, arguments, {}, {}, []) == 0
    parsed = json.loads(json_path.read_text())
    assert set(parsed["sections"]) == {"fprime", "project: project"}
    assert parsed["autocode_counted"] is False
    assert "GRAND TOTAL" in csv_path.read_text()
    assert "## Grand Total" in markdown_path.read_text()

    arguments = sloc_args(root / "MyModule", recursive=True, json_report=json_path)
    assert run_sloc(no_cache, arguments, {}, {}, []) == 0
    assert "MyModule" in capsys.readouterr().out
    parsed = json.loads(json_path.read_text())
    assert set(parsed["sections"]) == {"project: project"}
    assert parsed["autocode_counted"] is False


def test_run_sloc_errors(tmp_path):
    """Every documented failure of run_sloc raises SlocException with a clear message"""
    root = make_project(tmp_path)
    framework = make_framework(tmp_path)
    settings = {"framework_path": str(framework), "project_root": str(root)}
    no_cache = FakeBuild(None, {}, settings)
    with pytest.raises(SlocException, match="require a build cache"):
        run_sloc(no_cache, sloc_args(root / "MyDeployment"), {}, {}, [])
    with pytest.raises(SlocException, match="not part of an F Prime module"):
        run_sloc(no_cache, sloc_args(tmp_path), {}, {}, [])
    with pytest.raises(SlocException, match="framework_path"):
        run_sloc(FakeBuild(None, {}, {}), sloc_args(root), {}, {}, [])


NINJA = """build Ref/CMakeFiles/Ref.dir/Main.cpp.o: CXX_COMPILER__Ref_ /src/Ref/Main.cpp || cmake_object_order_depends_target_Ref
build bin/Linux/Ref: CXX_EXECUTABLE_LINKER__Ref_ Ref/CMakeFiles/Ref.dir/Main.cpp.o | Svc/CmdDispatcher/libSvc_CmdDispatcher.a $
    Fw/Cmd/libFw_Cmd.a || Svc/CmdDispatcher/libSvc_CmdDispatcher.a Fw/Cmd/libFw_Cmd.a
build Svc/CmdDispatcher/libSvc_CmdDispatcher.a: CXX_STATIC_LIBRARY_LINKER__Svc_CmdDispatcher_ Svc/CmdDispatcher/CMakeFiles/x.o || Fw/Types/libFw_Types.a
build Fw/Cmd/libFw_Cmd.a: CXX_STATIC_LIBRARY_LINKER__Fw_Cmd_ Fw/Cmd/CMakeFiles/y.o
build Fw/Types/libFw_Types.a: CXX_STATIC_LIBRARY_LINKER__Fw_Types_ Fw/Types/CMakeFiles/z.o
build Svc/Unused/libSvc_Unused.a: CXX_STATIC_LIBRARY_LINKER__Svc_Unused_ Svc/Unused/CMakeFiles/w.o
"""


def test_ninja_link_tokens(tmp_path):
    """Transitive library tokens are collected from the deployment's link edge only"""
    ninja = tmp_path / "build.ninja"
    ninja.write_text(NINJA)
    assert ninja_link_tokens(ninja, "Ref") == {
        "Svc_CmdDispatcher",
        "Fw_Cmd",
        "Fw_Types",
    }
    assert ninja_link_tokens(ninja, "Other") == set()


def test_deployment_modules(tmp_path):
    """Deployment closure follows link.txt / build.ninja; missing link info is an error"""
    root = make_project(tmp_path)
    modules, _ = discover_modules(root, "project", [])
    cache = root / "build-fprime-automatic-native"
    deployment = root / "MyDeployment"
    with pytest.raises(SlocException, match="Could not determine dependencies"):
        deployment_modules(FakeBuild(cache, {}), deployment, modules)
    deployment_cache = cache / "MyDeployment" / "CMakeFiles" / "MyDeployment.dir"
    deployment_cache.mkdir(parents=True)
    (deployment_cache / "link.txt").write_text(
        "/usr/bin/c++ main.o -o MyDeployment ../MyModule/libMyModule.a ../libOther.a\n"
    )
    configured = {
        deployment: cache / "MyDeployment",
        root / "MyModule": cache / "MyModule",
    }
    selected = deployment_modules(FakeBuild(cache, configured), deployment, modules)
    assert {module.name for module in selected} == {"MyDeployment", "MyModule"}
    # a same-named module CMake never configured into this cache is not pulled in by name
    selected = deployment_modules(
        FakeBuild(cache, {deployment: cache / "MyDeployment"}), deployment, modules
    )
    assert {module.name for module in selected} == {"MyDeployment"}
    (cache / "build.ninja").write_text(
        NINJA.replace("Ref", "MyDeployment").replace("Svc_CmdDispatcher", "MyModule")
    )
    selected = deployment_modules(
        FakeBuild(cache, {root / "MyModule": cache / "MyModule"}), deployment, modules
    )
    assert {module.name for module in selected} == {"MyDeployment", "MyModule"}


def test_submodule_exclusion(tmp_path):
    """Git submodule paths from .gitmodules are excluded unless requested"""
    root = make_project(tmp_path)
    submodule = root / "MyModule" / "googletest"
    submodule.mkdir()
    (submodule / "CMakeLists.txt").write_text("add_library(gtest gtest.cpp)\n")
    (submodule / "gtest.cpp").write_text(CPP_SOURCE)
    (root / ".gitmodules").write_text(
        '[submodule "googletest"]\n\tpath = MyModule/googletest\n\turl = https://example.invalid/gtest\n'
    )
    excludes = read_submodule_paths(root)
    assert excludes == [submodule.resolve()]
    modules, owners = discover_modules(root, "project", excludes)
    assert "MyModule_googletest" not in {module.name for module in modules}
    assert not any("googletest" in str(path) for path in owners)
    modules, _ = discover_modules(root, "project", [])
    assert "MyModule_googletest" in {module.name for module in modules}


def test_other_languages(tmp_path):
    """Non-base languages get their own 'other' column, largest first, and an 'other' total"""
    root = make_project(tmp_path)
    (root / "MyModule" / "tool.py").write_text("import os\n\nprint(os.name)\n")
    (root / "MyDeployment" / "run.sh").write_text("#!/bin/sh\necho hi\n")
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=sorted(modules, key=lambda module: module.name))
    count_files(file_owners, report.languages)
    by_name = {module.name: module for module in modules}
    assert by_name["MyModule"].other_languages() == ["Python"]
    assert by_name["MyModule"].other_total() == 2
    assert report.other_languages() == ["Python", "Bash"]
    markdown = render_markdown(report)
    assert "| other (Python) | other (Bash) | other (Total) |" in markdown
    assert "| MyModule | 5 | 2 | 6 | 2 | - | 2 | - | 4 | 2 | 0 | 2 | 14 |" in markdown


def test_cli_import_is_light():
    """Importing the CLI must not load pygount (it imports GitPython, which runs git)"""
    code = "import sys, fprime.util.cli; print(sorted(m for m in sys.modules if m in ('pygount', 'git')))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"


def test_project_root_is_not_a_module(tmp_path):
    """register_fprime_project() (and other non-target calls) do not make a directory a module"""
    root = make_project(tmp_path)
    (root / "CMakeLists.txt").write_text(
        "register_fprime_project()\nregister_fprime_target(x)\nadd_subdirectory(MyModule)\n"
    )
    assert registers_module(root / "CMakeLists.txt") == (False, False)
    modules, _ = discover_modules(root, "project", [])
    assert OTHER_MODULE_NAME in {module.name for module in modules}
    assert find_context_module(root / "nowhere") is None


def test_autogenerated_comment_does_not_drop_files(tmp_path):
    """pygount's 'autogenerated' comment heuristic must not hide hand-written sources"""
    root = make_project(tmp_path)
    (root / "MyModule" / "Version.cpp").write_text(
        "// autogenerated file: do not edit\n" + CPP_SOURCE
    )
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    by_name = {module.name: module for module in modules}
    assert by_name["MyModule"].category(CATEGORY_CPP).files == 2


def test_autocode_states(tmp_path):
    """Config copies are not autocode; a generated-but-unbuilt module reports AC as unknown"""
    root = make_project(tmp_path)
    cache = root / "build-fprime-automatic-native"
    module_cache = cache / "MyModule"
    module_cache.mkdir()
    (module_cache / "source.cpp").write_text(
        CPP_SOURCE
    )  # copy of a hand-written source
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    by_name = {module.name: module for module in modules}
    build = FakeBuild(cache, {by_name["MyModule"].path: module_cache})
    count_autocoded(build, report.modules, report.languages)
    assert by_name["MyModule"].category(CATEGORY_CPP_AC).files == 0
    assert (
        by_name["MyModule"].ac_status is AcStatus.NOT_BUILT
    )  # has model.fpp, no autocode
    assert "MyModule" in report.ac_missing() and "fprime-util build" in report.ac_note()
    # the fpp autocoder's record decides when present: nothing expected -> counted (AC = 0)
    fpp_cache = module_cache / "fpp-cache"
    fpp_cache.mkdir()
    (fpp_cache / "generated.txt").write_text("")
    count_autocoded(build, report.modules, report.languages)
    assert by_name["MyModule"].ac_status is AcStatus.COUNTED
    (fpp_cache / "generated.txt").write_text(
        "CompComponentAc.cpp\nCompComponentAc.hpp\n"
    )
    count_autocoded(build, report.modules, report.languages)
    assert by_name["MyModule"].ac_status is AcStatus.NOT_BUILT
    (module_cache / "CompComponentAc.cpp").write_text(CPP_SOURCE)
    count_autocoded(build, report.modules, report.languages)
    assert by_name["MyModule"].ac_status is AcStatus.COUNTED
    assert by_name["MyModule"].category(CATEGORY_CPP_AC).files == 1
    # a module without FPP models and without autocode is simply counted (AC = 0, not unknown)
    deployment_cache = cache / "MyDeployment"
    deployment_cache.mkdir()
    build = FakeBuild(cache, {by_name["MyDeployment"].path: deployment_cache})
    count_autocoded(build, report.modules, report.languages)
    assert by_name["MyDeployment"].ac_status is AcStatus.COUNTED
    assert "MyDeployment" not in report.ac_missing()


def test_orphan_cache_path_is_missing(tmp_path):
    """A module CMake never configured (CMakeOrphanException) reports AC as unknown"""
    from fprime.fbuild.cmake import CMakeOrphanException

    class OrphanBuild(FakeBuild):
        def get_build_cache_path(self, context: Path) -> Path:
            raise CMakeOrphanException(f"orphan {context}")

    root = make_project(tmp_path)
    modules, file_owners = discover_modules(root, "project", [])
    report = SlocReport(modules=modules)
    count_files(file_owners, report.languages)
    count_autocoded(
        OrphanBuild(root / "build-fprime-automatic-native", {}),
        report.modules,
        report.languages,
    )
    by_name = {module.name: module for module in modules}
    assert by_name["MyModule"].ac_status is AcStatus.MISSING
    assert by_name["MyDeployment"].ac_status is AcStatus.MISSING
    with pytest.raises(SlocException, match="Could not determine dependencies"):
        deployment_modules(
            OrphanBuild(root / "build-fprime-automatic-native", {}),
            root / "MyDeployment",
            modules,
        )


def test_module_names_relative_to_section_root(tmp_path):
    """Scoping down to a directory keeps the section-relative (CMake target) module names"""
    root = make_project(tmp_path)
    scope = root / "MyModule"
    modules, _ = discover_all([Section("project", scope, [], name_root=root)])
    assert [module.name for module in modules] == ["MyModule"]
    modules, _ = discover_all([Section("project", scope, [])])
    assert [module.name for module in modules] == [
        "MyModule"
    ]  # name_root defaults to root
    nested = scope / "Sub"
    nested.mkdir()
    (nested / "CMakeLists.txt").write_text("add_library(sub a.cpp)\n")
    modules, _ = discover_all([Section("project", scope, [], name_root=root)])
    assert {module.name for module in modules} == {"MyModule", "MyModule_Sub"}


def test_csv_safe_text_guard():
    """Spreadsheet formula prefixes are neutralized in CSV name cells"""
    assert csv_safe_text("=HYPERLINK(1)") == "'=HYPERLINK(1)"
    assert (
        csv_safe_text("+x") == "'+x"
        and csv_safe_text("-x") == "'-x"
        and csv_safe_text("@x") == "'@x"
    )
    assert csv_safe_text("MyModule") == "MyModule" and csv_safe_text("") == ""


def test_run_sloc_deployment(tmp_path, capsys):
    """Deployment context counts the deployment plus its linked modules, with autocode"""
    root = make_project(tmp_path)
    framework = make_framework(tmp_path)
    settings = {"framework_path": str(framework), "project_root": str(root)}
    cache = root / "build-fprime-automatic-native"
    deployment = root / "MyDeployment"
    link_dir = cache / "MyDeployment" / "CMakeFiles" / "MyDeployment.dir"
    link_dir.mkdir(parents=True)
    (link_dir / "link.txt").write_text(
        "c++ main.o -o MyDeployment ../MyModule/libMyModule.a\n"
    )
    module_cache = cache / "MyModule"
    module_cache.mkdir()
    (module_cache / "CompComponentAc.cpp").write_text(CPP_SOURCE)
    configured = {deployment: cache / "MyDeployment", root / "MyModule": module_cache}
    build = FakeBuild(cache, configured, settings)
    json_path = tmp_path / "deployment.json"
    assert (
        run_sloc(build, sloc_args(deployment, json_report=json_path), {}, {}, []) == 0
    )
    table = capsys.readouterr().out
    assert "MyDeployment" in table and "MyModule" in table
    assert OTHER_MODULE_NAME not in table and "[fprime]" not in table
    parsed = json.loads(json_path.read_text())
    modules_json = parsed["sections"]["project: project"]["modules"]
    assert set(modules_json) == {"MyDeployment", "MyModule"}
    assert modules_json["MyModule"]["autocode"] == "counted"
    assert modules_json["MyModule"]["categories"]["C/C++ AC"]["files"] == 1
    assert parsed["autocode_counted"] is True and parsed["autocode_missing"] == []


def test_sloc_argparse_surface():
    """The sloc subparser exposes exactly the documented flags with the expected defaults"""
    parser = argparse.ArgumentParser()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-p", "--path", default=".")
    subparsers = parser.add_subparsers(dest="command")

    class HelpText:
        @staticmethod
        def long(key):
            return f"long {key}"

        @staticmethod
        def short(key):
            return f"short {key}"

    runners, parsers = add_sloc_parsers(subparsers, common, HelpText)
    assert runners == {"sloc": run_sloc} and set(parsers) == {"sloc"}
    parsed = parser.parse_args(["sloc"])
    assert parsed.recursive is False and parsed.include_submodules is False
    assert (parsed.markdown_report, parsed.json_report, parsed.csv_report) == (
        None,
        None,
        None,
    )
    parsed = parser.parse_args(
        ["sloc", "--recursive", "--include-submodules", "--csv-report", "out.csv"]
    )
    assert parsed.recursive and parsed.include_submodules
    assert parsed.csv_report == Path("out.csv")
    with pytest.raises(SystemExit):
        parser.parse_args(["sloc", "--excel-report", "x.xlsx"])
