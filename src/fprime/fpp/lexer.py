"""fprime.fpp.lexer: Pygments lexer for FPP (F Prime Prime) files

Registered as a pygments plugin via the "pygments.lexers" entry point in pyproject.toml. This
enables tools built on pygments (e.g. pygount used by 'fprime-util sloc') to recognize .fpp and
.fppi files.

The lexer is intentionally minimal: it distinguishes comments, annotations, strings, and
everything else. That is all line counting needs, and it avoids maintaining a copy of the FPP
keyword list (which lives in fpp-tools) here.

Keep this module import-light (pygments only): every Pygments consumer on the host (pytest, rich,
sphinx, ...) imports it when enumerating lexer plugins through the entry point.

@author lestarch
"""

from pygments.lexer import RegexLexer
from pygments.token import Comment, String, Text, Whitespace


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
            (r'[^\s#@"]+', Text),
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
