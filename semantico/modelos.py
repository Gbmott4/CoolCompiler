"""Estruturas de dados da análise semântica: erro, assinatura de método,
informações de classe e pilha de escopos."""


class SemanticError(Exception):
    def __init__(self, line, msg):
        super().__init__(msg)
        self.line = line
        self.msg = msg


class MethodSig:
    """Assinatura de um método: nome, parâmetros [(nome, tipo)] e tipo de retorno."""
    def __init__(self, name, formals, ret, line):
        self.name = name
        self.formals = formals
        self.ret = ret
        self.line = line

    def __str__(self):
        params = ", ".join(f"{n}: {t}" for n, t in self.formals)
        return f"{self.name}({params}): {self.ret}"


class ClassInfo:
    def __init__(self, name, parent, line, node=None):
        self.name = name
        self.parent = parent
        self.line = line
        self.node = node          # nó Class da AST (None nas classes básicas)
        self.attrs = {}           # atributos próprios: nome -> (tipo, linha)
        self.methods = {}         # métodos próprios: nome -> MethodSig


class Scope:
    """Pilha de escopos para variáveis (atributos, parâmetros, let, case)."""
    def __init__(self):
        self.stack = [{}]

    def push(self, nomes=None):
        self.stack.append(dict(nomes) if nomes else {})

    def pop(self):
        self.stack.pop()

    def declare(self, nome, tipo):
        self.stack[-1][nome] = tipo

    def lookup(self, nome):
        for d in reversed(self.stack):
            if nome in d:
                return d[nome]
        return None
