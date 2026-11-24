#!/usr/bin/env python3
"""Static import check for pipeline scripts, including the ones only Blender runs.

    python3 tools/art/anim3d/kit/check_imports.py [folder ...]   # default: tools/art/anim3d

`blender --python script.py` does NOT put the script's own folder on sys.path
(plain `python script.py` does). A script that imports a sibling module without
inserting its folder passes every sandbox test that never launches Blender on
that path, then fails on the host. Round 12's GPU pass died two minutes in on
`from continuity import prepare` for exactly this reason, after a refactor that
all 33 tests passed.

For every .py file this resolves each local import against: the folders the
file inserts into sys.path (the `Path(__file__).resolve().parent` and
`.parents[N]` forms, optionally `/ 'name'`), plus the file's own folder when it
does not import bpy. Imports inside functions count. Standard-library, Blender
and third-party modules are ignored. Exit status 1 lists what cannot resolve.
No Blender needed; run it in every lane and before every GPU handoff.
"""
import ast
import sys
from pathlib import Path

EXTERNAL = set(sys.stdlib_module_names) | {
    'bpy', 'bmesh', 'mathutils', 'bpy_extras', 'bl_ext', 'addon_utils', 'gpu', 'idprop',
    'numpy', 'PIL', 'rigify', 'mpfb'}


def _path_expression(node, file):
    """Evaluate Path(__file__)...parent / parents[N] / 'name' chains, else None."""
    if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'str' and node.args:
        return _path_expression(node.args[0], file)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _path_expression(node.left, file)
        if left is not None and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return left/node.right.value
        return None
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == 'parents':
        base = _path_expression(node.value.value, file)
        if base is not None and isinstance(node.slice, ast.Constant):
            return base.parents[node.slice.value]
        return None
    if isinstance(node, ast.Attribute) and node.attr == 'parent':
        base = _path_expression(node.value, file)
        return base.parent if base is not None else None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('resolve', 'absolute'):
        return _path_expression(node.func.value, file)
    if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'Path' and node.args:
        if isinstance(node.args[0], ast.Name) and node.args[0].id == '__file__':
            return file
    return None


def analyse(file):
    """Return (roots, imports, uses_bpy, entry) for one script.

    `entry`: the file sets up sys.path, has a __main__ guard or reads sys.argv,
    so it is launched directly and must resolve its imports by itself.
    """
    file = Path(file).resolve()
    source = file.read_text()
    tree = ast.parse(source, filename=str(file))
    roots, imports = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ('insert', 'append') \
                and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == 'path' \
                and getattr(node.func.value.value, 'id', None) == 'sys':
            root = _path_expression(node.args[-1], file)
            if root is not None:
                roots.append(root)
        elif isinstance(node, ast.Import):
            imports += [(alias.name, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.append((node.module, node.lineno))
    uses_bpy = any(name.split('.')[0] == 'bpy' for name, _ in imports)
    entry = bool(roots) or '__main__' in source or 'sys.argv' in source
    if not uses_bpy:
        roots.append(file.parent)
    return roots, imports, uses_bpy, entry


def _resolves(name, roots):
    parts = name.split('.')
    for root in roots:
        target = root.joinpath(*parts)
        if target.with_suffix('.py').is_file() or (target/'__init__.py').is_file() or target.is_dir():
            return True
    return False


def check(folders):
    """Entry scripts must resolve local imports from their own sys.path setup.
    Modules that are only imported by others are checked against every root
    any entry script in the scanned folders sets up.
    """
    files = [f for folder in folders for f in sorted(Path(folder).rglob('*.py')) if '__pycache__' not in f.parts]
    analysed = {f: analyse(f) for f in files}
    shared = [root for roots, _, _, entry in analysed.values() if entry for root in roots]
    problems = []
    for file, (roots, imports, uses_bpy, entry) in analysed.items():
        for name, line in imports:
            if name.split('.')[0] in EXTERNAL or _resolves(name, roots if entry else roots+shared):
                continue
            if entry and uses_bpy:
                how = 'Blender does not add the script folder to sys.path'
            elif entry:
                how = 'not found on the script path'
            else:
                how = 'no entry script puts it on sys.path'
            problems.append(f'{file}:{line}: cannot resolve import {name!r} ({how})')
    return problems


def main():
    folders = sys.argv[1:] or [Path(__file__).resolve().parents[1]]
    problems = check(folders)
    for problem in problems:
        print(problem)
    print(f'{len(problems)} unresolved local import(s)')
    raise SystemExit(bool(problems))


if __name__ == '__main__':
    main()
