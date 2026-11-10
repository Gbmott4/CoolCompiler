"""Nomes de tipos e tabelas fixas usadas pela análise semântica."""
import ast_nodes as A

SELF_TYPE = "SELF_TYPE"
OBJECT, IO, INT, STRING, BOOL = "Object", "IO", "Int", "String", "Bool"
NAO_HERDAVEIS = (INT, STRING, BOOL, SELF_TYPE)
PRIMITIVOS = (INT, STRING, BOOL)

SIMBOLOS = {A.Plus: "+", A.Sub: "-", A.Mul: "*", A.Div: "/",
            A.Lt: "<", A.Leq: "<="}
