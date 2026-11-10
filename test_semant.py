"""Testes do analisador semântico.

Monta ASTs diretamente (no mesmo formato do JSON do parser em C) e confere
as mensagens de erro. Rodar:  python3 test_semant.py
"""
import ast_nodes as A
from semantico import Analyzer


def N(kind, line=1, **kw):
    d = {"kind": kind, "line": line}
    d.update(kw)
    return d

obj = lambda n, l=1: N("object", l, name=n)
inteiro = lambda v, l=1: N("int", l, value=str(v))
texto = lambda v, l=1: N("string", l, value=v)
booleano = lambda v, l=1: N("bool", l, value="true" if v else "false")
novo = lambda t, l=1: N("new", l, type=t)
plus = lambda a, b, l=1: N("plus", l, left=a, right=b)
mul = lambda a, b, l=1: N("mul", l, left=a, right=b)
eq = lambda a, b, l=1: N("eq", l, left=a, right=b)
lt = lambda a, b, l=1: N("lt", l, left=a, right=b)
se = lambda c, t, e, l=1: N("if", l, cond=c, then_branch=t, else_branch=e)
bloco = lambda *xs, l=1: N("block", l, exprs=list(xs))
atrib = lambda n, e, l=1: N("assign", l, name=n, expr=e)
let = lambda n, t, init, corpo, l=1: N("let", l, name=n, type=t, init=init, body=corpo)
chama = lambda o, m, *args, l=1: N("dispatch", l, object=o, method=m, args=list(args))
chama_self = lambda m, *args, l=1: chama(obj("self", l), m, *args, l=l)
estatica = lambda o, t, m, *args, l=1: N("static_dispatch", l, object=o, type=t, method=m, args=list(args))
ramo = lambda n, t, e, l=1: N("branch", l, name=n, type=t, expr=e)
caso = lambda e, *rs, l=1: N("case", l, expr=e, branches=list(rs))

def attr(n, t, init=None, l=1): return N("attr", l, name=n, type=t, init=init)
def formal(n, t, l=1): return N("formal", l, name=n, type=t)
def metodo(n, formais, ret, corpo, l=1):
    return N("method", l, name=n, formals=formais, return_type=ret, body=corpo)
def classe(n, pai, feats, l=1): return N("class", l, name=n, parent=pai, features=feats)
def prog(*cs): return N("program", 1, classes=list(cs))

def main_ok(corpo=None, extras=()):
    """Classe Main mínima e válida (main(): Object)."""
    return classe("Main", "IO", list(extras) + [metodo("main", [], "Object", corpo or inteiro(0))])

def analisar(p):
    a = Analyzer(A.build(p))
    a.run()
    return a

def erros(p):
    return [e.msg for e in analisar(p).errors]

falhas = 0
def teste(nome, p, esperado=None):
    """esperado=None: nenhum erro. esperado=str: algum erro contém o texto."""
    global falhas
    msgs = erros(p)
    ok = (not msgs) if esperado is None else any(esperado in m for m in msgs)
    print(("OK    " if ok else "FALHA ") + nome)
    if not ok:
        falhas += 1
        print("      esperado:", esperado, "| obtido:", msgs)


# ---------------------------------------------------------------- válidos
teste("programa válido com let, if, case, chamadas", prog(
    classe("A", "Object", []),
    classe("B", "A", []),
    classe("Main", "IO", [
        attr("x", "Int", inteiro(3)),
        metodo("main", [], "Object", bloco(
            chama_self("out_string", texto("oi")),
            let("a", "Int", inteiro(1), let("b", "Int", None, plus(obj("a"), mul(obj("b"), obj("x"))))),
            se(lt(obj("x"), inteiro(5)), novo("B"), novo("A")),
            caso(novo("B"), ramo("p", "A", obj("p")), ramo("q", "B", obj("q"))),
        )),
    ])))

teste("SELF_TYPE: copy() e new SELF_TYPE", prog(
    classe("A", "Object", [metodo("f", [], "SELF_TYPE", chama_self("copy")),
                           metodo("g", [], "SELF_TYPE", novo("SELF_TYPE"))]),
    main_ok()))

teste("override com a mesma assinatura", prog(
    classe("A", "Object", [metodo("f", [formal("x", "Int")], "Int", obj("x"))]),
    classe("B", "A", [metodo("f", [formal("x", "Int")], "Int", inteiro(1))]),
    main_ok()))

teste("atribuição subtipo -> supertipo", prog(
    classe("A", "Object", []), classe("B", "A", []),
    main_ok(extras=[attr("v", "A", novo("B"))])))

teste("método herdado de IO via classe filha", prog(
    classe("Main", "IO", [metodo("main", [], "Object", chama(novo("Main"), "out_int", inteiro(7)))])))

# ---------------------------------------------------------------- Main
teste("sem classe Main", prog(classe("A", "Object", [])), "classe Main não foi definida")
teste("Main sem método main", prog(classe("Main", "Object", [])), "não tem o método main")
teste("main com parâmetros", prog(classe("Main", "Object", [
    metodo("main", [formal("x", "Int")], "Object", inteiro(0))])), "não pode ter parâmetros")

