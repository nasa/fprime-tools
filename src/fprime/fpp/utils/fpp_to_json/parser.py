import os
from pathlib import Path
import shutil
import json
import fprime.fpp.utils.fpp_to_json.fpp_interface as fpp

"""
===================== BASE CLASSES =====================
"""


class QualifyingElements:
    """
    Base class for all AST parser classes that represent a qualifying element in the AST.
    This means both modules and topologies.

    open() and close() are abstract methods that must be implemented by the child class.
    They open the element and close the element, respectively. For example, for a module,

    open() should return "module <module_name> {"
    close() should return "}"
    """

    def __init__(self):
        pass

    def parse(self):
        pass

    def open(self):
        pass

    def close(self):
        pass

    def members(self):
        pass


class ValueElements:
    """
    Base class for all AST parser classes that represent a value-holding element
    in the AST. This means constants, instance specifications, instances, ports, and
    connection graphs.

    write() is an abstract method that must be implemented by the child class. It
    should return the string representation of the element. For example, for a constant,

    write() should return "constant <constant_name> = <constant_value>"
    """

    def __init__(self):
        pass

    def parse(self):
        pass

    def write(self):
        pass


"""
===================== ACTUAL AST PARSER CLASSES =====================
"""


class ModuleParser(QualifyingElements):
    """
    Module data variables:
    - module_JSON: The JSON AST for the module
    - module_name: The name of the module
    - module_preannot: The pre-annotation for the module
    - module_postannot: The post-annotation for the module
    - qf: The qualified form of the module name

    AST Name: DefModule
    """

    def __init__(self, module_JSON_list):
        self.module_JSON = {}
        self.module_name = None
        self.module_preannot = None
        self.module_postannot = None
        self.qf = None

        self.module_preannot = module_JSON_list[0]
        self.module_JSON = module_JSON_list[1]
        self.module_postannot = module_JSON_list[2]

    def parse(self):
        self.module_name = self.module_JSON["DefModule"]["node"]["AstNode"]["data"][
            "name"
        ]
        self.qf = self.module_name

    def open(self):
        return f"module {self.module_name} {{"

    def close(self):
        return "}"

    def members(self):
        return self.module_JSON["DefModule"]["node"]["AstNode"]["data"]["members"]


class ConstantParser(ValueElements):
    """
    Constant data variables:
    - constant_JSON: The JSON AST for the constant
    - constant_Id: The ID (LHS) of the constant
    - constant_value: The value of the constant
    - constant_preannot: The pre-annotation for the constant
    - constant_postannot: The post-annotation for the constant
    - qf: The qualified form of the constant name

    AST Name: DefConstant
    """

    def __init__(self, constant_JSON_list):
        self.constant_JSON = {}
        self.constant_Id = None
        self.constant_value = None
        self.constant_preannot = None
        self.constant_postannot = None
        self.qf = None

        self.constant_preannot = constant_JSON_list[0]
        self.constant_JSON = constant_JSON_list[1]
        self.constant_postannot = constant_JSON_list[2]

    def parse(self):
        self.constant_Id = self.constant_JSON["DefConstant"]["node"]["AstNode"]["data"][
            "name"
        ]
        self.qf = self.constant_Id

        constant_Value_JSON = self.constant_JSON["DefConstant"]["node"]["AstNode"][
            "data"
        ]["value"]

        self.constant_value = parse_constant(constant_Value_JSON)

    def write(self):
        return f"constant {self.constant_Id} = {self.constant_value}"


class InstanceSpecParser(ValueElements):
    """
    Instance specification data variables:
    - instance_spec_JSON: The JSON AST for the instance specification
    - instance_spec_name: The name of the instance specification
    - instance_spec_type: The type of the instance specification
    - instance_spec_preannot: The pre-annotation for the instance specification
    - instance_spec_postannot: The post-annotation for the instance specification
    - qf: The qualified form of the instance specification name

    AST Name: SpecCompInstance
    """

    def __init__(self, instance_JSON_list):
        self.instance_JSON = {}
        self.instance_name = None
        self.instance_visibility = None
        self.instance_preannot = None
        self.instance_postannot = None
        self.qf = None

        self.instance_preannot = instance_JSON_list[0]
        self.instance_JSON = instance_JSON_list[1]
        self.instance_postannot = instance_JSON_list[2]

    def parse(self):
        instance_bit_1 = self.instance_JSON["SpecCompInstance"]["node"]["AstNode"][
            "data"
        ]["instance"]

        self.instance_name = value_parser(instance_bit_1)
        self.qf = self.instance_name

        if (
            "Public"
            in self.instance_JSON["SpecCompInstance"]["node"]["AstNode"]["data"][
                "visibility"
            ]
        ):
            self.instance_visibility = ""
        elif (
            "Private"
            in self.instance_JSON["SpecCompInstance"]["node"]["AstNode"]["data"][
                "visibility"
            ]
        ):
            self.instance_visibility = "private"

    def write(self):
        return f"{self.instance_visibility} instance {self.instance_name}"


