"""
This file defines the structures for the annotatable elements in the fpp AST. These 
are separate from the converters itself such that it may be possible to write 
converters from other languages to these Python data structures.

If extending this utility, the first step would be to add a new class for the data
structure for any new element. Then, a converter is required to turn an input AST into
these structures.
"""


class Module:
    """
    Attributes:
        ast: The AST of the module
        name: The name of the module
        members: The members of the module
        preannot: The preannotations of the module
        postannot: The postannotations of the module
        qf: The qualified name of the module
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None
        self.members = []

        self.preannot = None
        self.postannot = None
        self.qf = None


class Constant:
    """
    Attributes:
        ast: The AST of the constant
        id: The id (LHS) of the constant
        value: The value of the constant
        preannot: The preannotations of the constant
        postannot: The postannotations of the constant
        qf: The qualified name of the constant
    """

    def __init__(self, ast):
        self.ast = ast
        self.id = None
        self.value = None

        self.preannot = None
        self.postannot = None
        self.qf = None


class InstanceSpec:
    """
    Attributes:
        ast: The AST of the instance spec
        name: The name of the instance spec
        visibility: The visibility of the instance spec (private, normal)
        preannot: The preannotations of the instance spec
        postannot: The postannotations of the instance spec
        qf: The qualified name of the instance spec
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None
        self.visibility = None

        self.preannot = None
        self.postannot = None
        self.qf = None


class ComponentInst:
    """
    Attributes:
        ast: The AST of the component instance
        name: The name of the component instance
        component_name: The name of the component
        base_id: The base id of the component instance
        queue_size: The queue size of the component instance
        stack_size: The stack size of the component instance
        cpu: The cpu of the component instance
        priority: The priority of the component instance
        phases: The phases of the component instance
        preannot: The preannotations of the component instance
        postannot: The postannotations of the component instance
        qf: The qualified name of the component instance
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None
        self.component_name = None
        self.base_id = None
        self.queue_size = None
        self.stack_size = None
        self.cpu = None
        self.priority = None
        self.phases = {
            "configObjects": None,
            "configComponents": None,
            "readParameters": None,
            "configConstants": None,
            "tearDownComponents": None,
            "startTasks": None,
            "stopTasks": None,
            "freeThreads": None,
        }

        self.preannot = None
        self.postannot = None
        self.qf = None


class Port:
    """
    Attributes:
        ast: The AST of the port
        name: The name of the port
        type: The type of the port
        preannot: The preannotations of the port
        postannot: The postannotations of the port
        qf: The qualified name of the port
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None
        self.parameters = []

        self.preannot = None
        self.postannot = None
        self.qf = None


class TopologyImport:
    """
    Attributes:
        ast: The AST of the topology import
        name: The name of the topology import
        preannot: The preannotations of the topology import
        postannot: The postannotations of the topology import
        qf: The qualified name of the topology import
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None

        self.preannot = None
        self.postannot = None
        self.qf = None


class ConnectionGraph:
    """
    Attributes:
        ast: The AST of the connection graph
        name: The name of the connection graph
        connections: The connections of the connection graph
        type: The type of the connection graph
        preannot: The preannotations of the connection graph
        postannot: The postannotations of the connection graph
        qf: The qualified name of the connection graph
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None
        self.connections = []
        self.type = None

        self.preannot = None
        self.postannot = None
        self.qf = None


class Topology:
    """
    Attributes:
        ast: The AST of the topology
        name: The name of the topology
        members: The members of the topology
        preannot: The preannotations of the topology
        postannot: The postannotations of the topology
        qf: The qualified name of the topology
    """

    def __init__(self, ast):
        self.ast = ast
        self.name = None
        self.members = []

        self.preannot = None
        self.postannot = None
        self.qf = None
