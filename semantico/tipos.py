"""Etapa 7: checagem de tipos das expressões (preenche node.static_type)."""
import ast_nodes as A

from .constantes import (OBJECT, INT, STRING, BOOL, SELF_TYPE, PRIMITIVOS,
                        SIMBOLOS)
from .modelos import Scope


class TiposMixin:
    """Métodos do Analyzer que verificam o corpo de atributos e métodos."""

    def _checar_tipos(self):
        for info in self.user_classes:
            self.cur = info.name
            env = Scope()
            for nome, tipo in self._todos_atributos(info.name).items():
                env.declare(nome, tipo)
            for f in info.node.features:
                if isinstance(f, A.Attr):
                    self._checar_atributo(info, f, env)
                else:
                    self._checar_metodo(info, f, env)

    def _checar_atributo(self, info, f, env):
        if f.init is None:
            return
        ti = self.tipo(f.init, env)
        declarado = info.attrs.get(f.name)
        if declarado and not self._conforma(ti, declarado[0]):
            self.error(f.line, f"inicialização do atributo '{f.name}' tem tipo '{ti}', "
                                f"incompatível com '{declarado[0]}'")

    def _checar_metodo(self, info, f, env):
        sig = info.methods.get(f.name)
        env.push({n: t for n, t in sig.formals} if sig else {})
        corpo = self.tipo(f.body, env)
        env.pop()
        if sig and not self._conforma(corpo, sig.ret):
            self.error(f.line, f"corpo do método '{f.name}' tem tipo '{corpo}', "
                                f"incompatível com o retorno '{sig.ret}'")

    # --- relações entre tipos
    def _conforma(self, a, b):
        """a <= b (a é subtipo de b) dentro da classe atual."""
        if a == b:
            return True
        if b == SELF_TYPE:
            return False
        if a == SELF_TYPE:
            a = self.cur
        while a is not None:
            if a == b:
                return True
            a = self.classes[a].parent
        return False

    def _lub(self, a, b):
        """Menor ancestral comum."""
        if a == b:
            return a
        a = self.cur if a == SELF_TYPE else a
        b = self.cur if b == SELF_TYPE else b
        ancestrais = set()
        x = a
        while x is not None:
            ancestrais.add(x)
            x = self.classes[x].parent
        x = b
        while x not in ancestrais:
            x = self.classes[x].parent
        return x

    # --- expressões
    def tipo(self, e, env):
        t = self._tipo(e, env)
        e.static_type = t
        return t

    def _tipo(self, e, env):
        if isinstance(e, A.IntConst):
            return INT
        if isinstance(e, A.StringConst):
            return STRING
        if isinstance(e, A.BoolConst):
            return BOOL

        if isinstance(e, A.Object):
            if e.name == "self":
                return SELF_TYPE
            t = env.lookup(e.name)
            if t is None:
                self.error(e.line, f"identificador '{e.name}' não declarado")
                return OBJECT
            return t

        if isinstance(e, A.Assign):
            t = self.tipo(e.expr, env)
            if e.name == "self":
                self.error(e.line, "não é possível atribuir a 'self'")
                return t
            td = env.lookup(e.name)
            if td is None:
                self.error(e.line, f"atribuição a identificador não declarado '{e.name}'")
            elif not self._conforma(t, td):
                self.error(e.line, f"atribuição a '{e.name}': tipo '{t}' incompatível com '{td}'")
            return t

        if isinstance(e, A.New):
            if e.type == SELF_TYPE:
                return SELF_TYPE
            if e.type not in self.classes:
                self.error(e.line, f"tipo '{e.type}' não definido")
                return OBJECT
            return e.type

        if isinstance(e, A.IsVoid):
            self.tipo(e.expr, env)
            return BOOL

        if isinstance(e, A.Neg):
            t = self.tipo(e.expr, env)
            if t != INT:
                self.error(e.line, f"'~' exige operando Int, mas recebeu '{t}'")
            return INT

        if isinstance(e, A.Not):
            t = self.tipo(e.expr, env)
            if t != BOOL:
                self.error(e.line, f"'not' exige operando Bool, mas recebeu '{t}'")
            return BOOL

        if isinstance(e, A.Eq):
            a = self.tipo(e.left, env)
            b = self.tipo(e.right, env)
            if (a in PRIMITIVOS or b in PRIMITIVOS) and a != b:
                self.error(e.line, f"comparação '=' entre tipos incompatíveis '{a}' e '{b}'")
            return BOOL

        if isinstance(e, A.BinOp):                      # + - * / < <=
            a = self.tipo(e.left, env)
            b = self.tipo(e.right, env)
            simbolo = SIMBOLOS[type(e)]
            if a != INT or b != INT:
                self.error(e.line, f"operador '{simbolo}' exige operandos Int, "
                                    f"mas recebeu '{a}' e '{b}'")
            return BOOL if isinstance(e, (A.Lt, A.Leq)) else INT

        if isinstance(e, A.If):
            c = self.tipo(e.cond, env)
            if c != BOOL:
                self.error(e.line, f"condição do 'if' deve ser Bool, mas é '{c}'")
            return self._lub(self.tipo(e.then_branch, env), self.tipo(e.else_branch, env))

        if isinstance(e, A.While):
            c = self.tipo(e.cond, env)
            if c != BOOL:
                self.error(e.line, f"condição do 'while' deve ser Bool, mas é '{c}'")
            self.tipo(e.body, env)
            return OBJECT

        if isinstance(e, A.Block):
            t = OBJECT
            for sub in e.exprs:
                t = self.tipo(sub, env)
            return t

        if isinstance(e, A.Let):
            declarado = self._resolver_tipo(e.type, e.line, True)
            if e.name == "self":
                self.error(e.line, "'self' não pode ser nome de variável do 'let'")
            if e.init is not None:
                ti = self.tipo(e.init, env)     # o init não enxerga a variável nova
                if not self._conforma(ti, declarado):
                    self.error(e.line, f"inicialização de '{e.name}' tem tipo '{ti}', "
                                        f"incompatível com '{declarado}'")
            env.push({e.name: declarado})
            t = self.tipo(e.body, env)
            env.pop()
            return t

        if isinstance(e, A.Case):
            self.tipo(e.expr, env)
            vistos, resultado = set(), None
            for b in e.branches:
                tb = self._resolver_tipo(b.type, b.line, False)
                if b.type in vistos:
                    self.error(b.line, f"tipo '{b.type}' repetido nos ramos do 'case'")
                vistos.add(b.type)
                if b.name == "self":
                    self.error(b.line, "'self' não pode ser nome de variável do 'case'")
                env.push({b.name: tb})
                tr = self.tipo(b.expr, env)
                env.pop()
                b.static_type = tr
                resultado = tr if resultado is None else self._lub(resultado, tr)
            return resultado if resultado is not None else OBJECT

        if isinstance(e, A.Dispatch):
            t0 = self.tipo(e.object, env)
            args = [self.tipo(a, env) for a in e.args]
            cls = self.cur if t0 == SELF_TYPE else t0
            return self._chamada(e, cls, t0, args)

        if isinstance(e, A.StaticDispatch):
            t0 = self.tipo(e.object, env)
            args = [self.tipo(a, env) for a in e.args]
            alvo = e.type
            if alvo == SELF_TYPE:
                self.error(e.line, "despacho estático não pode usar SELF_TYPE")
                alvo = OBJECT
            elif alvo not in self.classes:
                self.error(e.line, f"tipo '{alvo}' não definido")
                alvo = OBJECT
            elif not self._conforma(t0, alvo):
                self.error(e.line, f"despacho estático: '{t0}' não é subtipo de '{alvo}'")
            return self._chamada(e, alvo, t0, args)

        raise TypeError(f"nó desconhecido: {type(e).__name__}")

    def _chamada(self, e, cls, t0, tipos_args):
        sig = self._achar_metodo(cls, e.method)
        if sig is None:
            self.error(e.line, f"método '{e.method}' não definido na classe '{cls}'")
            return OBJECT
        if len(tipos_args) != len(sig.formals):
            self.error(e.line, f"chamada de '{e.method}' com {len(tipos_args)} argumento(s), "
                                f"mas o método espera {len(sig.formals)}")
        else:
            for i, (ta, (_, tf)) in enumerate(zip(tipos_args, sig.formals), start=1):
                if not self._conforma(ta, tf):
                    self.error(e.args[i - 1].line,
                                f"argumento {i} de '{e.method}': tipo '{ta}' incompatível com '{tf}'")
        return t0 if sig.ret == SELF_TYPE else sig.ret
