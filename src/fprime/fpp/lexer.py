"""fprime.fpp.lexer: Pygments lexer for FPP (F Prime Prime) files

Registered as a pygments plugin via the "pygments.lexers" entry point in pyproject.toml. This
enables tools built on pygments (e.g. pygount used by 'fprime-util sloc') to recognize .fpp and
.fppi files.

@author lestarch
"""

from pygments.lexer import RegexLexer, words
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)

FPP_KEYWORDS = (
    "active",
    "activity",
    "always",
    "array",
    "assert",
    "async",
    "at",
    "base",
    "block",
    "change",
    "command",
    "component",
    "connections",
    "constant",
    "container",
    "cpu",
    "default",
    "diagnostic",
    "drop",
    "enum",
    "event",
    "external",
    "false",
    "fatal",
    "format",
    "get",
    "guarded",
    "health",
    "high",
    "hook",
    "id",
    "import",
    "include",
    "input",
    "instance",
    "interface",
    "internal",
    "locate",
    "low",
    "match",
    "module",
    "on",
    "opcode",
    "orange",
    "output",
    "packet",
    "packets",
    "param",
    "passive",
    "phase",
    "port",
    "priority",
    "private",
    "product",
    "queue",
    "queued",
    "record",
    "recv",
    "red",
    "ref",
    "reg",
    "resp",
    "save",
    "send",
    "serial",
    "set",
    "severity",
    "size",
    "stack",
    "state",
    "struct",
    "sync",
    "telemetry",
    "text",
    "throttle",
    "time",
    "topology",
    "true",
    "type",
    "unmatched",
    "update",
    "warning",
    "with",
    "yellow",
)

FPP_TYPES = (
    "bool",
    "F32",
    "F64",
    "I16",
    "I32",
    "I64",
    "I8",
    "string",
    "U16",
    "U32",
    "U64",
    "U8",
)


class FppLexer(RegexLexer):
    """Lexer for the F Prime Prime (FPP) modeling language"""

    name = "FPP"
    aliases = ["fpp"]
    filenames = ["*.fpp", "*.fppi"]
    mimetypes = ["text/x-fpp"]

    tokens = {
        "root": [
            (r"\s+", Whitespace),
            (r"#.*?$", Comment.Single),
            (r"@<?.*?$", Comment.Special),
            (r'"""', String, "triple-string"),
            (r'"', String, "string"),
            (r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?", Number.Float),
            (r"0[xX][0-9a-fA-F]+", Number.Hex),
            (r"[0-9]+", Number.Integer),
            (words(FPP_KEYWORDS, suffix=r"\b"), Keyword),
            (words(FPP_TYPES, suffix=r"\b"), Keyword.Type),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name),
            (r"[=\-+*/.:;,$]+", Operator),
            (r"[()\[\]{}]", Punctuation),
            (r"\\\n", Text),
            (r".", Text),
        ],
        "string": [
            (r"\\.", String.Escape),
            (r'"', String, "#pop"),
            (r'[^"\\]+', String),
        ],
        "triple-string": [
            (r'"""', String, "#pop"),
            (r'"', String),
            (r'[^"]+', String),
        ],
    }
