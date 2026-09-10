"""fprime.fpp.topology_check: static capacity checks for a deployment topology

Implements the `fprime-util topology-check` command. The command reads artifacts that `fprime-util generate`/`build`
already leave in the build cache for a deployment (the generated topology C++, the topology dictionary, generated
configuration headers) together with the FPP sources indexed by `locs.fpp`, and checks a small set of capacity
limits that would otherwise only surface as an FW_ASSERT at run time:

1. Every Svc.Health instance has a queue at least as deep as its number of ping targets. Health is a queued
   component that only drains its queue on `Run`, so every ping reply of a cycle must fit in the queue.
2. The command dispatcher opcode table is at least as large as the number of commands in the dictionary.
3. (Heuristic warning) Every queued component instance has a queue at least as deep as the number of connections
   into its async input ports that neither `drop` nor `hook` on overflow.

The generated C++ and JSON are parsed with regular expressions rather than through `fpp-to-json` so that the check
works with the native fpp tools alone (no JVM required).

@author bitWarrior
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from fprime.common.error import FprimeException
from fprime.fbuild.builder import Build
from fprime.fpp.common import FppMissingSupportFiles, FppUtility

COMMAND_NAME = "topology-check"
TOPOLOGY_HEADER_SUFFIX = "TopologyAc.hpp"
DISPATCHER_CONFIG_NAME = "CommandDispatcherImplCfg.hpp"
DISPATCHER_TABLE_SYMBOL = "CMD_DISPATCHER_DISPATCH_TABLE_SIZE"
HEALTH_PING_OUTPUT_PORT = "PingSend"

LEVEL_OK = "OK"
LEVEL_WARNING = "WARNING"
LEVEL_ERROR = "ERROR"


class TopologyCheckException(FprimeException):
    """Raised when the build cache does not contain the artifacts needed to run the check"""


@dataclass(frozen=True)
class Connection:
    """One port connection from the generated topology source"""

    source: str  # C++ instance path, e.g. "CdhCore::health"
    source_port: str
    destination: str
    destination_port: str


@dataclass
class Finding:
    """Result of evaluating one rule against one subject"""

    level: str
    rule: str
    message: str


@dataclass
class TopologyModel:
    """Everything the rules need to know about a deployment topology"""

    deployment: str
    queue_sizes: Dict[str, int] = field(default_factory=dict)  # "CdhCore_health" -> 64
    instance_types: Dict[str, str] = field(
        default_factory=dict
    )  # "CdhCore::health" -> "Svc::Health"
    connections: List[Connection] = field(default_factory=list)
    health_instances: List[str] = field(default_factory=list)  # C++ instance paths
    command_count: Optional[int] = None
    dispatcher_table_size: Optional[int] = None
    # FPP-side information, keyed by fully-qualified FPP names ("Svc.Health", "CdhCore.health")
    component_kinds: Dict[str, str] = field(
        default_factory=dict
    )  # comp -> active|queued|passive
    async_ports: Dict[str, Dict[str, str]] = field(
        default_factory=dict
    )  # comp -> port -> ""|drop|hook
    instance_components: Dict[str, str] = field(
        default_factory=dict
    )  # instance -> comp
    fpp_available: bool = False

    @staticmethod
    def queue_key(instance: str) -> str:
        """Map a C++ instance path to its key in the generated QueueSizes enum"""
        return instance.replace("::", "_")

    @staticmethod
    def fpp_name(instance: str) -> str:
        """Map a C++ instance path to its fully-qualified FPP name"""
        return instance.replace("::", ".")

    def queue_depth(self, instance: str) -> Optional[int]:
        """Queue depth of a C++ instance path, or None for components without a queue"""
        return self.queue_sizes.get(self.queue_key(instance))


# ---------------------------------------------------------------------------------------------------------------------
# Pure text parsers. Each takes file contents and returns data so they can be unit tested on inline strings.
# ---------------------------------------------------------------------------------------------------------------------

_QUEUE_BLOCK_RE = re.compile(r"namespace\s+QueueSizes\s*\{\s*enum\s*\{(.*?)\}", re.S)
_ENUMERATOR_RE = re.compile(r"(\w+)\s*=\s*(\d+)")
_NAMESPACE_RE = re.compile(r"^\s*namespace\s+(\w+)\s*\{")
_EXTERN_RE = re.compile(r"^\s*extern\s+([\w:]+)\s+(\w+)\s*;")
_CONNECTION_RE = re.compile(
    r"([\w:]+)\.set_(\w+)_OutputPort\(\s*\d+\s*,\s*([\w:]+)\.get_(\w+)_InputPort\(\s*\d+\s*\)\s*\)",
    re.S,
)
_PING_ENTRIES_RE = re.compile(r"([\w:]+)\.setPingEntries\(")
_DISPATCHER_TABLE_RE = re.compile(DISPATCHER_TABLE_SYMBOL + r"\s*=\s*(\d+)")
_LOCATE_RE = re.compile(r"^\s*locate\s+(\w+)\s+(\S+)\s+at\s+\"([^\"]+)\"", re.M)
_COMPONENT_DECL_RE = re.compile(
    r"^\s*(active|queued|passive)\s+component\s+\$?(\w+)\s*\{", re.M
)
_ASYNC_PORT_RE = re.compile(r"^\s*async\s+input\s+port\s+\$?(\w+)\s*:(.*)$", re.M)
_INSTANCE_DECL_RE = re.compile(r"^\s*instance\s+\$?(\w+)\s*:\s*([\w.$]+)", re.M)
_LINE_COMMENT_RE = re.compile(r"(#|@<|@).*$")


def parse_queue_sizes(header_text: str) -> Dict[str, int]:
    """Parse the QueueSizes enum out of a generated <Deployment>TopologyAc.hpp

    Args:
        header_text: contents of the generated topology header

    Returns:
        mapping of enumerator name (e.g. "CdhCore_health") to queue depth
    """
    match = _QUEUE_BLOCK_RE.search(header_text)
    if match is None:
        return {}
    return {name: int(value) for name, value in _ENUMERATOR_RE.findall(match.group(1))}


def parse_instance_types(header_text: str) -> Dict[str, str]:
    """Parse the `extern <Type> <name>;` instance declarations out of a generated topology header

    Namespaces are tracked by counting braces so nested modules produce paths such as "CdhCore::health".

    Args:
        header_text: contents of the generated topology header

    Returns:
        mapping of C++ instance path to C++ component type
    """
    instances = {}
    depth = 0
    stack: List[Tuple[str, int]] = []
    for line in header_text.splitlines():
        namespace = _NAMESPACE_RE.match(line)
        if namespace is not None:
            stack.append((namespace.group(1), depth))
        extern = _EXTERN_RE.match(line)
        if extern is not None:
            path = "::".join([name for name, _ in stack] + [extern.group(2)])
            instances[path] = extern.group(1)
        depth += line.count("{") - line.count("}")
        while stack and depth <= stack[-1][1]:
            stack.pop()
    return instances


def parse_connections(source_text: str) -> List[Connection]:
    """Parse the port connections out of a generated <Deployment>TopologyAc.cpp

    Args:
        source_text: contents of the generated topology source

    Returns:
        list of connections in file order
    """
    return [
        Connection(source, source_port, destination, destination_port)
        for source, source_port, destination, destination_port in _CONNECTION_RE.findall(
            source_text
        )
    ]


def parse_health_instances(source_text: str) -> List[str]:
    """Return the C++ paths of instances that receive ping entries (i.e. Svc.Health instances)"""
    seen = []
    for instance in _PING_ENTRIES_RE.findall(source_text):
        if instance not in seen:
            seen.append(instance)
    return seen


def parse_dispatcher_table_size(config_text: str) -> Optional[int]:
    """Parse CMD_DISPATCHER_DISPATCH_TABLE_SIZE out of CommandDispatcherImplCfg.hpp"""
    match = _DISPATCHER_TABLE_RE.search(config_text)
    return int(match.group(1)) if match else None


def parse_locs(locs_text: str) -> Dict[str, Dict[str, str]]:
    """Parse a locs.fpp file

    Args:
        locs_text: contents of locs.fpp

    Returns:
        mapping of kind ("component", "instance", "topology", ...) to {qualified name: path string}. `$` escapes
        are removed from the qualified names.
    """
    located: Dict[str, Dict[str, str]] = {}
    for kind, name, path in _LOCATE_RE.findall(locs_text):
        located.setdefault(kind, {})[name.replace("$", "")] = path
    return located


def _strip_comment(text: str) -> str:
    """Remove an FPP line comment or annotation from a line"""
    return _LINE_COMMENT_RE.sub("", text)


def _join_continuations(text: str) -> str:
    """Join FPP backslash-newline continuations"""
    return re.sub(r"\\\s*\n", " ", text)


def parse_component_fpp(
    fpp_text: str, component: str
) -> Optional[Tuple[str, Dict[str, str]]]:
    """Parse the kind and async input ports of one component out of an FPP source file

    Args:
        fpp_text: contents of the FPP file
        component: unqualified component name to look for

    Returns:
        tuple of kind ("active", "queued" or "passive") and mapping of async input port name to its overflow
        behavior ("" for assert, "drop" or "hook"), or None when the component is not declared in the text
    """
    text = _join_continuations(fpp_text)
    declarations = list(_COMPONENT_DECL_RE.finditer(text))
    for index, declaration in enumerate(declarations):
        if declaration.group(2) != component:
            continue
        end = (
            declarations[index + 1].start()
            if index + 1 < len(declarations)
            else len(text)
        )
        body = text[declaration.end() : end]
        ports = {}
        for name, rest in _ASYNC_PORT_RE.findall(body):
            tokens = _strip_comment(rest).split()
            behavior = ""
            for token in tokens:
                if token in ("drop", "hook"):
                    behavior = token
            ports[name] = behavior
        return declaration.group(1), ports
    return None


def parse_instance_fpp(fpp_text: str, instance: str) -> Optional[str]:
    """Parse the component type of one instance declaration out of an FPP source file

    Args:
        fpp_text: contents of the FPP file
        instance: unqualified instance name to look for

    Returns:
        the component name as written in the declaration (may be partially qualified), or None if not found
    """
    text = _join_continuations(fpp_text)
    for name, component in _INSTANCE_DECL_RE.findall(text):
        if name == instance:
            return component.replace("$", "")
    return None


def resolve_component_name(
    written: str, instance_qualified: str, known: Dict[str, str]
) -> Optional[str]:
    """Resolve a possibly partially-qualified component reference to a fully-qualified locs.fpp key

    Tries the name as written, then prefixed with each enclosing module of the instance, then any unique known
    component whose qualified name ends with the written name.

    Args:
        written: component name as written in the instance declaration
        instance_qualified: fully-qualified instance name the declaration belongs to
        known: mapping of fully-qualified component names to anything (only keys are used)

    Returns:
        fully-qualified component name, or None if it cannot be resolved unambiguously
    """
    if written in known:
        return written
    modules = instance_qualified.split(".")[:-1]
    for count in range(len(modules), 0, -1):
        candidate = ".".join(modules[:count] + [written])
        if candidate in known:
            return candidate
    suffix_matches = [name for name in known if name.endswith("." + written)]
    return suffix_matches[0] if len(suffix_matches) == 1 else None


# ---------------------------------------------------------------------------------------------------------------------
# Loading the model from a build cache
# ---------------------------------------------------------------------------------------------------------------------


def find_dispatcher_config(build_root: Path) -> Optional[Path]:
    """Locate the generated CommandDispatcherImplCfg.hpp within the build cache"""
    default = build_root / "F-Prime" / "default" / "config" / DISPATCHER_CONFIG_NAME
    if default.exists():
        return default
    return next(build_root.rglob(DISPATCHER_CONFIG_NAME), None)


def find_topology_header(cache_dir: Path) -> Path:
    """Locate the single generated <Deployment>TopologyAc.hpp for a build cache directory

    Looks in the directory itself, then its `Top` subdirectory (the usual layout when run from a deployment
    directory), then recursively.

    Args:
        cache_dir: build cache directory matching the context the command was run in

    Returns:
        path to the generated topology header

    Raises:
        TopologyCheckException: when no topology, or more than one deployment's topology, is found
    """
    pattern = f"*{TOPOLOGY_HEADER_SUFFIX}"
    headers = sorted(cache_dir.glob(pattern)) or sorted(
        (cache_dir / "Top").glob(pattern)
    )
    if not headers:
        headers = sorted(cache_dir.rglob(pattern))
    if not headers:
        raise TopologyCheckException(
            f"No generated topology found under {cache_dir}. Run '{COMMAND_NAME}' from a deployment directory after "
            "'fprime-util generate' or 'fprime-util build'."
        )
    if len(headers) > 1:
        names = ", ".join(str(header.relative_to(cache_dir)) for header in headers)
        raise TopologyCheckException(
            f"Found more than one generated topology under {cache_dir} ({names}). Run '{COMMAND_NAME}' from a "
            "single deployment directory."
        )
    return headers[0]


def _load_fpp_model(model: TopologyModel, build_root: Path, locs_path: Path):
    """Fill the FPP-side fields of the model using locs.fpp and the FPP sources it points at"""
    located = parse_locs(locs_path.read_text())
    components = located.get("component", {})
    instances = located.get("instance", {})
    component_cache: Dict[str, Optional[Tuple[str, Dict[str, str]]]] = {}

    def component_info(qualified: str) -> Optional[Tuple[str, Dict[str, str]]]:
        if qualified not in component_cache:
            path = build_root / components[qualified]
            info = None
            if path.exists():
                info = parse_component_fpp(path.read_text(), qualified.split(".")[-1])
            component_cache[qualified] = info
        return component_cache[qualified]

    for cpp_path in model.instance_types:
        qualified = model.fpp_name(cpp_path)
        instance_file = instances.get(qualified)
        if instance_file is None:
            continue
        instance_path = build_root / instance_file
        if not instance_path.exists():
            continue
        written = parse_instance_fpp(
            instance_path.read_text(), qualified.split(".")[-1]
        )
        if written is None:
            continue
        component = resolve_component_name(written, qualified, components)
        if component is None:
            continue
        info = component_info(component)
        if info is None:
            continue
        kind, ports = info
        model.instance_components[qualified] = component
        model.component_kinds[component] = kind
        model.async_ports[component] = ports
    model.fpp_available = True


def load_model(build: Build, context: Path) -> TopologyModel:
    """Load the topology model for the deployment at `context` from its build cache

    Args:
        build: loaded build object
        context: source directory of the deployment (or its Top directory)

    Returns:
        populated TopologyModel

    Raises:
        TopologyCheckException: when no generated topology exists for the context
    """
    cache_dir = build.get_build_cache_path(context)
    header = find_topology_header(cache_dir)
    deployment = header.name[: -len(TOPOLOGY_HEADER_SUFFIX)]
    cache_dir = header.parent
    model = TopologyModel(deployment=deployment)

    header_text = header.read_text()
    model.queue_sizes = parse_queue_sizes(header_text)
    model.instance_types = parse_instance_types(header_text)

    source = cache_dir / f"{deployment}TopologyAc.cpp"
    if not source.exists():
        raise TopologyCheckException(f"Missing generated topology source: {source}")
    source_text = source.read_text()
    model.connections = parse_connections(source_text)
    model.health_instances = parse_health_instances(source_text)

    dictionary = cache_dir / f"{deployment}TopologyDictionary.json"
    if dictionary.exists():
        with open(dictionary, "r") as file_handle:
            model.command_count = len(json.load(file_handle).get("commands", []))

    build_root = Path(build.build_dir)
    dispatcher_config = find_dispatcher_config(build_root)
    if dispatcher_config is not None:
        model.dispatcher_table_size = parse_dispatcher_table_size(
            dispatcher_config.read_text()
        )

    try:
        _load_fpp_model(model, build_root, FppUtility.get_locations_file(build))
    except FppMissingSupportFiles:
        model.fpp_available = False
    return model


# ---------------------------------------------------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------------------------------------------------


def _health_instances(model: TopologyModel) -> List[str]:
    """Health instances: those receiving ping entries, plus any whose FPP component is Svc.Health"""
    instances = list(model.health_instances)
    for qualified, component in model.instance_components.items():
        cpp_path = qualified.replace(".", "::")
        if component == "Svc.Health" and cpp_path not in instances:
            instances.append(cpp_path)
    return instances


def rule_health_ping_capacity(model: TopologyModel) -> List[Finding]:
    """Rule 1: a Health instance's queue must hold one ping reply per ping target"""
    rule = "health-ping-capacity"
    findings = []
    instances = _health_instances(model)
    if not instances:
        return [
            Finding(LEVEL_WARNING, rule, "no Svc.Health instance found; rule skipped")
        ]
    for instance in instances:
        targets = sum(
            1
            for c in model.connections
            if c.source == instance and c.source_port == HEALTH_PING_OUTPUT_PORT
        )
        depth = model.queue_depth(instance)
        name = model.fpp_name(instance)
        if depth is None:
            findings.append(
                Finding(
                    LEVEL_WARNING, rule, f"{name}: no queue size found; rule skipped"
                )
            )
        elif depth < targets:
            findings.append(
                Finding(
                    LEVEL_ERROR,
                    rule,
                    f"{name}: queue depth {depth} < {targets} ping targets. Health drains its queue only on Run, "
                    f"so the first ping cycle will overflow it (FW_ASSERT with Os::Queue::FULL). Raise the "
                    f"instance's 'queue size' (CdhCoreConfig.QueueSizes.health for the CdhCore subtopology) "
                    f"to at least {targets}.",
                )
            )
        else:
            findings.append(
                Finding(
                    LEVEL_OK,
                    rule,
                    f"{name}: queue depth {depth} >= {targets} ping targets",
                )
            )
    return findings


