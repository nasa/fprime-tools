import fprime.fpp.utils.fpp_to_json.writer as Writer

def write():
    # create a new fpp module
    module = Writer.FppModule("ExampleModule")
    print(module.open())

    # create a new fpp constant
    constant = Writer.FppConstant("ExampleConstant", "42")
    print(constant.write())
    
    # create a new fpp topology
    topology = Writer.FppTopology("ExampleTopology")
    print(topology.open())
    
    # create a new fpp instance spec
    instanceSpec = Writer.FppInstanceSpec("ExampleInstance")
    print(instanceSpec.write())

    # close the module and topology
    print(topology.close())
    print(module.close())

if __name__ == "__main__":
    write()