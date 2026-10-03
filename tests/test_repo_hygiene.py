"""Repository rules that are cheap to break and expensive to find.

On Windows, Python still defaults to cp1252 (README, "Working in the repo"),
and our data is bilingual. A text file opened without an explicit encoding
reads fine on Linux and corrupts the Chinese fields on a teammate's machine,
so the rule is checked here rather than trusted.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OPENERS = {"open", "read_text", "write_text"}


def _mode(call: ast.Call) -> str:
    """The mode string the call was given, or "" when it named none."""
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return kw.value.value if isinstance(kw.value.value, str) else ""
    # Builtin/module open(path, mode) and Path.open(mode) differ.
    func = call.func
    module_open = (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                   and func.value.id in {"gzip", "bz2", "lzma", "io", "builtins"})
    index = 0 if isinstance(func, ast.Attribute) and not module_open else 1
    if len(call.args) > index and isinstance(call.args[index], ast.Constant):
        return call.args[index].value if isinstance(call.args[index].value, str) else ""
    return ""


def test_binary_mode_detection_for_builtin_and_path_open():
    for expression in ('open("file", "rb")', 'path.open("rb")',
                       'path.open(mode="rb")', 'open("file", mode="rb")',
                       'gzip.open("file", "rb")', 'io.open("file", "rb")'):
        assert _mode(ast.parse(expression, mode="eval").body) == "rb"
    for expression in ('open("file")', 'path.open()', 'path.read_text()',
                       'gzip.open("file")'):
        assert _mode(ast.parse(expression, mode="eval").body) == ""


def test_every_text_open_in_src_sets_an_encoding():
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name not in OPENERS:
                continue
            if "b" in _mode(node):  # binary: encoding= would raise
                continue
            if not any(kw.arg == "encoding" for kw in node.keywords):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} {name}()")
    assert not offenders, (
        "text opened without encoding=; on Windows this reads as cp1252 and "
        "corrupts the Chinese fields:\n  " + "\n  ".join(offenders)
    )
