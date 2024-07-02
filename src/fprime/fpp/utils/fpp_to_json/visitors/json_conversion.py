import fprime.fpp.utils.fpp_to_json.node_structs as NodeStructs
import fprime.fpp.utils.fpp_to_json.helpers as Utils

class ModuleConverter:
    """
    AST Name: DefModule
    """

    def __init__(self, module: NodeStructs.Module):
        self.module_struct:NodeStructs.Module = module

        self.module_struct.preannot = module.ast[0]
        self.module_JSON = module.ast[1]
        self.module_struct.postannot = module.ast[2]

    def convert(self):
        self.module_struct.name = self.module_JSON["DefModule"]["node"]["AstNode"]["data"][
            "name"
        ]
        self.module_struct.qf = self.module_struct.name

        self.module_struct.members = self.module_JSON["DefModule"]["node"]["AstNode"]["data"]["members"]
        
        return self.module_struct
    
class ConstantConverter:
    """
    AST Name: DefConstant
    """

    def __init__(self, constant: NodeStructs.Constant):
        self.constant_struct:NodeStructs.Constant = constant

        self.constant_struct.preannot = constant.ast[0]
        self.constant_JSON = constant.ast[1]
        self.constant_struct.postannot = constant.ast[2]

    def convert(self):
        self.constant_struct.id = self.constant_JSON["DefConstant"]["node"]["AstNode"]["data"][
            "name"
        ]
        self.constant_struct.qf = self.constant_struct.id

        constant_Value_JSON = self.constant_JSON["DefConstant"]["node"]["AstNode"][
            "data"
        ]["value"]

        self.constant_struct.value = Utils.parse_constant(constant_Value_JSON)
        
        return self.constant_struct
        
class InstanceSpecConverter:
    """
    AST Name: SpecCompInstance
    """

    def __init__(self, instance: NodeStructs.InstanceSpec):
        self.instance_struct:NodeStructs.InstanceSpec = instance
        
        self.instance_struct.preannot = instance.ast[0]
        self.instance_JSON = instance.ast[1]
        self.instance_struct.postannot = instance.ast[2]

    def convert(self):
        instance_bit_1 = self.instance_JSON["SpecCompInstance"]["node"]["AstNode"][
            "data"
        ]["instance"]

        self.instance_struct.name = Utils.value_parser(instance_bit_1)
        self.instance_struct.qf = self.instance_struct.name

        if (
            "Public"
            in self.instance_JSON["SpecCompInstance"]["node"]["AstNode"]["data"][
                "visibility"
            ]
        ):
            self.instance_struct.visibility = ""
        elif (
            "Private"
            in self.instance_JSON["SpecCompInstance"]["node"]["AstNode"]["data"][
                "visibility"
            ]
        ):
            self.instance_struct.visibility = "private"
            
        return self.instance_struct
            
