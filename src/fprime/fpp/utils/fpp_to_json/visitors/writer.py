import fprime.fpp.utils.fpp_to_json.node_structs as NodeStructs


class ModuleWriter:
    """
    Writer for an fpp module. Has open() and close() functions to write the module.
    """

    def __init__(self, module: NodeStructs.Module):
        self.module: NodeStructs.Module = module

    def open(self):
        return f"module {self.module.name} {{"

    def close(self):
        return "}"


class TopologyWriter:
    """
    Writer for an fpp topology. Has open() and close() functions to write the topology.
    """

    def __init__(self, topology: NodeStructs.Topology):
        self.topology: NodeStructs.Topology = topology

    def open(self):
        return f"topology {self.topology.name} {{"

    def close(self):
        return "}"


class ConstantWriter:
    """
    Writer for an fpp constant. Has write() function to write the constant out.
    """

    def __init__(self, constant: NodeStructs.Constant):
        self.constant: NodeStructs.Constant = constant

    def write(self):
        return f"constant {self.constant.id} = {self.constant.value}"


class InstanceSpecWriter:
    """
    Writer for an fpp instance spec. Has write() function to write the instance spec out.
    """

    def __init__(self, instance_spec: NodeStructs.InstanceSpec):
        self.instance_spec: NodeStructs.InstanceSpec = instance_spec

    def write(self):
        return f"{self.instance_spec.visibility} instance {self.instance_spec.name}"


class CompInstanceWriter:
    """
    Writer for an fpp component instance. Has write() function to write the component
    instance definition out.
    """

    def __init__(self, comp_instance: NodeStructs.ComponentInst):
        self.comp_instance: NodeStructs.ComponentInst = comp_instance

    def _writePhases(self):
        phaseOpen = False
        part = ""

        for phase in self.comp_instance.phases:
            if (
                self.comp_instance.phases[phase] is not None
                and self.comp_instance.phases[phase] != ""
            ):
                if not phaseOpen:
                    part += f"{{"
                    phaseOpen = True

                part += f'\n    phase Fpp.ToCpp.Phases.{phase} """\n'
                part += self.comp_instance.phases[phase]
                part += '"""'

        if phaseOpen:
            part += "}"

        return part

    def write(self):
        part_1 = f"instance {self.comp_instance.name}: {self.comp_instance.component_name} base id {self.comp_instance.base_id}"

        if (
            self.comp_instance.queue_size is not None
            and self.comp_instance.queue_size != "None"
        ):
            part_1 = part_1 + f" \\ \n    queue size {self.comp_instance.queue_size}"

        if (
            self.comp_instance.stack_size is not None
            and self.comp_instance.stack_size != "None"
        ):
            part_1 = part_1 + f" \\ \n    stack size {self.comp_instance.stack_size}"

        if (
            self.comp_instance.priority is not None
            and self.comp_instance.priority != "None"
        ):
            part_1 = part_1 + f" \\ \n    priority {self.comp_instance.priority}"

        if self.comp_instance.cpu is not None and self.comp_instance.cpu != "None":
            part_1 = part_1 + f" \\ \n    cpu {self.comp_instance.cpu}"

        return part_1 + self._writePhases()


class PortWriter:
    """
    Writer for an fpp port. Has write() function to write the port definition out.
    """

    def __init__(self, port: NodeStructs.Port):
        self.port: NodeStructs.Port = port

    def write(self):
        portParams = ""

        for i in self.port.parameters:
            portParams = portParams + f"{i['name']} : {i['type']},\n"

        return f"port {self.port.name}(\n    {portParams}\n)"


class TopologyImportWriter:
    """
    Writer for an fpp topology import. Has write() function to write the import out.
    """

    def __init__(self, topology_import: NodeStructs.TopologyImport):
        self.topology_import: NodeStructs.TopologyImport = topology_import

    def write(self):
        return f"import {self.topology_import.name}"


class ConnectionGraphWriter:
    """
    Writer for an fpp connection graph. Has write() function to write the connection graph out.
    """

    def __init__(self, connection_graph: NodeStructs.ConnectionGraph):
        self.connection_graph: NodeStructs.ConnectionGraph = connection_graph

    def write(self):
        part = f"connections {self.connection_graph.name} {{"

        for connection in self.connection_graph.connections:
            if (
                connection["source"]["num"] is None
                or connection["source"]["num"] == "None"
            ):
                connection["source"]["num"] = ""

            if connection["dest"]["num"] is None or connection["dest"]["num"] == "None":
                connection["dest"]["num"] = ""

            part = (
                part
                + f"\n    {connection['source']['name']}{connection['source']['num']} -> {connection['dest']['name']}{connection['dest']['num']}"
            )

        return part + "\n}"
