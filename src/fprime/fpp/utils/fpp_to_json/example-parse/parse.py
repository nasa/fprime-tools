import fprime.fpp.utils.fpp_to_json.fpp_interface as fpp
import fprime.fpp.utils.fpp_to_json.parser as Parser
from pathlib import Path

def walkModule(data, oldQf):
    module = Parser.ModuleParser(data)
    module.parse()

    if oldQf == "":
        qf = module.module_name
    else:
        qf = oldQf + "." + module.module_name  # qualifier

    module.qf = qf

    for member in module.members():
        if "DefComponentInstance" in member[1]:
            instance = Parser.InstanceParser(member)
            instance.parse()
            instance.qf = qf + "." + instance.instance_name
            
        if "DefConstant" in member[1]:
            constant = Parser.ConstantParser(member)
            constant.parse()
            constant.qf = qf + "." + constant.constant_Id
            
        # can be continued for other member types
            
        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf


def walkTopology(data, module):
    topology = Parser.TopologyParser(data)
    topology.parse()

    if module == "":
        qf = topology.topology_name
    else:
        qf = module + "." + topology.topology_name  # qualifier

    topology.qf = qf

    for member in topology.members():
        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf

def parse():
    AST = Parser.openFppFile(Path(__file__).parent / "example.fpp")
    
    for i in range(len(AST[0]["members"])):
        if "DefModule" in AST[0]["members"][i][1]:
            walkModule(AST[0]["members"][i], "")

        if "DefTopology" in AST[0]["members"][i][1]:
            walkTopology(AST[0]["members"][i], "")

if __name__ == "__main__":
    parse()