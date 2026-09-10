"""
Tests for fprime.fpp.topology_check
"""

import argparse
import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fprime.fpp.topology_check import (
    LEVEL_ERROR,
    LEVEL_OK,
    LEVEL_WARNING,
    Connection,
    TopologyCheckException,
    TopologyModel,
    check_model,
    find_topology_header,
    load_model,
    parse_component_fpp,
    parse_connections,
    parse_dispatcher_table_size,
    parse_health_instances,
    parse_instance_fpp,
    parse_instance_types,
    parse_locs,
    parse_queue_sizes,
    report,
    resolve_component_name,
    rule_command_dispatcher_table,
    rule_health_ping_capacity,
    rule_queued_component_burst,
    run_topology_check,
)

TOPOLOGY_HPP = textwrap.dedent("""
    namespace CdhCore {
      //! health
      extern Svc::Health health;
    }
    namespace CdhCore {
      extern Svc::CommandDispatcher cmdDisp;
    }
    namespace Deploy {
      namespace Nested {
        extern Svc::ActiveRateGroup rateGroup5Hz;
      }
    }
    extern Svc::Version version;
    namespace Deploy {
      extern Deploy::Bufferer bufferer;
    }
    namespace Deploy {
      namespace QueueSizes {
        enum {
          CdhCore_cmdDisp = 10,
          CdhCore_health = 64,
          Deploy_Nested_rateGroup5Hz = 20,
          Deploy_bufferer = 2
        };
      }
      namespace InstanceIds {
        enum {
          CdhCore_health = 0x1002000
        };
      }
    }
    """)

TOPOLOGY_CPP = textwrap.dedent("""
    void setupTopology() {
      CdhCore::health.setPingEntries(
          ConfigObjects::CdhCore_health::pingEntries,
          3,
          ConfigObjects::CdhCore_health::pingEntries[0].key
      );
      CdhCore::health.set_PingSend_OutputPort(
          0,
          CdhCore::cmdDisp.get_pingIn_InputPort(0)
      );
      CdhCore::health.set_PingSend_OutputPort(
          1,
          Deploy::Nested::rateGroup5Hz.get_PingIn_InputPort(0)
      );
      CdhCore::health.set_PingSend_OutputPort(2, Deploy::bufferer.get_pingIn_InputPort(0));
      CdhCore::cmdDisp.set_pingOut_OutputPort(0, CdhCore::health.get_PingReturn_InputPort(0));
      Deploy::Nested::rateGroup5Hz.set_PingOut_OutputPort(
          0,
          CdhCore::health.get_PingReturn_InputPort(1)
      );
      Deploy::bufferer.set_pingOut_OutputPort(0, CdhCore::health.get_PingReturn_InputPort(2));
      Deploy::Nested::rateGroup5Hz.set_RateGroupMemberOut_OutputPort(0, Deploy::bufferer.get_bufferIn_InputPort(0));
      Deploy::Nested::rateGroup5Hz.set_RateGroupMemberOut_OutputPort(1, Deploy::bufferer.get_bufferIn_InputPort(1));
      Deploy::Nested::rateGroup5Hz.set_RateGroupMemberOut_OutputPort(2, Deploy::bufferer.get_bufferIn_InputPort(2));
      Deploy::Nested::rateGroup5Hz.set_RateGroupMemberOut_OutputPort(3, Deploy::bufferer.get_dropped_InputPort(0));
    }
    """)

HEALTH_FPP = textwrap.dedent("""
    module Svc {
      @ Health component
      queued component Health {
        @ Ping output port
        output port PingSend: [HealthPingPorts] Svc.Ping
        @ Ping return port
        async input port PingReturn: [HealthPingPorts] Svc.Ping
        sync input port Run: Svc.Sched
      }
    }
    """)

BUFFERER_FPP = textwrap.dedent("""
    module Deploy {
      queued component Bufferer {
        async input port bufferIn: [3] Fw.BufferSend
        async input port dropped: Fw.BufferSend drop
        async input port hooked: Fw.BufferSend \\
          hook
        sync input port run: Svc.Sched
      }
      passive component Other {
        sync input port in: Svc.Sched
      }
    }
    """)

