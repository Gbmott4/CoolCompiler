"""Nomes de tipos e tabelas fixas usadas pela análise semântica."""
import ast_nodes as A

SELF_TYPE = "SELF_TYPE"
OBJECT, IO, INT, STRING, BOOL = "Object", "IO", "Int", "String", "Bool"
NAO_HERDAVEIS = (INT, STRING, BOOL, SELF_TYPE)
PRIMITIVOS = (INT, STRING, BOOL)

# Nomes usados pelas classes JVM do runtime (pasta runtime/). Uma classe do
# usuário com um desses nomes colidiria com elas no bytecode gerado.
RESERVADOS_JVM = ("CoolObject", "CoolInt", "CoolBool", "CoolString", "CoolRuntime")

SIMBOLOS = {A.Plus: "+", A.Sub: "-", A.Mul: "*", A.Div: "/",
            A.Lt: "<", A.Leq: "<="}
