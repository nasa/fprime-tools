import fprime.fpp.utils.fpp_to_json.fpp_interface as fpp

def writeFppFile(file, content):
    """
    This function writes content to a file and formats the file using fpp-format.

    Args:
        file: The file to write to (i.e. /path/to/file.fpp)
        content: The content to write to the file
    """

    with open(file, "w") as f:
        f.write(content)

    try:
        postFormat = fpp.fpp_format(file)

        # overwrite the file with the formatted version
        f = open(file, "w")
        f.write(postFormat)
        f.close()
    except:
        raise Exception("[ERR] fpp-format failed")

    return file

class FppModule:
    """
    Class to represent and write an fpp module.
    
    Args:
        module_name (str): The name of the module.
    """
    def __init__(self, module_name):
        self.module_name = ""
        self.module_name = module_name

    def open(self):
        return f"module {self.module_name} {{"

    def close(self):
        return "}"


class FppConstant:
    """
    Class to represent and write an fpp constant. Constants can be of any supported FPP
    type.
    
    Args:
        constant_name (str): The name of the constant.
        constant_value (str): The value of the constant
    """
    def __init__(self, constant_name, constant_value):
        self.constant_name = ""
        self.constant_value = ""

        self.constant_name = constant_name
        self.constant_value = constant_value

    def write(self):
        return f"constant {self.constant_name} = {self.constant_value}"

class FppTopology:
    """
    Class to represent and write an fpp topology.
    
    Args:
        topology_name (str): The name of the topology.
    """
    def __init__(self, topology_name):
        self.topology_name = ""

        self.topology_name = topology_name

    def open(self):
        return f"topology {self.topology_name} {{"

    def close(self):
        return "}"


class FppInstanceSpec:
    """
    Class to represent and write an fpp instance spec.
    
    Args:
        instance_spec_name (str): The name of the instance spec.
    """
    def __init__(self, instance_name):
        self.instance_name = instance_name

    def write(self):
        return f"instance {self.instance_name}"


class FppConnectionGraph:
    """
    Class to represent and write an fpp connection graph.
    
    Args:
        connection_graph_name (str): The name of the connection graph.
        
    Methods:
        make_connection_dict: Creates a connection dictionary in the proper structure
        open: Opens the connection graph.
        connect: Connects two instances in the connection graph given a connection input.
        connect_from_db: Connects all instances in the connection graph saved using save_connection.
        save_connection: Saves a connection to the connection graph.
        close: Closes the connection graph.
    """
    def __init__(self, connection_graph_name):
        self.connections = []
        self.connection_graph_name = connection_graph_name
        
    def make_connection_dict(self, source, sourcePort, dest, destPort):
        return {
            "source": {
                "name": source,
                "num": sourcePort
            },
            "dest": {
                "name": dest,
                "num": destPort
            }
        }

    def open(self):
        return f"connections {self.connection_graph_name} {{"

    def connect(self, connection):
        if connection["source"]["num"] is None or connection["source"]["num"] == "None":
            connection["source"]["num"] = ""

        if connection["dest"]["num"] is None or connection["dest"]["num"] == "None":
            connection["dest"]["num"] = ""

        return f"    {connection['source']['name']}{connection['source']['num']} -> {connection['dest']['name']}{connection['dest']['num']}"

    def connect_from_db(self):
        allConnections = ""
        for connection in self.connections:
            allConnections += self.connect(connection) + "\n"

        return allConnections

    def save_connection(self, connection):
        if connection["source"]["num"] == None or connection["source"]["num"] == "None":
            connection["source"]["num"] = ""

        if connection["dest"]["num"] == None or connection["dest"]["num"] == "None":
            connection["dest"]["num"] = ""

        self.connections.append(connection)

    def close(self):
        return "}"


class FppImport:
    """
    Class to represent and write an fpp import. Like: `import Topology`
    
    Args:
        import_name (str): The name of the import.
    """
    def __init__(self, import_name):
        self.import_name = import_name

    def write(self):
        return f"import {self.import_name}"
    
class FppInclude:
    def __init__(self, include_name, path):
        self.include_path = None
        self.include_name = include_name
        
        if path[0] != ".":
            raise ValueError("Path must be relative")
        
        self.include_path = path

    def write(self):
        return f"include {self.include_path}"


class FppInstance:
    """
    Class to represent and write an fpp component instance.
    
    Args:
        instance_name (str): The name of the instance.
        instance_details (dict): The details of the instance.
        
    instance_details structure:
    {
        "instanceOf": "",
        "base_id": "",
        "queueSize": "",
        "stackSize": "",
        "cpu": "",
        "priority": "",
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
    """
    def __init__(self, instance_name, instance_details):
        self.instance_name = ""
        self.instance_details = {
            "instanceOf": "",
            "base_id": "",
            "queueSize": "",
            "stackSize": "",
            "cpu": "",
            "priority": "",
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

        self.instance_name = instance_name
        self.instance_details = instance_details

    def writePhases(self):
        phaseOpen = False
        part = ""

        for phase in self.instance_details["phases"]:
            if (
                self.instance_details["phases"][phase] is not None
                and self.instance_details["phases"][phase] != ""
            ):
                if not phaseOpen:
                    part += f"{{"
                    phaseOpen = True

                part += f'\n    phase Fpp.ToCpp.Phases.{phase} """\n'
                part += self.instance_details["phases"][phase]
                part += '"""'

        if phaseOpen:
            part += "}"

        return part

    def write(self):
        part = f"instance {self.instance_name}: {self.instance_details['instanceOf']} base id {self.instance_details['base_id']}"

        if (
            self.instance_details["queueSize"]
            and self.instance_details["queueSize"] != ""
        ):
            part += f"\\ \n    queue size {self.instance_details['queueSize']}"

        if (
            self.instance_details["stackSize"]
            and self.instance_details["stackSize"] != ""
        ):
            part += f"\\ \n    stack size {self.instance_details['stackSize']}"

        if self.instance_details["cpu"] and self.instance_details["cpu"] != "":
            part += f"\\ \n    cpu {self.instance_details['cpu']}"

        if (
            self.instance_details["priority"]
            and self.instance_details["priority"] != ""
        ):
            part += f"\\ \n    priority {self.instance_details['priority']}"

        return part + self.writePhases()