RATE_GROUP_FPP = textwrap.dedent("""
    module Svc {
      active component ActiveRateGroup {
        async input port CycleIn: Svc.Cycle drop
        async input port PingIn: Ping drop # trailing comment with drop
      }
    }
    """)

CDHCORE_FPP = textwrap.dedent("""
    module CdhCore {
        instance $health: Svc.Health base id CdhCoreConfig.BASE_ID + 0x002000 \\
            queue size CdhCoreConfig.QueueSizes.$health \\
        {
            phase Fpp.ToCpp.Phases.configConstants \"\"\"
            enum {
            \"\"\"
        }
        instance cmdDisp: Svc.CommandDispatcher base id CdhCoreConfig.BASE_ID + 0x000000
    }
    """)

DEPLOY_INSTANCES_FPP = textwrap.dedent("""
    module Deploy {
      module Nested {
        instance rateGroup5Hz: Svc.ActiveRateGroup base id 0x20000000 \\
          queue size Default.QUEUE_SIZE \\
          stack size Default.STACK_SIZE \\
          priority 44
      }
      instance bufferer: Bufferer base id 0x20001000 queue size 2
      instance version: Svc.Version base id 0x20002000
    }
    """)

LOCS_FPP = textwrap.dedent("""
    locate component Svc.Health at "src/Health.fpp"
    locate component Deploy.Bufferer at "src/Bufferer.fpp"
    locate component Svc.ActiveRateGroup at "src/ActiveRateGroup.fpp"
    locate instance CdhCore.$health at "src/CdhCore.fpp"
    locate instance CdhCore.cmdDisp at "src/CdhCore.fpp"
    locate instance Deploy.Nested.rateGroup5Hz at "src/instances.fpp"
    locate instance Deploy.bufferer at "src/instances.fpp"
    locate instance Deploy.version at "src/instances.fpp"
    locate topology Deploy.Deploy at "src/topology.fpp"
    """)

DISPATCHER_CFG = textwrap.dedent("""
    enum {
        CMD_DISPATCHER_DISPATCH_TABLE_SIZE = 150,  // !< The size of the table holding opcodes to dispatch
        CMD_DISPATCHER_SEQUENCER_TABLE_SIZE = 25,  // !< The size of the table holding commands in progress
    };
    """)


def make_dictionary(command_count: int) -> str:
    """Build a minimal topology dictionary with the given number of commands"""
    commands = [
        {"name": f"Deploy.comp.CMD_{i}", "opcode": i} for i in range(command_count)
    ]
    return json.dumps({"metadata": {}, "commands": commands})


# ---------------------------------------------------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------------------------------------------------


def test_parse_queue_sizes():
    sizes = parse_queue_sizes(TOPOLOGY_HPP)
    assert sizes == {
        "CdhCore_cmdDisp": 10,
        "CdhCore_health": 64,
        "Deploy_Nested_rateGroup5Hz": 20,
        "Deploy_bufferer": 2,
    }


def test_parse_queue_sizes_missing():
    assert parse_queue_sizes("namespace Nothing {}") == {}


def test_parse_instance_types():
    types = parse_instance_types(TOPOLOGY_HPP)
    assert types == {
        "CdhCore::health": "Svc::Health",
        "CdhCore::cmdDisp": "Svc::CommandDispatcher",
        "Deploy::Nested::rateGroup5Hz": "Svc::ActiveRateGroup",
        "version": "Svc::Version",
        "Deploy::bufferer": "Deploy::Bufferer",
    }


def test_parse_connections():
    connections = parse_connections(TOPOLOGY_CPP)
    assert (
        Connection("CdhCore::health", "PingSend", "CdhCore::cmdDisp", "pingIn")
        in connections
    )
    assert (
        Connection(
            "CdhCore::health", "PingSend", "Deploy::Nested::rateGroup5Hz", "PingIn"
        )
        in connections
    )
    assert (
        Connection("Deploy::bufferer", "pingOut", "CdhCore::health", "PingReturn")
        in connections
    )
    assert len(connections) == 10