class InstanceParser(ValueElements):
    """
    Instance data variables:
    - instance_JSON: The JSON AST for the instance
    - instance_name: The name of the instance
    - instance_elements: A dictionary containing the instance's elements
    - instance_preannot: The pre-annotation for the instance
    - instance_postannot: The post-annotation for the instance
    - qf: The qualified form of the instance name

    The instance_elements dictionary contains the following elements:
    - component_name: The name of the component
    - base_id: The base ID of the instance
    - queue: The queue size of the instance
    - stack: The stack size of the instance
    - priority: The priority of the instance
    - cpu: The CPU of the instance
    - phases: A dictionary containing the phases (FppToCpp) of the instance

    AST Name: DefComponentInstance
    """

    def __init__(self, instance_JSON_list):
        self.instance_JSON = {}
        self.instance_name = None
        self.instance_elements = {
            "component_name": None,
            "base_id": None,
            "queue": None,
            "stack": None,
            "priority": None,
            "cpu": None,
            "phases": {
                "configObjects": None,
                "configComponents": None,
                "readParameters": None,
                "configConstants": None,
                "tearDownComponents": None,
                "startTasks": None,
                "stopTasks": None,
                "freeThreads": None,
            },
        }
        self.instance_preannot = None
        self.instance_postannot = None
        self.qf = None

        self.instance_preannot = instance_JSON_list[0]
        self.instance_JSON = instance_JSON_list[1]
        self.instance_postannot = instance_JSON_list[2]

    def parse_phases(self):
        initSpecs = self.instance_JSON["DefComponentInstance"]["node"]["AstNode"][
            "data"
        ]["initSpecs"]

        for initSpec in initSpecs:
            if "phase" in initSpec[1]["AstNode"]["data"]:
                specType = initSpec[1]["AstNode"]["data"]["phase"]["AstNode"]["data"][
                    "ExprDot"
                ]["id"]["AstNode"]["data"]
                specCode = initSpec[1]["AstNode"]["data"]["code"]

                try:
                    self.instance_elements["phases"][specType] = specCode
                except KeyError:
                    print(
                        "[WARN] Phase type not found in instance JSON [InstanceParser.parse_phases]"
                    )

    def parse(self):
        self.instance_name = self.instance_JSON["DefComponentInstance"]["node"][
            "AstNode"
        ]["data"]["name"]
        self.qf = self.instance_name

        components_bit_1 = self.instance_JSON["DefComponentInstance"]["node"][
            "AstNode"
        ]["data"]["component"]

        self.instance_elements["component_name"] = value_parser(components_bit_1)
        self.instance_elements["base_id"] = value_parser(
            self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"][
                "baseId"
            ]
        )

        if (
            "queueSize"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_elements["queue"] = self.instance_JSON[
                "DefComponentInstance"
            ]["node"]["AstNode"]["data"]["queueSize"]
        if (
            "stackSize"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_elements["stack"] = self.instance_JSON[
                "DefComponentInstance"
            ]["node"]["AstNode"]["data"]["stackSize"]
        if (
            "priority"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_elements["priority"] = self.instance_JSON[
                "DefComponentInstance"
            ]["node"]["AstNode"]["data"]["priority"]

        if (
            self.instance_elements["queue"] is not None
            and self.instance_elements["queue"] != "None"
        ):
            queueSize_JSON = self.instance_elements["queue"]["Some"]["AstNode"]["data"]

            if "ExprLiteralInt" in queueSize_JSON:
                self.instance_elements["queue"] = queueSize_JSON["ExprLiteralInt"][
                    "value"
                ]
            elif "ExprIdent" in queueSize_JSON:
                self.instance_elements["queue"] = queueSize_JSON["ExprIdent"]["value"]
            elif "ExprDot" in queueSize_JSON:
                self.instance_elements["queue"] = qualifier_calculator(
                    queueSize_JSON["ExprDot"]
                )

        if (
            self.instance_elements["stack"] is not None
            and self.instance_elements["stack"] != "None"
        ):
            stackSize_JSON = self.instance_elements["stack"]["Some"]["AstNode"]["data"]

            if "ExprLiteralInt" in stackSize_JSON:
                self.instance_elements["stack"] = stackSize_JSON["ExprLiteralInt"][
                    "value"
                ]
            elif "ExprIdent" in stackSize_JSON:
                self.instance_elements["stack"] = stackSize_JSON["ExprIdent"]["value"]
            elif "ExprDot" in stackSize_JSON:
                self.instance_elements["stack"] = qualifier_calculator(
                    stackSize_JSON["ExprDot"]
                )

        if (
            self.instance_elements["priority"] is not None
            and self.instance_elements["priority"] != "None"
        ):
            priority_JSON = self.instance_elements["priority"]["Some"]["AstNode"][
                "data"
            ]

            if "ExprLiteralInt" in priority_JSON:
                self.instance_elements["priority"] = priority_JSON["ExprLiteralInt"][
                    "value"
                ]
            elif "ExprIdent" in priority_JSON:
                self.instance_elements["priority"] = priority_JSON["ExprIdent"]["value"]
            elif "ExprDot" in priority_JSON:
                self.instance_elements["priority"] = qualifier_calculator(
                    priority_JSON["ExprDot"]
                )

        if (
            "cpu"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_elements["cpu"] = self.instance_JSON["DefComponentInstance"][
                "node"
            ]["AstNode"]["data"]["cpu"]

            if (
                self.instance_elements["cpu"] is not None
                and self.instance_elements["cpu"] != "None"
            ):
                cpu_JSON = self.instance_elements["cpu"]["Some"]["AstNode"]["data"]

                if "ExprLiteralInt" in cpu_JSON:
                    self.instance_elements["cpu"] = cpu_JSON["ExprLiteralInt"]["value"]
                elif "ExprIdent" in cpu_JSON:
                    self.instance_elements["cpu"] = cpu_JSON["ExprIdent"]["value"]
                elif "ExprDot" in cpu_JSON:
                    self.instance_elements["cpu"] = qualifier_calculator(
                        cpu_JSON["ExprDot"]
                    )

        self.parse_phases()

    def writePhases(self):
        phaseOpen = False
        part = ""

        for phase in self.instance_elements["phases"]:
            if (
                self.instance_elements["phases"][phase] is not None
                and self.instance_elements["phases"][phase] != ""
            ):
                if not phaseOpen:
                    part += f"{{"
                    phaseOpen = True

                part += f'\n    phase Fpp.ToCpp.Phases.{phase} """\n'
                part += self.instance_elements["phases"][phase]
                part += '"""'

        if phaseOpen:
            part += "}"

        return part

    def write(self):
        part_1 = f"instance {self.instance_name}: {self.instance_elements['component_name']} base id {self.instance_elements['base_id']}"

        if (
            self.instance_elements["queue"] is not None
            and self.instance_elements["queue"] != "None"
        ):
            part_1 = part_1 + f" \\ \n    queue size {self.instance_elements['queue']}"

        if (
            self.instance_elements["stack"] is not None
            and self.instance_elements["stack"] != "None"
        ):
            part_1 = part_1 + f" \\ \n    stack size {self.instance_elements['stack']}"

        if (
            self.instance_elements["priority"] is not None
            and self.instance_elements["priority"] != "None"
        ):
            part_1 = part_1 + f" \\ \n    priority {self.instance_elements['priority']}"

        return part_1 + self.writePhases()


class PortParser(ValueElements):
    """
    Port data variables:
    - port_JSON: The JSON AST for the port
    - port_name: The name of the port
    - port_type: The type of the port
    - port_preannot: The pre-annotation for the port
    - port_postannot: The post-annotation for the port
    - port_params: A list of dictionaries containing the port's parameters
    - qf: The qualified form of the port name

    AST Name: DefPort
    """

    def __init__(self, port_JSON_list):
        self.port_JSON = {}
        self.port_name = None
        self.port_type = None
        self.port_preannot = None
        self.port_postannot = None
        self.port_params = []
        self.qf = None

        self.port_preannot = port_JSON_list[0]
        self.port_JSON = port_JSON_list[1]
        self.port_postannot = port_JSON_list[2]

    def parse(self):
        self.port_name = self.port_JSON["DefPort"]["node"]["AstNode"]["data"]["name"]
        self.qf = self.port_name

        for i in self.port_JSON["DefPort"]["node"]["AstNode"]["data"]["params"]:
            param = self.port_JSON["DefPort"]["node"]["AstNode"]["data"]["params"][i][1]
            paramToAppend = {
                "name": None,
                "type": None,
            }

            paramToAppend["name"] = param["AstNode"]["data"]["name"]
            paramToAppend["type"] = param["AstNode"]["data"]["typeName"]

            paramToAppend["type"] = value_parser(paramToAppend["type"])

    def write(self):
        portParams = ""

        for i in self.port_params:
            portParams = portParams + f"{i['name']} : {i['type']},\n"

        return f"port {self.port_name}(\n    {portParams}\n)"


class TopologyImport(ValueElements):
    """
    Import data variables:
    - import_JSON: The JSON AST for the import
    - import_name: The name of the import
    - import_preannot: The pre-annotation for the import
    - import_postannot: The post-annotation for the import
    - qf: The qualified form of the

    AST Name: SpecTopImport
    """

    def __init__(self, import_JSON_list):
        self.import_JSON = {}
        self.import_name = None
        self.import_preannot = None
        self.import_postannot = None
        self.qf = None

        self.import_preannot = import_JSON_list[0]
        self.import_JSON = import_JSON_list[1]
        self.import_postannot = import_JSON_list[2]

    def parse(self):
        import_bit_1 = self.import_JSON["SpecTopImport"]["node"]["AstNode"]["data"][
            "top"
        ]

        self.import_name = value_parser(import_bit_1)
        self.qf = self.import_name

    def write(self):
        return f"import {self.import_name}\n"


class ConnectionGraphParser(ValueElements):
    """
    Connection graph data variables:
    - cg_JSON: The JSON AST for the connection graph
    - cg_name: The name of the connection graph
    - cg_preannot: The pre-annotation for the connection graph
    - cg_postannot: The post-annotation for the connection graph
    - qf: The qualified form of the connection graph name
    - cg_connections: A list of dictionaries containing the connection graph's connections
    - cg_type: The type of the connection graph (pattern or direct)

    AST Name: SpecConnectionGraph
    """

    def __init__(self, cg_JSON_list):
        self.cg_JSON = {}
        self.cg_name = None
        self.cg_preannot = None
        self.cg_postannot = None
        self.qf = None
        self.cg_connections = []
        self.cg_type = None

        self.cg_preannot = cg_JSON_list[0]
        self.cg_JSON = cg_JSON_list[1]
        self.cg_postannot = cg_JSON_list[2]

    def write(self):
        part = f"connections {self.cg_name} {{"

        for connection in self.cg_connections:
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

    def parse(self):
        import_bit = self.cg_JSON["SpecConnectionGraph"]["node"]["AstNode"]["data"]

        if "Direct" not in import_bit:
            self.cg_type = "Pattern"
            return
        else:
            self.cg_type = "Direct"
            import_bit = import_bit["Direct"]

        self.cg_name = import_bit["name"]
        self.qf = self.cg_name

        for connection in import_bit["connections"]:
            connectionToAppend = {
                "source": {
                    "name": None,
                    "num": None,
                },
                "dest": {
                    "name": None,
                    "num": None,
                },
            }

            fromPort = connection["fromPort"]["AstNode"]["data"]
            compInst = fromPort["componentInstance"]

            connectionToAppend["source"]["name"] = (
                value_parser(compInst) + "." + fromPort["portName"]["AstNode"]["data"]
            )

            if connectionToAppend["source"]["name"][-4:] == "None":
                connectionToAppend["source"]["name"] = connectionToAppend["source"][
                    "name"
                ].replace("None", "")

            if connection["fromIndex"] != "None":
                if connection["fromIndex"] is None or connection["fromIndex"] == "None":
                    connectionToAppend["source"]["num"] = ""
                if type(connection["fromIndex"]) is dict:
                    connectionToAppend["source"]["num"] = (
                        "[" + value_parser(connection["fromIndex"]["Some"]) + "]"
                    )
                else:
                    connectionToAppend["source"]["num"] = (
                        "[" + connection["fromIndex"] + "]"
                    )

            toPort = connection["toPort"]["AstNode"]["data"]
            compInst = toPort["componentInstance"]

            connectionToAppend["dest"]["name"] = (
                value_parser(compInst) + "." + toPort["portName"]["AstNode"]["data"]
            )

            if connectionToAppend["dest"]["name"][-4:] == "None":
                connectionToAppend["dest"]["name"] = connectionToAppend["dest"][
                    "name"
                ].replace("None", "")

            if connection["toIndex"] != "None":
                if connection["toIndex"] is None or connection["toIndex"] == "None":
                    connectionToAppend["dest"]["num"] = ""
                if type(connection["toIndex"]) is dict:
                    connectionToAppend["dest"]["num"] = (
                        "[" + value_parser(connection["toIndex"]["Some"]) + "]"
                    )
                else:
                    connectionToAppend["dest"]["num"] = (
                        "[" + connection["toIndex"] + "]"
                    )

            self.cg_connections.append(connectionToAppend)


class TopologyParser(QualifyingElements):
    """
    Topology data variables:
    - topology_JSON: The JSON AST for the topology
    - topology_name: The name of the topology
    - topology_preannot: The pre-annotation for the topology
    - topology_postannot: The post-annotation for the topology
    - qf: The qualified form of the topology name

    AST Name: DefTopology
    """

    def __init__(self, topology_JSON_list):
        self.topology_JSON = {}
        self.topology_name = None
        self.topology_preannot = None
        self.topology_postannot = None
        self.qf = None

        self.topology_preannot = topology_JSON_list[0]
        self.topology_JSON = topology_JSON_list[1]
        self.topology_postannot = topology_JSON_list[2]

    def parse(self):
        self.topology_name = self.topology_JSON["DefTopology"]["node"]["AstNode"][
            "data"
        ]["name"]
        self.qf = self.topology_name

    def open(self):
        return f"topology {self.topology_name} {{"

    def close(self):
        return "}"

    def members(self):
        return self.topology_JSON["DefTopology"]["node"]["AstNode"]["data"]["members"]


"""
===================== UTILITY FUNCTIONS =====================
"""


def qualifier_calculator(qualifier_JSON):
    """
    Calculate the qualified name for a variable, instance, etc

    Args:
        qualifier_JSON: The JSON AST for the qualifier
    """
    next_idx = qualifier_JSON["e"]["AstNode"]["data"]

    path = ""

    if "ExprDot" in next_idx:
        path += qualifier_calculator(next_idx["ExprDot"])
    elif "ExprIdent" in next_idx:
        path += next_idx["ExprIdent"]["value"]

    return path + "." + qualifier_JSON["id"]["AstNode"]["data"]


def value_parser(value_JSON):
    """
    Parse a value from the JSON AST. This could be parsing integers, strings, arrays, etc.

    Args:
        value_JSON: The JSON AST for the value
    """
    checker = value_JSON["AstNode"]["data"]

    if "Unqualified" in checker:
        return checker["Unqualified"]["name"]
    elif "Qualified" in checker:
        qf = (
            checker["Qualified"]["qualifier"]["AstNode"]["data"]["Unqualified"]["name"]
            + "."
            + checker["Qualified"]["name"]["AstNode"]["data"]
        )
        return qf
    elif "ExprIdent" in checker:
        return checker["ExprIdent"]["value"]
    elif "ExprDot" in checker:
        return qualifier_calculator(checker["ExprDot"])
    else:
        return parse_constant(value_JSON)


def Binops(binop):
    """
    Convert binop string name to actual operator

    Args:
        binop: The binop string name
    """
    if binop == "Add":
        return "+"
    elif binop == "Sub":
        return "-"
    elif binop == "Mul":
        return "*"
    elif binop == "Div":
        return "/"

    raise Exception("Invalid binop")


def parse_binop(constant_JSON):
    """
    Parse a binary operation from the JSON AST

    Args:
        constant_JSON: The JSON AST for the binary operation
    """
    idx_LHS = 1
    idx_RHS = 2
    binop = ""

    constant_JSON = constant_JSON["ExprBinop"]
    binop_LHS = constant_JSON[f"e{idx_LHS}"]["AstNode"]["data"]

    if "ExprBinop" in binop_LHS:
        binop += parse_binop(binop_LHS)
    else:
        binop += value_parser(constant_JSON[f"e{idx_LHS}"])

    return (
        binop
        + " "
        + Binops(list(constant_JSON["op"].keys())[0])
        + " "
        + value_parser(constant_JSON[f"e{idx_RHS}"])
    )


def parse_constant(constant_JSON):
    """
    Parse a constant from the JSON AST

    Args:
        constant_JSON: The JSON AST for the constant
    """
    constant_Value_JSON = constant_JSON["AstNode"]["data"]

    if "ExprLiteralString" in constant_Value_JSON:
        return '"' + constant_Value_JSON["ExprLiteralString"]["value"] + '"'
    elif "ExprLiteralInt" in constant_Value_JSON:
        return constant_Value_JSON["ExprLiteralInt"]["value"]
    elif "ExprLiteralFloat" in constant_Value_JSON:
        return constant_Value_JSON["ExprLiteralFloat"]["value"]
    elif "ExprLiteralBool" in constant_Value_JSON:
        return list(constant_Value_JSON["ExprLiteralBool"]["value"].keys())[0]
    elif "ExprIdent" in constant_Value_JSON:
        return constant_Value_JSON["ExprIdent"]["value"]
    elif "ExprArray" in constant_Value_JSON:
        return parse_array(constant_Value_JSON)
    elif "ExprStruct" in constant_Value_JSON:
        return parse_struct(constant_Value_JSON)
    elif "ExprDot" in constant_Value_JSON:
        return qualifier_calculator(constant_Value_JSON["ExprDot"])
    elif "ExprBinop" in constant_Value_JSON:
        return parse_binop(constant_Value_JSON)
    else:
        raise Exception("Invalid constant type")


def parse_array(constant_JSON):
    """
    Parse an array from the JSON AST

    Args:
        constant_JSON: The JSON AST for the array
    """
    arrayOpen = "["
    constant_Value_JSON = constant_JSON["ExprArray"]["elts"]

    for i in range(len(constant_Value_JSON)):
        if "ExprArray" not in constant_Value_JSON[i]["AstNode"]["data"]:
            arrayOpen = arrayOpen + parse_constant(constant_Value_JSON[i])
            if i is not len(constant_Value_JSON) - 1:
                arrayOpen = arrayOpen + ", "
        else:
            arrayOpen = (
                arrayOpen
                + parse_array(constant_Value_JSON[i]["AstNode"]["data"])
                + ", "
            )

    return arrayOpen + "]"


def parse_struct(constant_JSON):
    """
    Parse a struct from the JSON AST

    Args:
        constant_JSON: The JSON AST for the struct
    """
    structOpen = "{\n"

    for param in constant_JSON["ExprStruct"]["members"]:
        structOpen = (
            structOpen
            + "    "
            + param["AstNode"]["data"]["name"]
            + " = "
            + value_parser(param["AstNode"]["data"]["value"])
            + ",\n"
        )

    return structOpen + "}"


def module_walker(AST, qf, type, type_parser):
    """
    This function walks through the JSON AST of a module and returns the AST for a
    specific element type with the qualified name qf.

    Args:
        AST: The JSON AST of the module
        qf: The qualified name of the element to find (i.e. module.member.member)
        type: The type of element to find (i.e. DefTopology, DefComponentInstance)
        type_parser: The parser for the element type (i.e. Parser.TopologyParser)

    Returns:
        The AST for the element with the qualified name qf
    """

    qf = qf.split(".")
    for m in AST:
        if "DefModule" in m[1]:
            module = ModuleParser(m)
            module.parse()

            if module.module_name == qf[0] and len(qf) > 1:
                for _m in module.members():
                    if "DefModule" in _m[1]:
                        moduleDeeper = ModuleParser(_m)
                        moduleDeeper.parse()

                        if moduleDeeper.module_name == qf[1] and len(qf) > 2:
                            return module_walker(
                                moduleDeeper.members(),
                                ".".join(qf[1:]),
                                type,
                                type_parser,
                            )
                    if type in _m[1]:
                        _type = type_parser(_m)
                        _type.parse()

                        if _type.qf == qf[1]:
                            return _type
            elif module.module_name == qf[0] and len(qf) == 1:
                return m

    raise Exception("Element not found")


def openFppFile(path):
    if not os.path.isabs(path):
        path = str(Path(path).resolve())

    pathDir = os.path.dirname(path)
    fileBasename = os.path.basename(path)
    folderName = f"/{fileBasename.split('.')[0]}Cache"

    pathToFolder = pathDir + folderName

    if not os.path.exists(pathToFolder):
        try:
            os.mkdir(pathToFolder)
        except OSError as e:
            raise Exception("Creation of the directory %s failed" % (pathToFolder))

    os.chdir(pathToFolder)

    if not os.path.exists("fpp-ast.json"):
        fpp.fpp_to_json(path)

    # parse json
    with open("fpp-ast.json", "r") as f:
        AST = json.load(f)

    os.chdir(pathDir)

    shutil.rmtree(pathToFolder, ignore_errors=True)

    return AST
