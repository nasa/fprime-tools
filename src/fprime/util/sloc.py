"""fprime.util.sloc: SLOC counting for F Prime projects

Implements the (experimental) 'fprime-util sloc' command: a thin wrapper around pygount that
segments an F Prime project into modules (any directory whose CMakeLists.txt calls
register_fprime_*, add_library, or add_executable), counts SLOC per module, and rolls totals up
per section (project, framework, libraries) and for the whole repository.

The command is context aware:
    - In a component/module directory: counts just that module
    - In a deployment directory: counts the deployment and its dependencies (needs build cache)
    - At the project root: counts everything, segmented by project/framework/libraries
    - With --recursive: counts all modules under the current directory

FPP files are supported through the FPP pygments lexer plugin (fprime.fpp.lexer) which pygount
picks up automatically.

@author lestarch
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from pygount import SourceAnalysis, SourceState

from fprime.common.error import FprimeException
from fprime.fbuild.builder import Build
from fprime.fbuild.types import MissingBuildCachePath

MODULE_PATTERN = re.compile(
    r"^\s*(register_fprime_\w+|add_library|add_executable)\s*\(", re.MULTILINE
)
DEPLOYMENT_PATTERN = re.compile(r"^\s*register_fprime_deployment\s*\(", re.MULTILINE)
LIBRARY_TOKEN_PATTERN = re.compile(r"lib([A-Za-z0-9_\-]+)\.(?:a|so|dylib)")
SUBMODULE_PATH_PATTERN = re.compile(r"^\s*path\s*=\s*(.+)$", re.MULTILINE)

SKIP_DIRECTORY_NAMES = {"__pycache__", "node_modules", "build-artifacts"}
NON_CODE_LANGUAGES = {
    "Text only",
    "Markdown",
    "reStructuredText",
    "__unknown__",
    "__binary__",
    "__empty__",
    "__error__",
}
UT_PATH_NAMES = {"test", "tests", "ut"}
OTHER_MODULE_NAME = "(non-module files)"
AC_SUFFIXES = {".hpp", ".cpp", ".h", ".c", ".fppi", ".py"}

# Language classification: FPP model files, CMake, C/C++ (with UT and autocode splits), other
CPP_LANGUAGES = {"C++", "C"}
CATEGORY_FPP = "FPP"
CATEGORY_CMAKE = "CMake"
CATEGORY_CPP = "C/C++"
CATEGORY_CPP_AC = "C/C++ AC"
CATEGORY_CPP_UT = "C/C++ UT"
CATEGORY_CPP_AC_UT = "C/C++ AC UT"
BASE_CATEGORIES = [
    CATEGORY_FPP,
    CATEGORY_CMAKE,
    CATEGORY_CPP,
    CATEGORY_CPP_AC,
    CATEGORY_CPP_UT,
    CATEGORY_CPP_AC_UT,
]
AC_CATEGORIES = {CATEGORY_CPP_AC, CATEGORY_CPP_AC_UT}
AC_UT_FILE_PATTERN = re.compile(r"(TesterBase|GTestBase|TesterHelpers)")


class SlocException(FprimeException):
    """Error raised by the sloc command"""


@dataclass
class Counts:
    """Line counts for a set of files"""

    files: int = 0
    code: int = 0
    comment: int = 0
    blank: int = 0

    @classmethod
    def from_analysis(cls, analysis: SourceAnalysis) -> "Counts":
        """Counts for one pygount analysis (strings count as code)"""
        return cls(
            files=1,
            code=analysis.code_count + analysis.string_count,
            comment=analysis.documentation_count,
            blank=analysis.empty_count,
        )

    def accumulate(self, other: "Counts"):
        """Add another set of counts into this one"""
        self.files += other.files
        self.code += other.code
        self.comment += other.comment
        self.blank += other.blank

    def to_dict(self) -> dict:
        """Dictionary representation for JSON output"""
        return {
            "files": self.files,
            "code": self.code,
            "comment": self.comment,
            "blank": self.blank,
        }


def classify(language: str, is_ut: bool, is_ac: bool) -> str:
    """Map a pygount language (and UT/AC context) to a report category"""
    if language == "FPP":
        return CATEGORY_FPP
    if language == "CMake":
        return CATEGORY_CMAKE
    if language in CPP_LANGUAGES:
        if is_ac:
            return CATEGORY_CPP_AC_UT if is_ut else CATEGORY_CPP_AC
        return CATEGORY_CPP_UT if is_ut else CATEGORY_CPP
    return language


@dataclass
class ModuleSloc:
    """SLOC results for a single module, split into categories

    ac_counted records autocode availability for this module: None when autocode counting was not
    attempted (no build cache), False when the module has no build cache directory, True when its
    autocoded files were counted.
    """

    name: str
    path: Path
    section: str
    is_deployment: bool = False
    categories: Dict[str, Counts] = field(default_factory=dict)
    ac_counted: Optional[bool] = None

    def add(self, category: str, counts: Counts):
        """Accumulate counts into a category"""
        self.categories.setdefault(category, Counts()).accumulate(counts)

    def category(self, category: str) -> Counts:
        """Counts for a category (zero counts if absent)"""
        return self.categories.get(category, Counts())

    def cpp_total(self) -> int:
        """Total C/C++ code lines across code, UT, and autocode"""
        return sum(
            self.category(category).code
            for category in (
                CATEGORY_CPP,
                CATEGORY_CPP_AC,
                CATEGORY_CPP_UT,
                CATEGORY_CPP_AC_UT,
            )
        )

    def other_languages(self) -> List[str]:
        """Languages outside the base categories"""
        return [c for c in self.categories if c not in BASE_CATEGORIES]

    def other_total(self) -> int:
        """Total code lines across all 'other' languages"""
        return sum(self.categories[c].code for c in self.other_languages())

    def total_code(self) -> int:
        """Total code lines across all categories"""
        return sum(counts.code for counts in self.categories.values())

    def total_files(self) -> int:
        """Total files across all categories"""
        return sum(counts.files for counts in self.categories.values())


@dataclass
class SlocReport:
    """Full report: modules grouped into sections"""

    modules: List[ModuleSloc] = field(default_factory=list)
    languages: Dict[str, Counts] = field(default_factory=dict)

    def sections(self) -> List[str]:
        """Ordered unique section names"""
        return list(dict.fromkeys(module.section for module in self.modules))

    def section_modules(self, section: str) -> List[ModuleSloc]:
        """Modules belonging to a section"""
        return [module for module in self.modules if module.section == section]

    def other_languages(self) -> List[str]:
        """All 'other' languages in the report, largest first"""
        totals: Dict[str, int] = {}
        for module in self.modules:
            for language in module.other_languages():
                totals[language] = (
                    totals.get(language, 0) + module.categories[language].code
                )
        return sorted(totals, key=lambda language: -totals[language])

    def ac_counted(self) -> bool:
        """True when autocode was counted for at least one module"""
        return any(module.ac_counted for module in self.modules)

    def ac_missing(self) -> List[str]:
        """Names of modules whose autocode could not be counted (no build cache directory)"""
        return [module.name for module in self.modules if module.ac_counted is False]

    def ac_note(self) -> Optional[str]:
        """Human readable note on autocode coverage, None when autocode was not attempted"""
        missing = self.ac_missing()
        if not missing:
            return (
                "Autocoded (AC) files counted from the build cache."
                if self.ac_counted()
                else None
            )
        shown = ", ".join(missing[:5]) + (", ..." if len(missing) > 5 else "")
        return (
            f"Autocoded (AC) counts are partial: no build cache directory for {len(missing)} "
            f"module(s) ({shown}); their AC columns show '-' and are excluded from totals."
        )

    def section_totals(self, section: str) -> ModuleSloc:
        """Totals for a section, as a pseudo-module"""
        return self._totals(self.section_modules(section))

    def grand_totals(self) -> ModuleSloc:
        """Totals for the whole report, as a pseudo-module"""
        return self._totals(self.modules)

    @staticmethod
    def _totals(modules: List[ModuleSloc]) -> ModuleSloc:
        total = ModuleSloc(name="TOTAL", path=Path("."), section="")
        total.ac_counted = any(module.ac_counted for module in modules)
        for module in modules:
            for category, counts in module.categories.items():
                total.add(category, counts)
        return total


####
# Module discovery
####
def is_build_cache(path: Path) -> bool:
    """Check if a directory is (or holds) a build cache"""
    return (
        (path / "CMakeCache.txt").exists()
        or (path / ".fprime-build-dir").exists()
        or path.name.startswith("build-fprime")
    )


def should_skip_directory(path: Path) -> bool:
    """Check if a directory should be excluded from source scanning"""
    return (
        path.name.startswith(".")
        or path.name in SKIP_DIRECTORY_NAMES
        or is_build_cache(path)
        or (path / "pyvenv.cfg").exists()  # virtual environments
    )


def read_submodule_paths(root: Path) -> List[Path]:
    """Read git submodule paths under a root, if any"""
    gitmodules = root / ".gitmodules"
    if not gitmodules.is_file():
        return []
    matches = SUBMODULE_PATH_PATTERN.findall(gitmodules.read_text(errors="replace"))
    return [(root / match.strip()).resolve() for match in matches]


def registers_module(cmake_lists: Path) -> Tuple[bool, bool]:
    """Check a CMakeLists.txt: returns (is_module, is_deployment)"""
    try:
        content = cmake_lists.read_text(errors="replace")
    except OSError:
        return False, False
    return (
        MODULE_PATTERN.search(content) is not None,
        DEPLOYMENT_PATTERN.search(content) is not None,
    )


def discover_modules(
    root: Path, section: str, excludes: List[Path]
) -> Tuple[List[ModuleSloc], Dict[Path, ModuleSloc]]:
    """Discover modules under a root and attribute every source file to one

    Files not under any module directory are attributed to a per-section pseudo-module. Returns
    the module list and a mapping of file path to owning module.
    """
    modules: Dict[Path, ModuleSloc] = {}
    file_owners: Dict[Path, ModuleSloc] = {}
    other = ModuleSloc(name=OTHER_MODULE_NAME, path=root, section=section)

    def walk(directory: Path, owner: Optional[ModuleSloc]):
        cmake_lists = directory / "CMakeLists.txt"
        if cmake_lists.is_file():
            is_module, is_deployment = registers_module(cmake_lists)
            if is_module:
                name = (
                    str(directory.relative_to(root)).replace("/", "_")
                    if directory != root
                    else root.name
                )
                owner = modules.setdefault(
                    directory,
                    ModuleSloc(
                        name=name,
                        path=directory,
                        section=section,
                        is_deployment=is_deployment,
                    ),
                )
        for entry in sorted(directory.iterdir()):
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if should_skip_directory(entry) or entry.resolve() in excludes:
                    continue
                walk(entry, owner)
            elif entry.is_file():
                file_owners[entry] = owner if owner is not None else other

    walk(root, None)
    module_list = list(modules.values())
    if any(owner is other for owner in file_owners.values()):
        module_list.append(other)
    return module_list, file_owners


def discover_all(
    scope_roots: List[Tuple[str, Path, List[Path]]],
) -> Tuple[List[ModuleSloc], Dict[Path, ModuleSloc]]:
    """Discover modules across several (section, root, excludes) scopes"""
    all_modules: List[ModuleSloc] = []
    all_owners: Dict[Path, ModuleSloc] = {}
    for section, root, excludes in scope_roots:
        modules, owners = discover_modules(root, section, excludes)
        all_modules.extend(modules)
        all_owners.update(owners)
    return all_modules, all_owners


def find_context_module(path: Path) -> Optional[Tuple[Path, bool]]:
    """Find the nearest ancestor (inclusive) module directory of a path

    Returns (module_directory, is_deployment) or None when no module is found.
    """
    for candidate in [path, *path.parents]:
        cmake_lists = candidate / "CMakeLists.txt"
        if cmake_lists.is_file():
            is_module, is_deployment = registers_module(cmake_lists)
            if is_module:
                return candidate, is_deployment
    return None


####
# Counting (pygount)
####
def is_ut_file(path: Path, module_path: Path) -> bool:
    """Check if a file is unit-test code based on its path within the module"""
    try:
        relative = path.relative_to(module_path)
    except ValueError:
        return False
    return any(part.lower() in UT_PATH_NAMES for part in relative.parts[:-1])


def analyze_file(path: Path) -> Optional[SourceAnalysis]:
    """Run pygount on a single file, returning None for non-code or unreadable files"""
    try:
        if path.name == "CMakeLists.txt":
            # pygount keys the language off the file name and treats *.txt as plain text, so
            # analyze CMakeLists.txt content under a .cmake name
            with path.open("rb") as handle:
                analysis = SourceAnalysis.from_file(
                    str(path.with_suffix(".cmake")),
                    "sloc",
                    fallback_encoding="utf-8",
                    file_handle=handle,
                )
        else:
            analysis = SourceAnalysis.from_file(
                str(path), "sloc", fallback_encoding="utf-8"
            )
    except (OSError, UnicodeError, LookupError):
        # unreadable file or undecodable/unknown encoding: not countable, skip it
        return None
    if (
        analysis.state != SourceState.analyzed
        or analysis.language in NON_CODE_LANGUAGES
    ):
        return None
    return analysis


def count_files(
    file_owners: Dict[Path, ModuleSloc], languages: Dict[str, Counts]
) -> None:
    """Count all files, accumulating into their owning modules and the language rollup"""
    for path, module in file_owners.items():
        analysis = analyze_file(path)
        if analysis is None:
            continue
        counts = Counts.from_analysis(analysis)
        module.add(
            classify(analysis.language, is_ut_file(path, module.path), is_ac=False),
            counts,
        )
        languages.setdefault(analysis.language, Counts()).accumulate(counts)


def cache_available(build: Build) -> bool:
    """Check whether the build has a generated build cache"""
    return build.build_dir is not None and (build.build_dir / "CMakeCache.txt").exists()


def count_autocoded(
    build: Build, modules: List[ModuleSloc], languages: Dict[str, Counts]
) -> None:
    """Count autocoded files in the build cache for each module

    Records availability per module in ModuleSloc.ac_counted so that modules without a build
    cache directory are reported as unknown rather than zero.
    """
    if not cache_available(build):
        return
    for module in modules:
        if module.name == OTHER_MODULE_NAME:
            continue  # loose files outside any module have no autocode
        try:
            cache_path = build.get_build_cache_path(module.path)
        except MissingBuildCachePath:
            module.ac_counted = False
            continue
        module.ac_counted = True
        # Generated files land directly in the module's mirrored cache directory;
        # do not recurse as subdirectories belong to other modules or CMake internals
        for path in sorted(cache_path.iterdir()):
            if not path.is_file() or path.suffix not in AC_SUFFIXES:
                continue
            analysis = analyze_file(path)
            if analysis is None:
                continue
            counts = Counts.from_analysis(analysis)
            is_ut = AC_UT_FILE_PATTERN.search(path.name) is not None
            module.add(classify(analysis.language, is_ut, is_ac=True), counts)
            languages.setdefault(analysis.language, Counts()).accumulate(counts)


def build_report(
    build: Build,
    modules: List[ModuleSloc],
    file_owners: Dict[Path, ModuleSloc],
    with_autocode: bool,
) -> SlocReport:
    """Count SLOC for the given modules and produce a report"""
    report = SlocReport(modules=list(modules))
    selected = set(id(module) for module in modules)
    owners = {
        path: module for path, module in file_owners.items() if id(module) in selected
    }
    count_files(owners, report.languages)
    if with_autocode:
        count_autocoded(build, report.modules, report.languages)
    report.modules.sort(key=lambda module: (module.section, module.name))
    return report


####
# Sections and deployment closure
####
def get_sections(
    build: Build, include_submodules: bool
) -> List[Tuple[str, Path, List[Path]]]:
    """Compute the (name, root, excludes) sections: project, framework, and libraries"""
    framework_setting = build.get_settings("framework_path", None)
    if framework_setting is None:
        raise SlocException(
            "Cannot determine 'framework_path'. Run from a directory with a settings.ini or "
            "supply an existing build cache with --build-cache."
        )
    framework = Path(framework_setting).resolve()
    project = Path(build.get_settings("project_root", framework)).resolve()
    libraries = [
        Path(library).resolve()
        for library in build.get_settings("library_locations", [])
    ]
    sections = []
    if project != framework and project not in libraries:
        sections.append((f"project: {project.name}", project))
    sections.append(("fprime", framework))
    sections.extend((f"library: {library.name}", library) for library in libraries)
    roots = [root for _, root in sections]
    results = []
    for name, root in sections:
        excludes = [
            other for other in roots if other != root and other.is_relative_to(root)
        ]
        if not include_submodules:
            excludes.extend(read_submodule_paths(root))
        results.append((name, root, excludes))
    return results


def find_section_name(path: Path, sections: List[Tuple[str, Path, List[Path]]]) -> str:
    """Find the section name owning a path, preferring the deepest matching root"""
    best = None
    for name, root, _ in sections:
        if path == root or path.is_relative_to(root):
            if best is None or len(root.parts) > len(best[1].parts):
                best = (name, root)
    return best[0] if best else "project"


def ninja_link_tokens(ninja_file: Path, executable: str) -> set:
    """Extract library names linked into an executable from a build.ninja file

    Walks the ninja build graph from the build statement(s) producing the executable, following
    dependencies transitively, and collects the lib<name> tokens seen along the way.
    """
    text = ninja_file.read_text(errors="replace").replace("$\n", " ")
    edges: Dict[str, List[str]] = {}
    for line in text.splitlines():
        if not line.startswith("build ") or ":" not in line:
            continue
        outputs, _, remainder = line[len("build ") :].partition(":")
        dependencies = remainder.replace("|", " ").split()[1:]  # drop the rule name
        for output in outputs.replace("|", " ").split():
            edges.setdefault(output, []).extend(dependencies)
    # deployment targets may be mangled with path prefixes (e.g. Project_Deployment)
    starts = [
        output
        for output in edges
        if Path(output).name == executable
        or Path(output).name.endswith(f"_{executable}")
    ]
    tokens = set()
    visited = set()
    queue = list(starts)
    while queue:
        node = queue.pop()
        if node in visited:
            continue
        visited.add(node)
        tokens.update(LIBRARY_TOKEN_PATTERN.findall(node))
        queue.extend(edges.get(node, []))
    return tokens


def deployment_module_paths(
    build: Build, deployment: Path, modules: List[ModuleSloc]
) -> List[ModuleSloc]:
    """Restrict modules to a deployment and its linked dependencies

    Parses link lines (link.txt for Makefiles, build.ninja for Ninja) in the build cache to find
    the libraries linked into the deployment, then matches them to discovered module names.
    """
    tokens = set()
    try:
        link_files = list(build.get_build_cache_path(deployment).rglob("link.txt"))
    except MissingBuildCachePath:
        link_files = []  # not a Makefile build cache; fall back to build.ninja below
    for link_file in link_files:
        tokens.update(
            LIBRARY_TOKEN_PATTERN.findall(link_file.read_text(errors="replace"))
        )
    ninja_file = build.build_dir / "build.ninja" if build.build_dir else None
    if not tokens and ninja_file is not None and ninja_file.exists():
        tokens.update(ninja_link_tokens(ninja_file, deployment.name))
    if not tokens:
        raise SlocException(
            f"Could not determine dependencies for deployment '{deployment.name}' from the "
            "build cache. Ensure the deployment has been generated and built."
        )
    return [
        module
        for module in modules
        if module.path == deployment
        or module.path.is_relative_to(deployment)
        or module.name in tokens
    ]


####
# Output rendering: one row grid shared by the table, Markdown, and CSV outputs
####
ROW_SECTION = "section"
ROW_MODULE = "module"
ROW_TOTAL = "total"


def report_columns(report: SlocReport) -> List[str]:
    """Column headers: base categories, C/C++ total, per-language others, other/grand totals"""
    columns = ["Module", "Files"] + BASE_CATEGORIES + ["C/C++ Total"]
    columns += [f"other ({language})" for language in report.other_languages()]
    return columns + ["other (Total)", "Total"]


def module_row(module: ModuleSloc, report: SlocReport, label: str = None) -> List[str]:
    """Build a display row for a module (or totals pseudo-module)"""

    def cell(category: str) -> str:
        if category in AC_CATEGORIES and not module.ac_counted:
            return "-"
        return str(module.category(category).code)

    row = [label if label is not None else module.name, str(module.total_files())]
    row += [cell(category) for category in BASE_CATEGORIES]
    row.append(str(module.cpp_total()))
    row += [
        str(module.category(language).code) for language in report.other_languages()
    ]
    return row + [str(module.other_total()), str(module.total_code())]


def report_rows(report: SlocReport) -> List[Tuple[str, str, List[str]]]:
    """Report grid as (row kind, section, cells) tuples: per section its modules and total, then
    a grand total when there is more than one section"""
    rows = []
    width = len(report_columns(report))
    for section in report.sections():
        rows.append((ROW_SECTION, section, [f"[{section}]"] + [""] * (width - 1)))
        rows.extend(
            (ROW_MODULE, section, module_row(module, report))
            for module in report.section_modules(section)
        )
        rows.append(
            (
                ROW_TOTAL,
                section,
                module_row(
                    report.section_totals(section), report, f"TOTAL [{section}]"
                ),
            )
        )
    if len(report.sections()) > 1:
        rows.append(
            (ROW_TOTAL, "", module_row(report.grand_totals(), report, "GRAND TOTAL"))
        )
    return rows


def render_table(report: SlocReport, output=None):
    """Render the report as an aligned text table to the given stream"""
    output = output if output is not None else sys.stdout
    columns = report_columns(report)
    rows = report_rows(report)
    widths = [
        max(len(cells[index]) for _, _, cells in [("", "", columns)] + rows)
        for index in range(len(columns))
    ]
    rule = "-" * (sum(widths) + 2 * (len(widths) - 1))

    def print_row(cells):
        padded = [cells[0].ljust(widths[0])] + [
            cell.rjust(width) for cell, width in zip(cells[1:], widths[1:])
        ]
        print("  ".join(padded).rstrip(), file=output)

    print_row(columns)
    print(rule, file=output)
    for kind, _, cells in rows:
        print_row(cells)
        if kind == ROW_TOTAL:
            print(rule, file=output)
    if report.ac_note():
        print(report.ac_note(), file=output)


def render_markdown(report: SlocReport) -> str:
    """Render the report as a Markdown document: one table per section plus a grand total"""
    columns = report_columns(report)
    header = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    lines = ["# SLOC Report", ""]
    if report.ac_note():
        lines += [report.ac_note(), ""]
    for kind, section, cells in report_rows(report):
        if kind == ROW_SECTION:
            lines += [f"## {section}", ""] + header
        elif kind == ROW_MODULE:
            lines.append("| " + " | ".join(cells) + " |")
        elif section:
            lines.append("| " + " | ".join(f"**{cell}**" for cell in cells) + " |")
            lines.append("")
        else:
            lines += ["## Grand Total", ""] + header
            lines.append("| " + " | ".join(f"**{cell}**" for cell in cells) + " |")
            lines.append("")
    return "\n".join(lines) + "\n"


def render_csv(report: SlocReport, path: Path):
    """Render the report as CSV: a section column followed by the report columns"""
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Section"] + report_columns(report))
        writer.writerows(
            [section] + cells
            for kind, section, cells in report_rows(report)
            if kind != ROW_SECTION
        )


def categories_dict(module: ModuleSloc) -> dict:
    """Per-category counts dictionary for JSON output"""
    return {
        category: counts.to_dict() for category, counts in module.categories.items()
    }


def render_json(report: SlocReport) -> str:
    """Render the report as JSON"""
    sections = {
        section: {
            "modules": {
                module.name: {
                    "path": str(module.path),
                    "deployment": module.is_deployment,
                    "autocode_counted": module.ac_counted,
                    "categories": categories_dict(module),
                }
                for module in report.section_modules(section)
            },
            "totals": categories_dict(report.section_totals(section)),
        }
        for section in report.sections()
    }
    return json.dumps(
        {
            "autocode_counted": report.ac_counted(),
            "autocode_missing": report.ac_missing(),
            "sections": sections,
            "totals": categories_dict(report.grand_totals()),
            "languages": {
                language: counts.to_dict()
                for language, counts in report.languages.items()
            },
        },
        indent=2,
    )


####
# CLI handling
####
def run_sloc(
    build: Build,
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___,
):
    """Run the sloc command: context-aware SLOC counting

    Args:
        build: build object (cache validation skipped; used for settings and AC counting)
        parsed: parsed command namespace
        _: unused cmake arguments
        __: unused make arguments
        ___: unused pass through arguments
    """
    path = Path(parsed.path).resolve()
    sections = get_sections(build, parsed.include_submodules)
    section_roots = [root for _, root, _ in sections]
    has_cache = cache_available(build)

    def scoped_excludes(scope: Path) -> List[Path]:
        """Section excludes (including submodules) that fall under a scope directory"""
        return [
            exclude
            for _, _, excludes in sections
            for exclude in excludes
            if exclude.is_relative_to(scope)
        ]

    if parsed.recursive:
        if not has_cache:
            raise SlocException(
                "--recursive requires a build cache. Run 'fprime-util generate' first."
            )
        name = find_section_name(path, sections)
        modules, file_owners = discover_all([(name, path, scoped_excludes(path))])
        report = build_report(build, modules, file_owners, with_autocode=True)
    elif (
        path in section_roots
        or path == Path(build.get_settings("project_root", path)).resolve()
    ):
        modules, file_owners = discover_all(sections)
        report = build_report(build, modules, file_owners, with_autocode=has_cache)
    else:
        context = find_context_module(path)
        if context is None:
            raise SlocException(
                f"'{path}' is not part of an F Prime module. Use --recursive to count a "
                "directory tree."
            )
        module_path, is_deployment = context
        name = find_section_name(module_path, sections)
        if is_deployment:
            if not has_cache:
                raise SlocException(
                    "Deployment SLOC counts require a build cache. Run 'fprime-util generate' "
                    "first."
                )
            # Discover everywhere, restrict to the deployment closure, then count
            modules, file_owners = discover_all(sections)
            selected = deployment_module_paths(build, module_path, modules)
            report = build_report(build, selected, file_owners, with_autocode=True)
        else:
            modules, file_owners = discover_all(
                [(name, module_path, scoped_excludes(module_path))]
            )
            report = build_report(build, modules, file_owners, with_autocode=has_cache)

    render_table(report)
    if parsed.markdown_report:
        Path(parsed.markdown_report).write_text(render_markdown(report))
        print(f"[INFO] Markdown report written to {parsed.markdown_report}")
    if parsed.json_report:
        Path(parsed.json_report).write_text(render_json(report))
        print(f"[INFO] JSON report written to {parsed.json_report}")
    if parsed.csv_report:
        render_csv(report, Path(parsed.csv_report))
        print(f"[INFO] CSV report written to {parsed.csv_report}")
    return 0


def add_sloc_parsers(
    subparsers, common: argparse.ArgumentParser, help_text
) -> Tuple[Dict[str, Callable], Dict[str, argparse.ArgumentParser]]:
    """Add the sloc subparser to the CLI

    Args:
        subparsers: subparsers to add the sloc parser to
        common: common parent parser
        help_text: HelpText class providing help messages

    Returns:
        Tuple of runner dictionary and parser dictionary
    """
    sloc_parser = subparsers.add_parser(
        "sloc",
        description=help_text.long("sloc"),
        help=help_text.short("sloc"),
        parents=[common],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sloc_parser.add_argument(
        "--recursive",
        default=False,
        action="store_true",
        help="Count all modules under the current directory (requires a build cache)",
    )
    sloc_parser.add_argument(
        "--include-submodules",
        default=False,
        action="store_true",
        help="Include git submodules (e.g. googletest) in counts",
    )
    for flag, description in (
        ("--markdown-report", "Write a Markdown report to the given path"),
        ("--json-report", "Write a JSON report to the given path"),
        ("--csv-report", "Write a CSV report to the given path"),
    ):
        sloc_parser.add_argument(flag, default=None, type=Path, help=description)
    return {"sloc": run_sloc}, {"sloc": sloc_parser}
