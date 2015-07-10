"""Forcibly fix .pth files made by setuptools
"""
import ast
import astcheck
import inspect
import os
import sys
from pathlib import Path

__version__ = "0.1"

### Danger zone
from setuptools.command import easy_install
###

def rewrite_pth(path: Path):
    is_infected = False
    contents = []
    with path.open('r') as f:
        for line in f:
            if line.startswith("import "):
                is_infected = True
            else:
                contents.append(line)

    if is_infected:
        print("Treating infected file:", path)

        with path.open('w') as f:
            f.writelines(contents)

def pth_doctor():
    for d in sys.path:
        d = Path(d)
        if not d.is_dir():
            pass

        for pth_file in d.glob('*.pth'):
            if pth_file.name.endswith('-nspkg.pth'):
                # Skip namespace package .pth files for now
                continue

            try:
                rewrite_pth(pth_file)
            except PermissionError:
                print("Don't have permission to rewrite", pth_file)

def immunise_setuptools():
    ei_file = easy_install.__file__
    if not os.access(ei_file, os.R_OK|os.W_OK):
        print("Don't have access to {}, not changing".format(ei_file))
        return

    # Don't try this at home
    lines, first_line_no = inspect.getsourcelines(
                easy_install.PthDistributions.save)

    mod = ast.parse("".join(lines).lstrip())
    pattern = ast.Assign(targets=[ast.Name(id='data')],
                  value=ast.BinOp(left=ast.Str(), op=ast.Mod(),
                              right=ast.Name(id='data')))
    for astpath, node in _walk_with_path(mod):
        if astcheck.is_ast_like(node, pattern):
            break
    else:
        print("Leaving easy_install module untouched")
        return

    starting_line = first_line_no + node.lineno - 1

    parent = _resolve_ast_path(astpath[:-2], mod)  # -2 for ('body', ix)
    if astpath[-1] == len(parent.body) - 1:
        print("PthDistributions.save not as expected, leaving untouched")
        return

    print("Immunising", ei_file)
    next_node = parent.body[astpath[-1]+1]
    finishing_line = first_line_no + next_node.lineno - 1
    print("Cut lines:", starting_line, finishing_line)

    with open(ei_file) as f:
        contents = f.readlines()

    #print(contents[starting_line-1:finishing_line-1])
    contents[starting_line-1:finishing_line-1] = []

    with open(ei_file, 'w') as f:
        f.writelines(contents)



def _walk_with_path(ast_node, path=()):
    """
    Variant of ast.walk() that tracks the paths to nodes

    A path is a tuple of attribute names and integer indices into lists, e.g.
    ('body', 3, 'test') means node.body[3].test
    """
    yield (path, ast_node)
    for name in ast_node._fields:
        try:
            field = getattr(ast_node, name)
        except AttributeError:
            continue

        if isinstance(field, ast.AST):
            yield from _walk_with_path(field, path+(name,))
        elif isinstance(field, list):
            for ix, item in enumerate(field):
                yield from _walk_with_path(item, path+(name, ix))

def _ast_path_parent(path):
    if isinstance(path[-1], int):
        return path[:-2]
    return path[:-1]

def _resolve_ast_path(path, node):
    obj = node
    for part in path:
        if isinstance(part, str):
            obj = getattr(obj, part)
        else:
            obj = obj[part]
    return obj

def main():
    pth_doctor()
    immunise_setuptools()