class CompInstanceConverter:
    """
    AST Name: DefComponentInstance
    """

    def __init__(self, instance: NodeStructs.ComponentInst):        
        self.instance_struct:NodeStructs.ComponentInst = instance

        self.instance_struct.preannot = instance.ast[0]
        self.instance_JSON = instance.ast[1]
        self.instance_struct.postannot = instance.ast[2]
            
    def convert(self):
        self._parse()
        self._parse_phases()
        
        return self.instance_struct

    def _parse_phases(self):
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
                    self.instance_struct.phases[specType] = specCode
                except KeyError:
                    print(
                        "[WARN] Phase type not found in instance JSON [InstanceParser.parse_phases]"
                    )

    def _parse(self):
        self.instance_struct.name = self.instance_JSON["DefComponentInstance"]["node"][
            "AstNode"
        ]["data"]["name"]
        self.instance_struct.qf = self.instance_struct.name

        components_bit_1 = self.instance_JSON["DefComponentInstance"]["node"][
            "AstNode"
        ]["data"]["component"]

        self.instance_struct.component_name = Utils.value_parser(components_bit_1)
        self.instance_struct.base_id = Utils.value_parser(
            self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"][
                "baseId"
            ]
        )

        if (
            "queueSize"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_struct.queue_size = self.instance_JSON[
                "DefComponentInstance"
            ]["node"]["AstNode"]["data"]["queueSize"]
        if (
            "stackSize"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_struct.stack_size = self.instance_JSON[
                "DefComponentInstance"
            ]["node"]["AstNode"]["data"]["stackSize"]
        if (
            "priority"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_struct.priority = self.instance_JSON[
                "DefComponentInstance"
            ]["node"]["AstNode"]["data"]["priority"]

        if (
            self.instance_struct.queue_size is not None
            and self.instance_struct.queue_size != "None"
        ):
            queueSize_JSON = self.instance_struct.queue_size["Some"]["AstNode"]["data"]

            if "ExprLiteralInt" in queueSize_JSON:
                self.instance_struct.queue_size = queueSize_JSON["ExprLiteralInt"][
                    "value"
                ]
            elif "ExprIdent" in queueSize_JSON:
                self.instance_struct.queue_size = queueSize_JSON["ExprIdent"]["value"]
            elif "ExprDot" in queueSize_JSON:
                self.instance_struct.queue_size = Utils.qualifier_calculator(
                    queueSize_JSON["ExprDot"]
                )

        if (
            self.instance_struct.stack_size is not None
            and self.instance_struct.stack_size != "None"
        ):
            stackSize_JSON = self.instance_struct.stack_size["Some"]["AstNode"]["data"]

            if "ExprLiteralInt" in stackSize_JSON:
                self.instance_struct.stack_size = stackSize_JSON["ExprLiteralInt"][
                    "value"
                ]
            elif "ExprIdent" in stackSize_JSON:
                self.instance_struct.stack_size = stackSize_JSON["ExprIdent"]["value"]
            elif "ExprDot" in stackSize_JSON:
                self.instance_struct.stack_size = Utils.qualifier_calculator(
                    stackSize_JSON["ExprDot"]
                )

        if (
            self.instance_struct.priority is not None
            and self.instance_struct.priority != "None"
        ):
            priority_JSON = self.instance_struct.priority["Some"]["AstNode"][
                "data"
            ]

            if "ExprLiteralInt" in priority_JSON:
                self.instance_struct.priority = priority_JSON["ExprLiteralInt"][
                    "value"
                ]
            elif "ExprIdent" in priority_JSON:
                self.instance_struct.priority = priority_JSON["ExprIdent"]["value"]
            elif "ExprDot" in priority_JSON:
                self.instance_struct.priority = Utils.qualifier_calculator(
                    priority_JSON["ExprDot"]
                )

        if (
            "cpu"
            in self.instance_JSON["DefComponentInstance"]["node"]["AstNode"]["data"]
        ):
            self.instance_struct.cpu = self.instance_JSON["DefComponentInstance"][
                "node"
            ]["AstNode"]["data"]["cpu"]

            if (
                self.instance_struct.cpu is not None
                and self.instance_struct.cpu != "None"
            ):
                cpu_JSON = self.instance_struct.cpu["Some"]["AstNode"]["data"]

                if "ExprLiteralInt" in cpu_JSON:
                    self.instance_struct.cpu = cpu_JSON["ExprLiteralInt"]["value"]
                elif "ExprIdent" in cpu_JSON:
                    self.instance_struct.cpu = cpu_JSON["ExprIdent"]["value"]
                elif "ExprDot" in cpu_JSON:
                    self.instance_struct.cpu = Utils.qualifier_calculator(
                        cpu_JSON["ExprDot"]
                    )
                    
class PortConverter:
    """
    AST Name: DefPort
    """

    def __init__(self, port: NodeStructs.Port):        
        self.port_struct:NodeStructs.Port = port

        self.port_struct.preannot = port.ast[0]
        self.port_JSON = port.ast[1]
        self.port_struct.postannot = port.ast[2]

    def convert(self):
        self.port_struct.name = self.port_JSON["DefPort"]["node"]["AstNode"]["data"]["name"]
        self.port_struct.qf = self.port_name

        for i in self.port_JSON["DefPort"]["node"]["AstNode"]["data"]["params"]:
            param = self.port_JSON["DefPort"]["node"]["AstNode"]["data"]["params"][i][1]
            paramToAppend = {
                "name": None,
                "type": None,
            }

            paramToAppend["name"] = param["AstNode"]["data"]["name"]
            paramToAppend["type"] = param["AstNode"]["data"]["typeName"]
            paramToAppend["type"] = Utils.value_parser(paramToAppend["type"])
            
            self.port_struct.parameters.append(paramToAppend)
            
        return self.port_struct
            
class TopologyImportConverter:
    """
    AST Name: SpecTopImport
    """

    def __init__(self, import_struct: NodeStructs.TopologyImport):        
        self.import_struct = import_struct

        self.import_struct.preannot = import_struct.ast[0]
        self.import_JSON = import_struct.ast[1]
        self.import_struct.postannot = import_struct.ast[2]

    def convert(self):
        import_bit_1 = self.import_JSON["SpecTopImport"]["node"]["AstNode"]["data"][
            "top"
        ]

        self.import_struct.name = Utils.value_parser(import_bit_1)
        self.import_struct.qf = self.import_struct.name
        
        return self.import_struct
        
class ConnectionGraphConverter:
    """
    AST Name: SpecConnectionGraph
    """

    def __init__(self, cg: NodeStructs.ConnectionGraph):        
        self.cg_struct = cg

        self.cg_struct.preannot = cg.ast[0]
        self.cg_JSON = cg.ast[1]
        self.cg_struct.postannot = cg.ast[2]

    def convert(self):
        import_bit = self.cg_JSON["SpecConnectionGraph"]["node"]["AstNode"]["data"]

        if "Direct" not in import_bit:
            self.cg_struct.type = "Pattern"
            return
        else:
            self.cg_struct.type = "Direct"
            import_bit = import_bit["Direct"]

        self.cg_struct.name = import_bit["name"]
        self.cg_struct.qf = self.cg_struct.name

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
                Utils.value_parser(compInst) + "." + fromPort["portName"]["AstNode"]["data"]
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
                        "[" + Utils.value_parser(connection["fromIndex"]["Some"]) + "]"
                    )
                else:
                    connectionToAppend["source"]["num"] = (
                        "[" + connection["fromIndex"] + "]"
                    )

            toPort = connection["toPort"]["AstNode"]["data"]
            compInst = toPort["componentInstance"]

            connectionToAppend["dest"]["name"] = (
                Utils.value_parser(compInst) + "." + toPort["portName"]["AstNode"]["data"]
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
                        "[" + Utils.value_parser(connection["toIndex"]["Some"]) + "]"
                    )
                else:
                    connectionToAppend["dest"]["num"] = (
                        "[" + connection["toIndex"] + "]"
                    )

            self.cg_struct.connections.append(connectionToAppend)
        
        return self.cg_struct
            
class TopologyConverter:
    """
    AST Name: DefTopology
    """

    def __init__(self, topology: NodeStructs.Topology):
        self.topology_struct:NodeStructs.Topology = topology

        self.topology_struct.preannot = topology.ast[0]
        self.topology_JSON = topology.ast[1]
        self.topology_struct.postannot = topology.ast[2]

    def convert(self):
        self.topology_struct.name = self.topology_JSON["DefTopology"]["node"]["AstNode"][
            "data"
        ]["name"]
        self.topology_struct.qf = self.topology_struct.name

        self.topology_struct.members = self.topology_JSON["DefTopology"]["node"]["AstNode"]["data"]["members"]
        
        return self.topology_struct