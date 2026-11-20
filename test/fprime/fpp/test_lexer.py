"""test_lexer.py: tests for the FPP pygments lexer plugin"""

import subprocess
import sys

from pygments.lexers import get_lexer_for_filename
from pygments.token import Comment, String, Text

from fprime.fpp.lexer import FppLexer

FPP_SOURCE = """# A comment
@ An annotation
module M {
  constant s = "quoted # not a comment"
  constant t = \"\"\"
    # not a comment either
  \"\"\"
  enum E { A @< post annotation
  }
}
"""


def test_lexer_registered():
    """The plugin entry point makes pygments pick the FPP lexer for .fpp and .fppi files"""
    assert isinstance(get_lexer_for_filename("Model.fpp"), FppLexer)
    assert isinstance(get_lexer_for_filename("Model.fppi"), FppLexer)


def test_lexer_tokens():
    """Comments, annotations, and strings are distinguished from code"""
    tokens = [
        (token, value)
        for token, value in FppLexer().get_tokens(FPP_SOURCE)
        if value.strip()
    ]
    comments = [value for token, value in tokens if token in Comment]
    assert comments == ["# A comment", "@ An annotation", "@< post annotation"]
    strings = "".join(value for token, value in tokens if token in String)
    assert "quoted # not a comment" in strings
    assert "# not a comment either" in strings
    code = [value for token, value in tokens if token in Text]
    assert "module" in code and "constant" in code and "#" not in "".join(code)


def test_lexer_import_is_light():
    """The plugin module is loaded by every Pygments consumer, so it must import only pygments"""
    code = (
        "import sys, fprime.fpp.lexer; "
        "print(sorted(m for m in sys.modules if m.startswith(('fprime', 'pygount', 'git'))))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "['fprime', 'fprime.fpp', 'fprime.fpp.lexer']"
