from pathlib import Path
from fprime.fpp.utils.fpp_to_json.helpers import openFppFile
import fprime.fpp.utils.fpp_to_json.visitors.json_conversion as JSONConverter
import fprime.fpp.utils.fpp_to_json.node_structs as NodeStructs


def walkModule(data, oldQf):
    module = NodeStructs.Module(data)
    module: NodeStructs.Module = JSONConverter.ModuleConverter(module).convert()

    if oldQf == "":
        qf = module.name
    else:
        qf = oldQf + "." + module.name  # qualifier

    module.qf = qf

    for member in module.members:
        if "DefComponentInstance" in member[1]:
            instance = NodeStructs.ComponentInst(member)
            instance: NodeStructs.ComponentInst = JSONConverter.CompInstanceConverter(
                instance
            ).convert()
            instance.qf = qf + "." + instance.name

        if "DefConstant" in member[1]:
            constant = NodeStructs.Constant(member)
            constant: NodeStructs.Constant = JSONConverter.ConstantConverter(
                constant
            ).convert()
            constant.qf = qf + "." + constant.id

        # can be continued for other member types

        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf


def walkTopology(data, module):
    topology = NodeStructs.Topology(data)
    topology: NodeStructs.Topology = JSONConverter.TopologyConverter(topology).convert()

    if module == "":
        qf = topology.name
    else:
        qf = module + "." + topology.name  # qualifier

    topology.qf = qf

    for member in topology.members:
        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf


def visit():
    AST = openFppFile(Path(__file__).parent / "example.fpp")

    for i in range(len(AST[0]["members"])):
        if "DefModule" in AST[0]["members"][i][1]:
            walkModule(AST[0]["members"][i], "")

        if "DefTopology" in AST[0]["members"][i][1]:
            walkTopology(AST[0]["members"][i], "")


if __name__ == "__main__":
    visit()