def test_parse_health_instances():
    assert parse_health_instances(TOPOLOGY_CPP) == ["CdhCore::health"]
    assert parse_health_instances("nothing here") == []


def test_parse_dispatcher_table_size():
    assert parse_dispatcher_table_size(DISPATCHER_CFG) == 150
    assert parse_dispatcher_table_size("enum { OTHER = 3 };") is None


def test_parse_locs():
    located = parse_locs(LOCS_FPP)
    assert located["component"]["Svc.Health"] == "src/Health.fpp"
    assert located["instance"]["CdhCore.health"] == "src/CdhCore.fpp"
    assert located["instance"]["Deploy.Nested.rateGroup5Hz"] == "src/instances.fpp"
    assert located["topology"]["Deploy.Deploy"] == "src/topology.fpp"


def test_parse_component_fpp_queued_with_overflow_behaviors():
    kind, ports = parse_component_fpp(BUFFERER_FPP, "Bufferer")
    assert kind == "queued"
    assert ports == {"bufferIn": "", "dropped": "drop", "hooked": "hook"}
    # A second component in the same file is isolated from the first
    assert parse_component_fpp(BUFFERER_FPP, "Other") == ("passive", {})
    assert parse_component_fpp(BUFFERER_FPP, "Missing") is None


def test_parse_component_fpp_ignores_comments():
    kind, ports = parse_component_fpp(RATE_GROUP_FPP, "ActiveRateGroup")
    assert kind == "active"
    assert ports == {"CycleIn": "drop", "PingIn": "drop"}
    assert parse_component_fpp(HEALTH_FPP, "Health") == ("queued", {"PingReturn": ""})


def test_parse_instance_fpp():
    assert parse_instance_fpp(CDHCORE_FPP, "health") == "Svc.Health"
    assert parse_instance_fpp(CDHCORE_FPP, "cmdDisp") == "Svc.CommandDispatcher"
    assert parse_instance_fpp(DEPLOY_INSTANCES_FPP, "bufferer") == "Bufferer"
    assert (
        parse_instance_fpp(DEPLOY_INSTANCES_FPP, "rateGroup5Hz")
        == "Svc.ActiveRateGroup"
    )
    assert parse_instance_fpp(DEPLOY_INSTANCES_FPP, "nope") is None


def test_resolve_component_name():
    known = {
        "Svc.Health": "",
        "Deploy.Bufferer": "",
        "Other.Bufferer": "",
        "Only.Thing": "",
    }
    assert resolve_component_name("Svc.Health", "CdhCore.health", known) == "Svc.Health"
    assert (
        resolve_component_name("Bufferer", "Deploy.bufferer", known)
        == "Deploy.Bufferer"
    )
    assert resolve_component_name("Thing", "Deploy.Nested.thing", known) == "Only.Thing"
    assert resolve_component_name("Bufferer", "Elsewhere.x", known) is None


# ---------------------------------------------------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------------------------------------------------


def make_model(health_depth=64, targets=28, commands=152, table=256) -> TopologyModel:
    """Build a model with the given health/ping and dispatcher/command numbers"""
    model = TopologyModel(deployment="Deploy")
    model.queue_sizes = {"CdhCore_health": health_depth}
    model.instance_types = {"CdhCore::health": "Svc::Health"}
    model.health_instances = ["CdhCore::health"]
    model.connections = [
        Connection("CdhCore::health", "PingSend", f"Deploy::c{i}", "pingIn")
        for i in range(targets)
    ] + [
        Connection(f"Deploy::c{i}", "pingOut", "CdhCore::health", "PingReturn")
        for i in range(targets)
    ]
    model.command_count = commands
    model.dispatcher_table_size = table
    model.fpp_available = True
    model.instance_components = {"CdhCore.health": "Svc.Health"}
    model.component_kinds = {"Svc.Health": "queued"}
    model.async_ports = {"Svc.Health": {"PingReturn": ""}}
    return model