# ---------------------------------------------------------------- herança
teste("herança circular", prog(
    classe("A", "B", [], 2), classe("B", "A", [], 3), main_ok()), "herança circular")
teste("pai não definido", prog(classe("A", "Foo", [], 2), main_ok()), "que não foi definida")
teste("herdar de Int", prog(classe("A", "Int", [], 2), main_ok()), "não pode herdar de 'Int'")
teste("classe repetida", prog(classe("A", "Object", [], 2), classe("A", "Object", [], 3), main_ok()),
      "já foi definida")
teste("redefinir classe básica", prog(classe("IO", "Object", [], 2), main_ok()), "já foi definida")

# ---------------------------------------------------------------- features
teste("atributo repetido", prog(main_ok(extras=[attr("x", "Int", None, 2), attr("x", "Int", None, 3)])),
      "atributo 'x' já foi definido")
teste("atributo redefinido na subclasse", prog(
    classe("A", "Object", [attr("x", "Int")], 2), classe("B", "A", [attr("x", "Int")], 3), main_ok()),
      "já existe na classe herdada")
teste("override com assinatura diferente", prog(
    classe("A", "Object", [metodo("f", [formal("x", "Int")], "Int", inteiro(1))], 2),
    classe("B", "A", [metodo("f", [formal("x", "String")], "Int", inteiro(1))], 3), main_ok()),
      "assinatura diferente")
teste("parâmetro repetido", prog(
    classe("A", "Object", [metodo("f", [formal("x", "Int"), formal("x", "Int")], "Int", inteiro(1))]),
    main_ok()), "repetido")
teste("tipo de atributo não definido", prog(main_ok(extras=[attr("x", "Foo")])), "tipo 'Foo' não definido")
teste("self como atributo", prog(main_ok(extras=[attr("self", "Int")])), "'self' não pode ser nome de atributo")

# ---------------------------------------------------------------- expressões
teste("soma com String", prog(main_ok(plus(inteiro(1), texto("a"), 5))), "exige operandos Int")
teste("identificador não declarado", prog(main_ok(obj("zzz", 4))), "'zzz' não declarado")
teste("atribuição de tipo errado", prog(main_ok(
    bloco(atrib("x", texto("a"), 6)), extras=[attr("x", "Int")])), "incompatível com 'Int'")
teste("atribuição a self", prog(main_ok(atrib("self", novo("Main"), 6))), "atribuir a 'self'")
teste("if com condição não Bool", prog(main_ok(se(inteiro(1), inteiro(2), inteiro(3), 7))),
      "condição do 'if'")
teste("lub no if: A/B vira A (não cabe em B)", prog(
    classe("A", "Object", []), classe("B", "A", []), classe("C", "A", []),
    main_ok(extras=[attr("v", "B", se(booleano(True), novo("B"), novo("C"), 9), 9)])),
      "incompatível com 'B'")
teste("comparação Int = String", prog(main_ok(eq(inteiro(1), texto("a"), 8))), "comparação '='")
teste("comparação de objetos é livre", prog(
    classe("A", "Object", []), main_ok(eq(novo("A"), novo("Main")))))
teste("not com Int", prog(main_ok(N("not", 3, expr=inteiro(1)))), "'not' exige operando Bool")
teste("chamada de método inexistente", prog(main_ok(chama_self("naoexiste", l=5))),
      "não definido na classe")
teste("número de argumentos errado", prog(main_ok(chama_self("out_string", l=5))), "0 argumento(s)")
teste("tipo de argumento errado", prog(main_ok(chama_self("out_string", inteiro(1), l=5))),
      "argumento 1 de 'out_string'")
teste("despacho estático válido", prog(
    classe("A", "Object", [metodo("f", [], "Int", inteiro(1))]),
    classe("B", "A", []), main_ok(estatica(novo("B"), "A", "f"))))
teste("despacho estático com tipo errado", prog(
    classe("A", "Object", [metodo("f", [], "Int", inteiro(1))]),
    main_ok(estatica(novo("Main"), "A", "f", l=6))), "não é subtipo")
teste("case com ramo repetido", prog(main_ok(
    caso(inteiro(1), ramo("a", "Int", inteiro(1)), ramo("b", "Int", inteiro(2)), l=4))), "repetido nos ramos")
teste("retorno incompatível", prog(classe("A", "Object", [
    metodo("f", [], "Int", texto("x"), 2)]), main_ok()), "incompatível com o retorno")
teste("let: init não enxerga a própria variável", prog(main_ok(
    let("a", "Int", obj("a", 3), obj("a"), 3))), "'a' não declarado")
teste("static_type é preenchido", prog(main_ok(plus(inteiro(1), inteiro(2)))))

a = analisar(prog(main_ok(plus(inteiro(1), inteiro(2)))))
corpo = a.program.classes[0].features[0].body
print(("OK    " if corpo.static_type == "Int" else "FALHA ") + "static_type do corpo = Int")
falhas += corpo.static_type != "Int"

print("\n" + ("Todos os testes passaram." if not falhas else f"{falhas} teste(s) falharam."))
raise SystemExit(1 if falhas else 0)
