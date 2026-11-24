"""Geração de código: AST tipada (saída da análise semântica) -> assembly JVM.

Cada classe COOL vira uma classe JVM (um arquivo .j para o Jasmin).

Representação dos valores na pilha da JVM:
    Int, Bool  -> int  (Bool: 0 = false, 1 = true)
    String     -> java/lang/String
    outros     -> referência para um objeto (CoolObject e subclasses); void = null
Quando um Int/Bool/String vai para um lugar de tipo Object, ele é
"encaixotado" em CoolInt/CoolBool/CoolString (veja _converter).

Para cada método COOL m da classe C são gerados:
    static m$s(C self, params...)  -> corpo do método (self é a local 0)
    m(params...)                   -> método virtual que só chama m$s
O despacho dinâmico usa invokevirtual em m; o despacho estático (e@T.m)
usa invokestatic direto no m$s da classe que define o método.

Para cada classe C também são gerados:
    <init>()       -> construtor JVM: valores padrão dos atributos
    $init_C()      -> inicializadores dos atributos (primeiro os da classe pai)
    $new()         -> usado por "new SELF_TYPE"

Otimizações (desligadas com otimizar=False / coolc.py --sem-otimizacao):
    - constant folding: expressões só com constantes são calculadas na
      compilação; if/while com condição constante geram só o ramo usado;
    - valores descartados: em blocos e no corpo do while, atribuições não
      fazem dup/pop e expressões sem efeito colateral não geram código;
    - desvios diretos: "if a < b" vira um único if_icmpge (sem calcular 0/1);
    - instruções curtas: iload_1/astore_2..., e iinc para "x <- x + c".
"""
import ast_nodes as A
from semantico.constantes import OBJECT, IO, INT, STRING, BOOL, SELF_TYPE

from .jvm import Metodo, nome_campo

BASICAS = (OBJECT, IO, INT, STRING, BOOL)
PRIMITIVOS = (INT, BOOL, STRING)
RT = "CoolRuntime"
_NOMES_JVM = {OBJECT: "CoolObject", INT: "CoolInt", BOOL: "CoolBool", STRING: "CoolString"}


def jnome(t):
    """Nome da classe JVM correspondente a um tipo COOL."""
    return _NOMES_JVM.get(t, t)


def rep(t):
    """Como o valor fica na pilha: 'I' (int), 'S' (String) ou 'R' (referência)."""
    if t in (INT, BOOL):
        return "I"
    if t == STRING:
        return "S"
    return "R"


def desc(t):
    """Descritor JVM de um tipo COOL."""
    if t in (INT, BOOL):
        return "I"
    if t == STRING:
        return "Ljava/lang/String;"
    if t in (OBJECT, SELF_TYPE):
        return "LCoolObject;"
    return f"L{t};"


def desc_params(sig):
    return "".join(desc(t) for _, t in sig.formals)


def desc_metodo(sig):
    return f"({desc_params(sig)}){desc(sig.ret)}"


def _load(r):
    return "iload" if r == "I" else "aload"


def _store(r):
    return "istore" if r == "I" else "astore"


def _return(r):
    return "ireturn" if r == "I" else "areturn"


