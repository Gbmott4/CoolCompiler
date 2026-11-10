from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Node:
    line: int
    # Preenchido pela análise semântica (checagem de tipos). Não vem do JSON.
    static_type: Optional[str] = field(default=None, init=False)


# ---------- estrutura do programa ----------

@dataclass
class Program(Node):
    classes: List["Class"]


@dataclass
class Class(Node):
    name: str
    parent: str                      # "Object" quando não há 'inherits'
    features: List[Node]


@dataclass
class Attr(Node):
    name: str
    type: str
    init: Optional[Node]


@dataclass
class Formal(Node):
    name: str
    type: str


@dataclass
class Method(Node):
    name: str
    formals: List[Formal]
    return_type: str
    body: Node


# ---------- expressões ----------

@dataclass
class Assign(Node):
    name: str
    expr: Node


@dataclass
class Dispatch(Node):                # e.f(args)  ou  f(args) == self.f(args)
    object: Node
    method: str
    args: List[Node]


@dataclass
class StaticDispatch(Node):          # e@T.f(args)
    object: Node
    type: str
    method: str
    args: List[Node]


@dataclass
class If(Node):
    cond: Node
    then_branch: Node
    else_branch: Node


@dataclass
class While(Node):
    cond: Node
    body: Node


@dataclass
class Block(Node):
    exprs: List[Node]


@dataclass
class Let(Node):                     # let com várias variáveis vira lets aninhados
    name: str
    type: str
    init: Optional[Node]
    body: Node


@dataclass
class Branch(Node):
    name: str
    type: str
    expr: Node


@dataclass
class Case(Node):
    expr: Node
    branches: List[Branch]


@dataclass
class New(Node):
    type: str


@dataclass
class IsVoid(Node):
    expr: Node


@dataclass
class Neg(Node):                     # ~e
    expr: Node


@dataclass
class Not(Node):
    expr: Node


@dataclass
class BinOp(Node):
    left: Node
    right: Node


class Plus(BinOp): pass
class Sub(BinOp): pass
class Mul(BinOp): pass
class Div(BinOp): pass
class Lt(BinOp): pass
class Leq(BinOp): pass
class Eq(BinOp): pass


@dataclass
class Object(Node):                  # referência a variável (inclui 'self')
    name: str


@dataclass
class IntConst(Node):
    value: int


@dataclass
class StringConst(Node):
    value: str


@dataclass
class BoolConst(Node):
    value: bool


# kind (JSON) -> classe
KINDS = {
    "program": Program, "class": Class, "attr": Attr, "formal": Formal,
    "method": Method, "assign": Assign, "dispatch": Dispatch,
    "static_dispatch": StaticDispatch, "if": If, "while": While,
    "block": Block, "let": Let, "branch": Branch, "case": Case, "new": New,
    "isvoid": IsVoid, "neg": Neg, "not": Not, "plus": Plus, "sub": Sub,
    "mul": Mul, "div": Div, "lt": Lt, "leq": Leq, "eq": Eq,
    "object": Object, "int": IntConst, "string": StringConst, "bool": BoolConst,
}


def build(d):
    """Converte recursivamente um dict/list do JSON em objetos da AST."""
    if isinstance(d, list):
        return [build(x) for x in d]
    if not isinstance(d, dict):
        return d                     # str ou None

    kind = d["kind"]
    cls = KINDS[kind]
    kwargs = {k: build(v) for k, v in d.items() if k not in ("kind", "line")}

    if kind == "int":
        kwargs["value"] = int(kwargs["value"])
    elif kind == "bool":
        kwargs["value"] = (kwargs["value"] == "true")

    return cls(line=d["line"], **kwargs)


def load_ast(text: str) -> Program:
    return build(json.loads(text))