def rule_command_dispatcher_table(model: TopologyModel) -> List[Finding]:
    """Rule 2: the dispatcher opcode table must hold every command in the dictionary"""
    rule = "command-dispatcher-table"
    if model.command_count is None:
        return [
            Finding(LEVEL_WARNING, rule, "topology dictionary not found; rule skipped")
        ]
    if model.dispatcher_table_size is None:
        return [
            Finding(
                LEVEL_WARNING,
                rule,
                f"{DISPATCHER_CONFIG_NAME} not found in build cache; rule skipped",
            )
        ]
    if model.command_count > model.dispatcher_table_size:
        return [
            Finding(
                LEVEL_ERROR,
                rule,
                f"{model.command_count} commands > {DISPATCHER_TABLE_SYMBOL} {model.dispatcher_table_size}. "
                f"CommandDispatcher will FW_ASSERT while registering opcode number "
                f"{model.dispatcher_table_size + 1}. Override {DISPATCHER_CONFIG_NAME} in the project config "
                f"directory with a table size of at least {model.command_count}.",
            )
        ]
    return [
        Finding(
            LEVEL_OK,
            rule,
            f"{model.command_count} commands <= {DISPATCHER_TABLE_SYMBOL} {model.dispatcher_table_size}",
        )
    ]


def rule_queued_component_burst(model: TopologyModel) -> List[Finding]:
    """Rule 3 (heuristic): a queued component's queue should hold one message per asserting async connection"""
    rule = "queued-component-burst"
    if not model.fpp_available:
        return [
            Finding(
                LEVEL_WARNING, rule, "locs.fpp or FPP sources not found; rule skipped"
            )
        ]
    health = set(_health_instances(model))
    findings = []
    checked = 0
    for qualified, component in sorted(model.instance_components.items()):
        cpp_path = qualified.replace(".", "::")
        if model.component_kinds.get(component) != "queued" or cpp_path in health:
            continue
        depth = model.queue_depth(cpp_path)
        if depth is None:
            continue
        checked += 1
        asserting_ports = {
            port
            for port, behavior in model.async_ports.get(component, {}).items()
            if not behavior
        }
        burst = sum(
            1
            for c in model.connections
            if c.destination == cpp_path and c.destination_port in asserting_ports
        )
        if burst > depth:
            findings.append(
                Finding(
                    LEVEL_WARNING,
                    rule,
                    f"{qualified} ({component}): queue depth {depth} < {burst} connections into async input ports "
                    f"that assert on overflow. If every connection can deliver one message between drains of the "
                    f"queue, the component will FW_ASSERT with Os::Queue::FULL. This is a heuristic; verify the "
                    f"real message rate or raise the instance's 'queue size'.",
                )
            )
    if not findings:
        findings.append(
            Finding(
                LEVEL_OK,
                rule,
                f"no queued component exceeds its queue depth ({checked} instance(s) checked)",
            )
        )
    return findings