def levels(findings):
    return [(finding.level, finding.rule) for finding in findings]


def test_rule_health_ping_capacity_pass_and_fail():
    ok = rule_health_ping_capacity(make_model(health_depth=64, targets=28))
    assert levels(ok) == [(LEVEL_OK, "health-ping-capacity")]
    assert "64 >= 28" in ok[0].message

    bad = rule_health_ping_capacity(make_model(health_depth=25, targets=28))
    assert levels(bad) == [(LEVEL_ERROR, "health-ping-capacity")]
    assert "queue depth 25 < 28 ping targets" in bad[0].message
    assert "CdhCoreConfig.QueueSizes.health" in bad[0].message


def test_rule_health_ping_capacity_skips_without_health():
    model = make_model()
    model.health_instances = []
    model.instance_components = {}
    assert levels(rule_health_ping_capacity(model)) == [
        (LEVEL_WARNING, "health-ping-capacity")
    ]


def test_rule_health_found_via_fpp_component():
    model = make_model(health_depth=1, targets=3)
    model.health_instances = (
        []
    )  # no setPingEntries in generated code, but FPP says it is Svc.Health
    assert levels(rule_health_ping_capacity(model)) == [
        (LEVEL_ERROR, "health-ping-capacity")
    ]


def test_rule_command_dispatcher_table():
    assert levels(
        rule_command_dispatcher_table(make_model(commands=152, table=256))
    ) == [(LEVEL_OK, "command-dispatcher-table")]
    bad = rule_command_dispatcher_table(make_model(commands=152, table=150))
    assert levels(bad) == [(LEVEL_ERROR, "command-dispatcher-table")]
    assert "152 commands > CMD_DISPATCHER_DISPATCH_TABLE_SIZE 150" in bad[0].message

    missing = make_model()
    missing.dispatcher_table_size = None
    assert levels(rule_command_dispatcher_table(missing)) == [
        (LEVEL_WARNING, "command-dispatcher-table")
    ]
    missing.command_count = None
    assert levels(rule_command_dispatcher_table(missing)) == [
        (LEVEL_WARNING, "command-dispatcher-table")
    ]


def make_burst_model(depth: int, ports: dict, kind: str = "queued") -> TopologyModel:
    """Model with one non-health queued instance receiving three connections into port `in` and one into `other`"""
    model = make_model()
    model.queue_sizes["Deploy_bufferer"] = depth
    model.instance_types["Deploy::bufferer"] = "Deploy::Bufferer"
    model.instance_components["Deploy.bufferer"] = "Deploy.Bufferer"
    model.component_kinds["Deploy.Bufferer"] = kind
    model.async_ports["Deploy.Bufferer"] = ports
    model.connections += [
        Connection("Deploy::rg", "out", "Deploy::bufferer", "in") for _ in range(3)
    ] + [Connection("Deploy::rg", "out", "Deploy::bufferer", "other")]
    return model


def test_rule_queued_component_burst_warns():
    findings = rule_queued_component_burst(
        make_burst_model(2, {"in": "", "other": "drop"})
    )
    assert levels(findings) == [(LEVEL_WARNING, "queued-component-burst")]
    assert (
        "Deploy.bufferer (Deploy.Bufferer): queue depth 2 < 3 connections"
        in findings[0].message
    )


def test_rule_queued_component_burst_passes_when_deep_enough():
    findings = rule_queued_component_burst(make_burst_model(4, {"in": "", "other": ""}))
    assert levels(findings) == [(LEVEL_OK, "queued-component-burst")]
    assert "1 instance(s) checked" in findings[0].message


