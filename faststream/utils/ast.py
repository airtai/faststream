import ast
import traceback
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Union


def is_contains_context_name(scip_name: str, name: str) -> bool:
    stack = traceback.extract_stack()[-3]
    tree = read_source_ast(stack.filename)
    node = find_ast_node(tree, stack.lineno)
    context_calls = get_withitem_calls(node)

    try:
        pos = context_calls.index(scip_name)
    except ValueError:
        pos = 1

    return name in context_calls[pos:]


@lru_cache
def read_source_ast(filename: str) -> ast.Module:
    return ast.parse(Path(filename).read_text())


def find_ast_node(module: ast.Module, lineno: int) -> ast.AST:
    for i in getattr(module, "body", ()):
        if i.lineno == lineno:
            return i

        r = find_ast_node(i, lineno)
        if r is not None:
            return r


def find_withitems(node: Union[ast.With, ast.AsyncWith]) -> Iterator[ast.withitem]:
    if isinstance(node, (ast.With, ast.AsyncWith)):
        yield from node.items

    for i in getattr(node, "body", ()):
        yield from find_withitems(i)


def get_withitem_calls(node: Union[ast.With, ast.AsyncWith]) -> list[str]:
    return [
        id
        for i in find_withitems(node)
        if (id := getattr(i.context_expr.func, "id", None))
    ]
