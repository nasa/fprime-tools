import fprime.fpp.utils.fpp_to_json.visitors.writer as Writer
import fprime.fpp.utils.fpp_to_json.node_structs as NodeStructs


def write():
    # create a new fpp module
    module = NodeStructs.Module("ExampleModule")
    module.name = "ExampleModule"

    module = Writer.ModuleWriter(module)
    print(module.open())

    # create a new fpp constant
    constant = NodeStructs.Constant("ExampleConstant")
    constant.id = "ExampleConstant"
    constant.value = "42"

    constant = Writer.ConstantWriter(constant)
    print(constant.write())

    # create a new fpp topology
    topology = NodeStructs.Topology("ExampleTopology")
    topology.name = "ExampleTopology"

    topology = Writer.TopologyWriter(topology)
    print(topology.open())

    # create a new fpp instance spec
    instanceSpec = NodeStructs.InstanceSpec("ExampleInstance")
    instanceSpec.name = "ExampleInstance"

    instanceSpec = Writer.InstanceSpecWriter(instanceSpec)
    print(instanceSpec.write())

    # close the module and topology
    print(topology.close())
    print(module.close())


if __name__ == "__main__":
    write()