def test_rule_queued_component_burst_ignores_drop_hook_and_non_queued():
    # drop and hook ports never assert, so they do not count toward the burst
    assert levels(
        rule_queued_component_burst(
            make_burst_model(1, {"in": "drop", "other": "hook"})
        )
    ) == [(LEVEL_OK, "queued-component-burst")]
    # active components drain on their own thread; passive have no queue
    for kind in ("active", "passive"):
        findings = rule_queued_component_burst(
            make_burst_model(1, {"in": ""}, kind=kind)
        )
        assert levels(findings) == [(LEVEL_OK, "queued-component-burst")]
        assert "0 instance(s) checked" in findings[0].message


def test_rule_queued_component_burst_skips_health_and_missing_fpp():
    # The health instance itself is covered by rule 1 and must not be double reported
    model = make_model(health_depth=1, targets=5)
    assert levels(rule_queued_component_burst(model)) == [
        (LEVEL_OK, "queued-component-burst")
    ]
    model.fpp_available = False
    assert levels(rule_queued_component_burst(model)) == [
        (LEVEL_WARNING, "queued-component-burst")
    ]


def test_check_model_runs_all_rules():
    assert [rule for _, rule in levels(check_model(make_model()))] == [
        "health-ping-capacity",
        "command-dispatcher-table",
        "queued-component-burst",
    ]


# ---------------------------------------------------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------------------------------------------------


def test_report_exit_codes(capsys):
    from fprime.fpp.topology_check import Finding

    assert report([Finding(LEVEL_OK, "r", "fine")]) == 0
    assert report([Finding(LEVEL_WARNING, "r", "hmm")]) == 0
    assert report([Finding(LEVEL_WARNING, "r", "hmm")], warnings_as_errors=True) == 1
    assert (
        report([Finding(LEVEL_OK, "r", "fine"), Finding(LEVEL_ERROR, "r", "bad")]) == 1
    )
    captured = capsys.readouterr()
    assert "[OK] r: fine" in captured.out
    assert "[ERROR] r: bad" in captured.err


# ---------------------------------------------------------------------------------------------------------------------
# Loading from a fake build cache
# ---------------------------------------------------------------------------------------------------------------------


def write_fake_cache(
    root: Path,
    health_depth=64,
    commands=3,
    table=150,
    with_locs=True,
    with_dictionary=True,
):
    """Populate `root` as a build cache for deployment "Deploy" and return the deployment cache dir"""
    top = root / "Deploy" / "Top"
    top.mkdir(parents=True)
    (top / "DeployTopologyAc.hpp").write_text(
        TOPOLOGY_HPP.replace("CdhCore_health = 64", f"CdhCore_health = {health_depth}")
    )
    (top / "DeployTopologyAc.cpp").write_text(TOPOLOGY_CPP)
    if with_dictionary:
        (top / "DeployTopologyDictionary.json").write_text(make_dictionary(commands))
    config = root / "F-Prime" / "default" / "config"
    config.mkdir(parents=True)
    (config / "CommandDispatcherImplCfg.hpp").write_text(
        DISPATCHER_CFG.replace("= 150", f"= {table}")
    )
    if with_locs:
        (root / "locs.fpp").write_text(LOCS_FPP)
        src = root / "src"
        src.mkdir()
        (src / "Health.fpp").write_text(HEALTH_FPP)
        (src / "Bufferer.fpp").write_text(BUFFERER_FPP)
        (src / "ActiveRateGroup.fpp").write_text(RATE_GROUP_FPP)
        (src / "CdhCore.fpp").write_text(CDHCORE_FPP)
        (src / "instances.fpp").write_text(DEPLOY_INSTANCES_FPP)
    return root / "Deploy"


@pytest.fixture
def mock_build(tmp_path):
    """Build object whose cache root is tmp_path and whose context maps to the deployment cache dir"""
    build = MagicMock()
    build.build_dir = tmp_path
    build.get_build_cache_path.side_effect = lambda context: tmp_path / "Deploy"
    return build