RULES: List[Callable[[TopologyModel], List[Finding]]] = [
    rule_health_ping_capacity,
    rule_command_dispatcher_table,
    rule_queued_component_burst,
]


def check_model(model: TopologyModel) -> List[Finding]:
    """Evaluate every rule against the model"""
    findings = []
    for rule in RULES:
        findings.extend(rule(model))
    return findings


def report(findings: List[Finding], warnings_as_errors: bool = False) -> int:
    """Print findings and compute the exit code

    Args:
        findings: findings to print
        warnings_as_errors: treat warnings as failures

    Returns:
        0 when the check passes, 1 otherwise
    """
    failed = False
    for finding in findings:
        line = f"[{finding.level}] {finding.rule}: {finding.message}"
        if finding.level == LEVEL_ERROR or (
            finding.level == LEVEL_WARNING and warnings_as_errors
        ):
            failed = True
            print(line, file=sys.stderr)
        else:
            print(line)
    return 1 if failed else 0


# ---------------------------------------------------------------------------------------------------------------------
# Command line integration
# ---------------------------------------------------------------------------------------------------------------------


def run_topology_check(
    build: "Build",
    parsed: argparse.Namespace,
    _: Dict[str, str],
    __: Dict[str, str],
    ___: List[str],
) -> int:
    """Run the topology-check command

    Args:
        build: build directory output
        parsed: parsed input arguments
        _: unused cmake_args
        __: unused make_args
        ___: unused pass-through arguments

    Returns:
        process exit code
    """
    model = load_model(build, Path(parsed.path))
    print(f"[INFO] Checking topology of deployment '{model.deployment}'")
    return report(check_model(model), warnings_as_errors=parsed.warnings_as_errors)


def add_topology_check_parsers(
    subparsers, common: argparse.ArgumentParser, help_text
) -> Tuple[Dict[str, Callable], Dict[str, argparse.ArgumentParser]]:
    """Sets up the topology-check command line parser

    Args:
        subparsers: subparsers to add to
        common: common parser for all fprime-util commands
        help_text: HelpText class used to look up help strings

    Returns:
        Tuple of dictionary mapping command name to processor, and command to parser
    """
    parser = subparsers.add_parser(
        COMMAND_NAME,
        description=help_text.long(COMMAND_NAME),
        help=help_text.short(COMMAND_NAME),
        parents=[common],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_argument_group(f"{COMMAND_NAME} arguments")
    group.add_argument(
        "--warnings-as-errors",
        action="store_true",
        default=False,
        help="Return a failure exit code when heuristic warnings are reported",
    )
    return {COMMAND_NAME: run_topology_check}, {COMMAND_NAME: parser}