def _int32(v):
    """Reduz v a um inteiro de 32 bits com sinal (como a JVM faz)."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


def _ld(m, r, slot, curto=True):
    """Carrega uma local; usa a forma curta (iload_1, aload_0...) quando possível."""
    op = _load(r)
    m.emit(f"{op}_{slot}" if curto and slot <= 3 else f"{op} {slot}", 1)


def _st(m, r, slot, curto=True):
    op = _store(r)
    m.emit(f"{op}_{slot}" if curto and slot <= 3 else f"{op} {slot}", -1)


class Gerador:
    def __init__(self, program, analyzer, otimizar=True):
        self.program = program
        self.an = analyzer
        self.otimizar = otimizar
        self.cur = None           # classe sendo gerada
        self.m = None             # Metodo sendo gerado
        self.escopos = []         # pilha de {nome: (slot, tipo)} para variáveis locais
        self._campos = {}         # cache: classe -> {atributo: tipo} (inclui herdados)

    # ================================================================ classes
    def gerar(self):
        """Retorna {nome_do_arquivo: texto} com um .j por classe do usuário."""
        return {info.name + ".j": self._classe(info) for info in self.an.user_classes}

    def _classe(self, info):
        C, P = info.name, jnome(info.parent)
        self.cur = C
        partes = [f"; classe COOL {C} (herda de {info.parent})",
                  f".class public {C}", f".super {P}"]
        if C == "Main":
            partes.append(".implements java/lang/Runnable")   # veja _ponto_de_entrada
        partes.append("")
        for nome, (t, _) in info.attrs.items():
            partes.append(f".field public {nome_campo(nome)} {desc(t)}")
        partes.append("")

        partes.append(self._construtor(info, P))
        partes.append(self._init_atributos(info))
        partes.append(self._fabrica(C))
        for f in info.node.features:
            if isinstance(f, A.Method):
                partes.extend(self._metodo(info, f))
        if C == "Main":
            partes.append(self._ponto_de_entrada())
        return "\n".join(partes)

    def _construtor(self, info, P):
        m = Metodo(".method public <init>()V")
        m.emit("aload_0", 1)
        m.emit(f"invokespecial {P}/<init>()V", -1)
        # Int/Bool já começam com 0 e objetos com null; String começa com ""
        for nome, (t, _) in info.attrs.items():
            if t == STRING:
                m.emit("aload_0", 1)
                m.push_str("")
                m.emit(f"putfield {info.name}/{nome_campo(nome)} {desc(t)}", -2)
        m.emit("return")
        return m.texto()

    def _init_atributos(self, info):
        C = info.name
        self._comecar(Metodo(f".method public $init_{C}()V"))
        if info.parent not in BASICAS:
            self.m.emit("aload_0", 1)
            self.m.emit(f"invokevirtual {info.parent}/$init_{info.parent}()V", -1)
        for f in info.node.features:
            if isinstance(f, A.Attr) and f.init is not None:
                t = info.attrs[f.name][0]
                self.m.comentario(f"{f.name} <- ... (linha {f.line})")
                self.m.emit("aload_0", 1)
                self.expr(f.init)
                self._converter(f.init.static_type, t)
                self.m.emit(f"putfield {C}/{nome_campo(f.name)} {desc(t)}", -2)
        self.m.emit("return")
        return self._terminar()

    def _fabrica(self, C):
        m = Metodo(".method public $new()LCoolObject;")
        self._new_objeto(m, C)
        m.emit("areturn", -1)
        return m.texto()

    def _metodo(self, info, f):
        C = info.name
        sig = info.methods[f.name]
        r = rep(sig.ret)

        # corpo: método estático com self explícito
        estatico = f"{f.name}$s(L{C};{desc_params(sig)}){desc(sig.ret)}"
        self._comecar(Metodo(f".method public static {estatico}", 1 + len(sig.formals)))
        self.escopos.append({n: (i, t) for i, (n, t) in enumerate(sig.formals, start=1)})
        self.expr(f.body)
        self._converter(f.body.static_type, sig.ret)
        self.m.emit(_return(r), -1)
        corpo = self._terminar()

        # método virtual: repassa self e os parâmetros para o corpo estático
        m = Metodo(f".method public {f.name}{desc_metodo(sig)}", 1 + len(sig.formals))
        m.emit("aload_0", 1)
        for i, (_, t) in enumerate(sig.formals, start=1):
            _ld(m, rep(t), i, self.otimizar)
        m.emit(f"invokestatic {C}/{estatico}", -len(sig.formals))
        m.emit(_return(r), -1)
        return [f"; metodo {sig}", corpo, m.texto()]

    def _ponto_de_entrada(self):
        """O programa roda numa thread com pilha de 32 MB (a pilha padrão da JVM
        estoura com ~200 mil chamadas recursivas; 32 MB aguenta ~1 milhão).
        Se mesmo assim estourar, vira um erro de execução do COOL."""
        sig = self.an._achar_metodo("Main", "main")

        # main(String[]): cria a thread, inicia e espera terminar
        m = Metodo(".method public static main([Ljava/lang/String;)V")
        m.emit("new java/lang/Thread", 1)
        m.emit("dup", 1)
        m.emit("aconst_null", 1)                           # ThreadGroup
        m.emit("new Main", 1)                              # Runnable
        m.emit("dup", 1)
        m.emit("invokespecial Main/<init>()V", -1)
        m.push_str("cool-main")
        m.emit("ldc2_w 33554432", 2)                       # pilha de 32 MB (long)
        m.emit("invokespecial java/lang/Thread/<init>(Ljava/lang/ThreadGroup;"
               "Ljava/lang/Runnable;Ljava/lang/String;J)V", -6)
        m.emit("dup", 1)
        m.emit("invokevirtual java/lang/Thread/start()V", -1)
        m.emit("invokevirtual java/lang/Thread/join()V", -1)
        m.emit(f"invokestatic {RT}/flush()V")
        m.emit("return")
        principal = m.texto()

        # run(): inicializa os atributos de Main e chama main()
        r = Metodo(".method public run()V")
        r.codigo.append("    .catch java/lang/StackOverflowError from Ini to Fim using Estouro")
        r.marca("Ini")
        r.emit("aload_0", 1)
        r.emit("invokevirtual Main/$init_Main()V", -1)
        r.emit("aload_0", 1)
        r.emit(f"invokevirtual Main/main{desc_metodo(sig)}", 0)
        r.emit("pop", -1)
        r.marca("Fim")
        r.emit("return")
        r.marca("Estouro", 1)
        r.emit("pop", -1)
        r.emit(f"invokestatic {RT}/erroPilha()V")
        r.emit("return")
        return ("; ponto de entrada da JVM: roda (new Main).main() numa thread\n"
                + principal + "\n" + r.texto())

    def _new_objeto(self, m, t):
        J = jnome(t)
        m.emit(f"new {J}", 1)
        m.emit("dup", 1)
        m.emit(f"invokespecial {J}/<init>()V", -1)
        if t not in BASICAS:
            m.emit("dup", 1)
            m.emit(f"invokevirtual {J}/$init_{J}()V", -1)

    # ============================================================ auxiliares
    def _comecar(self, metodo):
        self.m = metodo
        self.escopos = []

    def _terminar(self):
        texto = self.m.texto()
        self.m = None
        return texto

    def _campos_de(self, cls):
        if cls not in self._campos:
            self._campos[cls] = self.an._todos_atributos(cls)
        return self._campos[cls]

    def _dono_campo(self, nome):
        """Classe que declara o atributo (procura do atual para os pais)."""
        c = self.cur
        while c is not None:
            if nome in self.an.classes[c].attrs:
                return c
            c = self.an.classes[c].parent
        return self.cur

    def _var(self, nome):
        """('local', slot, tipo) ou ('campo', None, tipo)."""
        for esc in reversed(self.escopos):
            if nome in esc:
                slot, t = esc[nome]
                return "local", slot, t
        return "campo", None, self._campos_de(self.cur)[nome]

    def _definidor(self, cls, nome):
        """(classe que define o método, assinatura), subindo pela herança."""
        while cls is not None:
            sig = self.an.classes[cls].methods.get(nome)
            if sig is not None:
                return cls, sig
            cls = self.an.classes[cls].parent
        raise KeyError(nome)

    def _profundidade(self, t):
        return len(self.an._ancestrais(t))

    def _real(self, t):
        return self.cur if t == SELF_TYPE else t

    def _converter(self, de, para):
        """Ajusta o valor no topo da pilha do tipo 'de' para o lugar de tipo 'para'."""
        rd, rp = rep(de), rep(para)
        if rd == rp:
            return
        if rd == "I":
            J = jnome(de)
            self.m.emit(f"invokestatic {J}/box(I)L{J};")
        elif rd == "S":
            self.m.emit("invokestatic CoolString/box(Ljava/lang/String;)LCoolString;")
        # 'R' -> 'R' não precisa de nada (subclasse no lugar da superclasse)

    def _padrao(self, t):
        """Empilha o valor padrão de uma variável do tipo t."""
        if rep(t) == "I":
            self.m.push_int(0)
        elif t == STRING:
            self.m.push_str("")
        else:
            self.m.emit("aconst_null", 1)

    def _booleano(self, instr_desvio):
        """Converte um desvio condicional (que consome 2 ints) em 0/1 na pilha."""
        m = self.m
        verdadeiro, fim = m.rotulo(), m.rotulo()
        m.emit(f"{instr_desvio} {verdadeiro}", -2)
        base = m.altura
        m.push_int(0)
        m.emit(f"goto {fim}")
        m.marca(verdadeiro, base)
        m.push_int(1)
        m.marca(fim)

    def _ld(self, r, slot):
        _ld(self.m, r, slot, self.otimizar)

    def _st(self, r, slot):
        _st(self.m, r, slot, self.otimizar)

    # ======================================================== otimizações
    def _constante(self, e):
        """Valor de e se ele puder ser calculado em tempo de compilação
        (int para Int, bool para Bool), senão None.  [constant folding]"""
        if isinstance(e, A.IntConst):
            return e.value
        if isinstance(e, A.BoolConst):
            return e.value
        if isinstance(e, A.Neg):
            v = self._constante(e.expr)
            return _int32(-v) if _eh_int(v) else None
        if isinstance(e, A.Not):
            v = self._constante(e.expr)
            return (not v) if isinstance(v, bool) else None
        if isinstance(e, A.BinOp):
            a, b = self._constante(e.left), self._constante(e.right)
            if isinstance(e, A.Eq):
                if a is not None and b is not None and type(a) is type(b):
                    return a == b
                return None
            if not (_eh_int(a) and _eh_int(b)):
                return None
            if isinstance(e, A.Plus):
                return _int32(a + b)
            if isinstance(e, A.Sub):
                return _int32(a - b)
            if isinstance(e, A.Mul):
                return _int32(a * b)
            if isinstance(e, A.Div):
                if b == 0:
                    return None                  # o erro tem que acontecer na execução
                q = abs(a) // abs(b)             # a JVM trunca em direção a zero
                return _int32(q if (a < 0) == (b < 0) else -q)
            if isinstance(e, A.Lt):
                return a < b
            if isinstance(e, A.Leq):
                return a <= b
        return None

    def _sem_efeito(self, e):
        """Expressões que podem ser descartadas sem gerar código."""
        return (isinstance(e, (A.IntConst, A.BoolConst, A.StringConst, A.Object))
                or self._constante(e) is not None)

    def _descartar(self, e):
        """Gera e só pelos efeitos colaterais (o valor não é usado)."""
        if self.otimizar:
            if self._sem_efeito(e):
                return
            if isinstance(e, A.Assign):
                self._atribuir(e, manter=False)
                return
            if isinstance(e, A.Block):
                for sub in e.exprs:
                    self._descartar(sub)
                return
            if isinstance(e, A.While):
                self._laco(e)                    # sem o aconst_null/pop
                return
        self.expr(e)
        self.m.emit("pop", -1)

    def _desvio(self, e, rotulo, quando):
        """Desvia para 'rotulo' se o valor booleano de e for igual a 'quando'.
        Comparações viram um único if_icmpXX, sem calcular 0/1 antes."""
        m = self.m
        if self.otimizar:
            v = self._constante(e)
            if isinstance(v, bool):
                if v == quando:
                    m.emit(f"goto {rotulo}")
                return
            if isinstance(e, A.Not):
                self._desvio(e.expr, rotulo, not quando)
                return
            comparacoes = {A.Lt: ("if_icmplt", "if_icmpge"),
                           A.Leq: ("if_icmple", "if_icmpgt")}
            if type(e) in comparacoes:
                self._binario(e)
                m.emit(f"{comparacoes[type(e)][0 if quando else 1]} {rotulo}", -2)
                return
            if (isinstance(e, A.Eq) and rep(e.left.static_type) == "I"
                    and rep(e.right.static_type) == "I"):
                self._binario(e)
                m.emit(f"{'if_icmpeq' if quando else 'if_icmpne'} {rotulo}", -2)
                return
            if isinstance(e, A.IsVoid) and rep(e.expr.static_type) == "R":
                self.expr(e.expr)
                m.emit(f"{'ifnull' if quando else 'ifnonnull'} {rotulo}", -1)
                return
        self.expr(e)
        m.emit(f"{'ifne' if quando else 'ifeq'} {rotulo}", -1)

    def _incremento(self, e, slot):
        """Se e for 'x <- x + c' ou 'x <- x - c' (x local Int, c pequeno),
        devolve c para usar a instrução iinc."""
        x = e.expr
        c = None
        if isinstance(x, A.Plus):
            if isinstance(x.left, A.Object) and x.left.name == e.name:
                c = self._constante(x.right)
            elif isinstance(x.right, A.Object) and x.right.name == e.name:
                c = self._constante(x.left)
        elif isinstance(x, A.Sub):
            if isinstance(x.left, A.Object) and x.left.name == e.name:
                c = self._constante(x.right)
                c = -c if _eh_int(c) else None
        return c if _eh_int(c) and -128 <= c <= 127 else None

    # =========================================================== expressões
    def expr(self, e):
        """Gera o código de e; deixa exatamente um valor na pilha."""
        if self.otimizar and not isinstance(e, (A.IntConst, A.BoolConst)):
            v = self._constante(e)
            if v is not None:
                self.m.comentario(f"constante calculada na compilacao")
                self.m.push_int(int(v))
                return
        metodo = getattr(self, "_e_" + type(e).__name__)
        metodo(e)

    # ---- constantes
    def _e_IntConst(self, e):
        self.m.push_int(e.value)

    def _e_BoolConst(self, e):
        self.m.push_int(1 if e.value else 0)

    def _e_StringConst(self, e):
        self.m.push_str(e.value)

    # ---- variáveis
    def _e_Object(self, e):
        m = self.m
        if e.name == "self":
            m.emit("aload_0", 1)
            return
        tipo_var, slot, t = self._var(e.name)
        if tipo_var == "local":
            self._ld(rep(t), slot)
        else:
            m.emit("aload_0", 1)
            m.emit(f"getfield {self._dono_campo(e.name)}/{nome_campo(e.name)} {desc(t)}", 0)
        if t == SELF_TYPE:
            m.emit(f"checkcast {jnome(self.cur)}")

    def _e_Assign(self, e):
        self._atribuir(e, manter=True)

    def _atribuir(self, e, manter):
        """manter=True: o valor da atribuição fica na pilha (é o valor da expressão)."""
        m = self.m
        tipo_var, slot, t = self._var(e.name)
        if self.otimizar and tipo_var == "local" and t == INT:
            c = self._incremento(e, slot)
            if c is not None:
                m.emit(f"iinc {slot} {c}")
                if manter:
                    self._ld("I", slot)
                return
        self.expr(e.expr)
        if manter or not self.otimizar:
            m.emit("dup", 1)
        self._converter(e.expr.static_type, t)
        if tipo_var == "local":
            self._st(rep(t), slot)
        else:
            m.emit("aload_0", 1)
            m.emit("swap")
            m.emit(f"putfield {self._dono_campo(e.name)}/{nome_campo(e.name)} {desc(t)}", -2)

    # ---- aritmética e comparação
    def _binario(self, e):
        self.expr(e.left)
        self.expr(e.right)

    def _e_Plus(self, e):
        self._binario(e)
        self.m.emit("iadd", -1)

    def _e_Sub(self, e):
        self._binario(e)
        self.m.emit("isub", -1)

    def _e_Mul(self, e):
        self._binario(e)
        self.m.emit("imul", -1)

    def _e_Div(self, e):
        self._binario(e)
        self.m.push_int(e.line)
        self.m.emit(f"invokestatic {RT}/div(III)I", -2)

    def _e_Lt(self, e):
        self._binario(e)
        self._booleano("if_icmplt")

    def _e_Leq(self, e):
        self._binario(e)
        self._booleano("if_icmple")

    def _e_Eq(self, e):
        a, b = e.left.static_type, e.right.static_type
        m = self.m
        if rep(a) == "I" and rep(b) == "I":
            self._binario(e)
            self._booleano("if_icmpeq")
        elif rep(a) == "S" and rep(b) == "S":
            self._binario(e)
            m.emit("invokevirtual java/lang/String/equals(Ljava/lang/Object;)Z", -1)
        else:
            self.expr(e.left)
            self._converter(a, OBJECT)
            self.expr(e.right)
            self._converter(b, OBJECT)
            m.emit(f"invokestatic {RT}/eq(Ljava/lang/Object;Ljava/lang/Object;)I", -1)

    def _e_Neg(self, e):
        self.expr(e.expr)
        self.m.emit("ineg")

    def _e_Not(self, e):
        self.expr(e.expr)
        self.m.push_int(1)
        self.m.emit("ixor", -1)

    def _e_IsVoid(self, e):
        m = self.m
        self.expr(e.expr)
        if rep(e.expr.static_type) != "R":       # Int/Bool/String nunca são void
            m.emit("pop", -1)
            m.push_int(0)
            return
        verdadeiro, fim = m.rotulo(), m.rotulo()
        m.emit(f"ifnull {verdadeiro}", -1)
        base = m.altura
        m.push_int(0)
        m.emit(f"goto {fim}")
        m.marca(verdadeiro, base)
        m.push_int(1)
        m.marca(fim)

    # ---- controle de fluxo
    def _e_If(self, e):
        m = self.m
        t = e.static_type
        if self.otimizar:
            v = self._constante(e.cond)
            if isinstance(v, bool):              # condição constante: só um ramo é gerado
                ramo = e.then_branch if v else e.else_branch
                self.expr(ramo)
                self._converter(ramo.static_type, t)
                return
        senao, fim = m.rotulo(), m.rotulo()
        self._desvio(e.cond, senao, False)
        base = m.altura
        self.expr(e.then_branch)
        self._converter(e.then_branch.static_type, t)
        m.emit(f"goto {fim}")
        m.marca(senao, base)
        self.expr(e.else_branch)
        self._converter(e.else_branch.static_type, t)
        m.marca(fim)

    def _e_While(self, e):
        m = self.m
        self._laco(e)
        m.emit("aconst_null", 1)                 # while tem valor void

    def _laco(self, e):
        m = self.m
        if self.otimizar and self._constante(e.cond) is False:
            return                               # o laço nunca executa
        inicio, fim = m.rotulo(), m.rotulo()
        m.marca(inicio)
        self._desvio(e.cond, fim, False)
        self._descartar(e.body)
        m.emit(f"goto {inicio}")
        m.marca(fim)

    def _e_Block(self, e):
        for sub in e.exprs[:-1]:
            self._descartar(sub)
        self.expr(e.exprs[-1])

    def _e_Let(self, e):
        m = self.m
        t = e.type
        if e.init is not None:
            self.expr(e.init)
            self._converter(e.init.static_type, t)
        else:
            self._padrao(t)
        slot = m.nova_local()
        self._st(rep(t), slot)
        self.escopos.append({e.name: (slot, t)})
        self.expr(e.body)
        self.escopos.pop()

    def _e_Case(self, e):
        m = self.m
        t = e.static_type
        self.expr(e.expr)
        self._converter(e.expr.static_type, OBJECT)
        tmp = m.nova_local()
        self._st("R", tmp)

        ok, fim = m.rotulo(), m.rotulo()
        self._ld("R", tmp)
        m.emit(f"ifnonnull {ok}", -1)
        m.push_str("case em objeto void")
        m.push_int(e.line)
        m.emit(f"invokestatic {RT}/error(Ljava/lang/String;I)V", -2)
        m.marca(ok)
        base = m.altura

        # ramos da classe mais específica para a mais geral
        ramos = sorted(e.branches, key=lambda b: -self._profundidade(b.type))
        for b in ramos:
            J = jnome(b.type)
            proximo = m.rotulo()
            self._ld("R", tmp)
            m.emit(f"instanceof {J}")
            m.emit(f"ifeq {proximo}", -1)
            self._ld("R", tmp)
            m.emit(f"checkcast {J}")
            if b.type in (INT, BOOL):
                m.emit(f"getfield {J}/val I")        # desencaixota
            elif b.type == STRING:
                m.emit("getfield CoolString/val Ljava/lang/String;")
            slot = m.nova_local()
            self._st(rep(b.type), slot)
            self.escopos.append({b.name: (slot, b.type)})
            self.expr(b.expr)
            self.escopos.pop()
            self._converter(b.expr.static_type, t)
            m.emit(f"goto {fim}")
            m.marca(proximo, base)

        m.push_str("nenhum ramo do case corresponde ao tipo do valor")
        m.push_int(e.line)
        m.emit(f"invokestatic {RT}/error(Ljava/lang/String;I)V", -2)
        self._padrao(t)                          # nunca executa; mantém a pilha coerente
        m.marca(fim)

    # ---- objetos
    def _e_New(self, e):
        m = self.m
        if e.type == SELF_TYPE:
            m.emit("aload_0", 1)
            m.emit("invokevirtual CoolObject/$new()LCoolObject;")
            m.emit(f"checkcast {jnome(self.cur)}")
        elif e.type in PRIMITIVOS:
            self._padrao(e.type)
        else:
            self._new_objeto(m, e.type)

    def _e_Dispatch(self, e):
        t0 = e.object.static_type
        cls = self._real(t0)
        if cls in PRIMITIVOS:
            self._metodo_basico(e, cls)
            return
        _, sig = self._definidor(cls, e.method)
        self._receptor_e_args(e, sig, t0, cls)
        self.m.emit(f"invokevirtual {jnome(cls)}/{e.method}{desc_metodo(sig)}",
                    -len(sig.formals))
        if sig.ret == SELF_TYPE:
            self.m.emit(f"checkcast {jnome(cls)}")

    def _e_StaticDispatch(self, e):
        t0 = e.object.static_type
        if e.type in PRIMITIVOS:
            self._metodo_basico(e, e.type)
            return
        dono, sig = self._definidor(e.type, e.method)
        self._receptor_e_args(e, sig, t0, e.type)
        n = len(sig.formals)
        # o corpo de todo método (inclusive os de Object e IO, no runtime) está
        # na versão estática m$s da classe que o define
        J = jnome(dono)
        self.m.emit(f"invokestatic {J}/{e.method}$s(L{J};{desc_params(sig)})"
                    f"{desc(sig.ret)}", -n)
        if sig.ret == SELF_TYPE:
            self.m.emit(f"checkcast {jnome(self._real(t0))}")

    def _receptor_e_args(self, e, sig, t0, cls):
        """Empilha receptor e argumentos. Em COOL os argumentos são avaliados
        antes do receptor; por isso, quando o receptor não é 'self', os
        argumentos vão para locais temporárias primeiro."""
        m = self.m
        formais = [t for _, t in sig.formals]
        if isinstance(e.object, A.Object) and e.object.name == "self":
            m.emit("aload_0", 1)
            for a, tf in zip(e.args, formais):
                self.expr(a)
                self._converter(a.static_type, tf)
            return

        temps = []
        for a, tf in zip(e.args, formais):
            self.expr(a)
            self._converter(a.static_type, tf)
            slot = m.nova_local()
            self._st(rep(tf), slot)
            temps.append((slot, tf))
        self.expr(e.object)
        self._converter(t0, cls)                 # ex.: Int em e@Object.type_name()
        m.emit("dup", 1)
        m.push_int(e.line)
        m.emit(f"invokestatic {RT}/checkVoid(Ljava/lang/Object;I)V", -2)
        for slot, tf in temps:
            self._ld(rep(tf), slot)

    def _metodo_basico(self, e, cls):
        """Métodos chamados sobre Int, Bool ou String (que não são objetos JVM)."""
        m = self.m
        if e.args and not isinstance(e.object, A.StringConst):
            # argumentos antes do receptor (regra do COOL), via temporárias
            temps = []
            for a in e.args:
                self.expr(a)
                slot = m.nova_local()
                self._st(rep(a.static_type), slot)
                temps.append((slot, a.static_type))
            self.expr(e.object)
            for slot, t in temps:
                self._ld(rep(t), slot)
        else:
            self.expr(e.object)
            for a in e.args:
                self.expr(a)
        nome = e.method
        if cls == STRING and nome == "length":
            m.emit("invokevirtual java/lang/String/length()I")
        elif cls == STRING and nome == "concat":
            m.emit("invokevirtual java/lang/String/concat(Ljava/lang/String;)Ljava/lang/String;", -1)
        elif cls == STRING and nome == "substr":
            m.push_int(e.line)
            m.emit(f"invokestatic {RT}/substr(Ljava/lang/String;III)Ljava/lang/String;", -3)
        elif nome == "copy":
            pass                                 # valores imutáveis: a cópia é o próprio valor
        elif nome == "type_name":
            self._converter(cls, OBJECT)
            m.emit("invokevirtual CoolObject/type_name()Ljava/lang/String;")
        elif nome == "abort":
            self._converter(cls, OBJECT)
            m.emit("invokevirtual CoolObject/abort()LCoolObject;")
        else:
            raise KeyError(f"método básico desconhecido: {cls}.{nome}")


def _eh_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def gerar(program, analyzer, otimizar=True):
    return Gerador(program, analyzer, otimizar).gerar()