def test_find_topology_header(tmp_path):
    deploy = write_fake_cache(tmp_path)
    assert find_topology_header(deploy) == deploy / "Top" / "DeployTopologyAc.hpp"
    assert (
        find_topology_header(deploy / "Top") == deploy / "Top" / "DeployTopologyAc.hpp"
    )
    with pytest.raises(TopologyCheckException):
        find_topology_header(tmp_path / "F-Prime")
    # Two deployments under one directory is ambiguous
    other = tmp_path / "Other" / "Top"
    other.mkdir(parents=True)
    (other / "OtherTopologyAc.hpp").write_text("")
    with pytest.raises(TopologyCheckException):
        find_topology_header(tmp_path)


def test_load_model_full(mock_build, tmp_path):
    write_fake_cache(tmp_path)
    model = load_model(mock_build, Path("Deploy"))
    assert model.deployment == "Deploy"
    assert model.queue_sizes["CdhCore_health"] == 64
    assert (
        model.instance_types["Deploy::Nested::rateGroup5Hz"] == "Svc::ActiveRateGroup"
    )
    assert model.health_instances == ["CdhCore::health"]
    assert len(model.connections) == 10
    assert model.command_count == 3
    assert model.dispatcher_table_size == 150
    assert model.fpp_available
    assert model.instance_components == {
        "CdhCore.health": "Svc.Health",
        "Deploy.Nested.rateGroup5Hz": "Svc.ActiveRateGroup",
        "Deploy.bufferer": "Deploy.Bufferer",
    }
    assert model.component_kinds["Deploy.Bufferer"] == "queued"
    assert model.async_ports["Deploy.Bufferer"] == {
        "bufferIn": "",
        "dropped": "drop",
        "hooked": "hook",
    }


def test_load_model_without_optional_inputs(mock_build, tmp_path):
    write_fake_cache(tmp_path, with_locs=False, with_dictionary=False)
    model = load_model(mock_build, Path("Deploy"))
    assert model.command_count is None
    assert not model.fpp_available
    assert model.instance_components == {}


def test_load_model_missing_topology(mock_build, tmp_path):
    (tmp_path / "Deploy").mkdir()
    with pytest.raises(TopologyCheckException):
        load_model(mock_build, Path("Deploy"))


def test_end_to_end_clean(mock_build, tmp_path, capsys):
    # 3 ping targets, depth 64; 3 commands, table 150; bufferer depth 2 receives 3 asserting connections -> warning
    write_fake_cache(tmp_path)
    parsed = argparse.Namespace(path=Path("Deploy"), warnings_as_errors=False)
    assert run_topology_check(mock_build, parsed, {}, {}, []) == 0
    out = capsys.readouterr().out
    assert "[INFO] Checking topology of deployment 'Deploy'" in out
    assert (
        "[OK] health-ping-capacity: CdhCore.health: queue depth 64 >= 3 ping targets"
        in out
    )
    assert (
        "[OK] command-dispatcher-table: 3 commands <= CMD_DISPATCHER_DISPATCH_TABLE_SIZE 150"
        in out
    )
    assert (
        "[WARNING] queued-component-burst: Deploy.bufferer (Deploy.Bufferer): queue depth 2 < 3"
        in out
    )


def test_end_to_end_failures(mock_build, tmp_path, capsys):
    write_fake_cache(tmp_path, health_depth=2, commands=151, table=150)
    parsed = argparse.Namespace(path=Path("Deploy"), warnings_as_errors=False)
    assert run_topology_check(mock_build, parsed, {}, {}, []) == 1
    err = capsys.readouterr().err
    assert (
        "[ERROR] health-ping-capacity: CdhCore.health: queue depth 2 < 3 ping targets"
        in err
    )
    assert (
        "[ERROR] command-dispatcher-table: 151 commands > CMD_DISPATCHER_DISPATCH_TABLE_SIZE 150"
        in err
    )


def test_end_to_end_warnings_as_errors(mock_build, tmp_path):
    write_fake_cache(tmp_path)
    parsed = argparse.Namespace(path=Path("Deploy"), warnings_as_errors=True)
    assert run_topology_check(mock_build, parsed, {}, {}, []) == 1
