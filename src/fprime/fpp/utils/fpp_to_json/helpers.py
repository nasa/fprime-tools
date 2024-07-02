import os
from pathlib import Path
import shutil
import json
import fprime.fpp.utils.fpp_to_json.fpp_interface as fpp
import fprime.fpp.utils.fpp_to_json.visitors.json_conversion as JSONConverter
import fprime.fpp.utils.fpp_to_json.node_structs as NodeStructs

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
            module = NodeStructs.Module(m)
            module: NodeStructs.Module = JSONConverter.ModuleConverter(module).convert()

            if module.name == qf[0] and len(qf) > 1:
                for _m in module.members():
                    if "DefModule" in _m[1]:
                        moduleDeeper = NodeStructs.Module(_m)
                        moduleDeeper: NodeStructs.Module = JSONConverter.ModuleConverter(
                            moduleDeeper
                        ).convert()

                        if moduleDeeper.name == qf[1] and len(qf) > 2:
                            return module_walker(
                                moduleDeeper.members,
                                ".".join(qf[1:]),
                                type,
                                type_parser,
                            )
                    if type in _m[1]:
                        _type = type_parser(_m)
                        _type.parse()

                        if _type.qf == qf[1]:
                            return _type
            elif module.name == qf[0] and len(qf) == 1:
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