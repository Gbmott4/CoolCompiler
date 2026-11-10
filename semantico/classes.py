"""Etapas 1 a 3: classes básicas, classes do usuário e grafo de herança."""
from .constantes import OBJECT, IO, INT, STRING, BOOL, SELF_TYPE, NAO_HERDAVEIS
from .modelos import ClassInfo, MethodSig


class ClassesMixin:
    """Métodos do Analyzer.

    Usa os atributos criados em Analyzer.__init__ (classes, user_classes,
    program) e o método Analyzer.error.
    """

    # ---------------------------------------------- 1. classes básicas
    def _criar_classes_basicas(self):
        def m(nome, formais, ret):
            return MethodSig(nome, formais, ret, 0)

        obj = ClassInfo(OBJECT, None, 0)
        obj.methods = {
            "abort": m("abort", [], OBJECT),
            "type_name": m("type_name", [], STRING),
            "copy": m("copy", [], SELF_TYPE),
        }
        io = ClassInfo(IO, OBJECT, 0)
        io.methods = {
            "out_string": m("out_string", [("x", STRING)], SELF_TYPE),
            "out_int": m("out_int", [("x", INT)], SELF_TYPE),
            "in_string": m("in_string", [], STRING),
            "in_int": m("in_int", [], INT),
        }
        inteiro = ClassInfo(INT, OBJECT, 0)
        string = ClassInfo(STRING, OBJECT, 0)
        string.methods = {
            "length": m("length", [], INT),
            "concat": m("concat", [("s", STRING)], STRING),
            "substr": m("substr", [("i", INT), ("l", INT)], STRING),
        }
        booleano = ClassInfo(BOOL, OBJECT, 0)
        for c in (obj, io, inteiro, string, booleano):
            self.classes[c.name] = c

    # ------------------------------------- 2. classes do usuário
    def _registrar_classes(self):
        for c in self.program.classes:
            if c.name == SELF_TYPE:
                self.error(c.line, "SELF_TYPE não pode ser nome de classe")
                continue
            if c.name in self.classes:
                self.error(c.line, f"classe '{c.name}' já foi definida")
                continue
            info = ClassInfo(c.name, c.parent, c.line, c)
            self.classes[c.name] = info
            self.user_classes.append(info)

    # ------------------------------------------------- 3. herança
    def _checar_heranca(self):
        ok = True
        for info in self.user_classes:
            p = info.parent
            if p in NAO_HERDAVEIS:
                self.error(info.line, f"classe '{info.name}' não pode herdar de '{p}'")
                ok = False
            elif p not in self.classes:
                self.error(info.line,
                            f"classe '{info.name}' herda de '{p}', que não foi definida")
                ok = False
        if not ok:
            return False

        # ciclos: segue a cadeia de pais de cada classe
        concluidos = set()
        for info in self.user_classes:
            caminho = []
            atual = info.name
            while atual is not None and atual not in concluidos:
                if atual in caminho:
                    ciclo = caminho[caminho.index(atual):]
                    self.error(self.classes[atual].line,
                                "herança circular entre as classes: " + ", ".join(ciclo))
                    ok = False
                    break
                caminho.append(atual)
                atual = self.classes[atual].parent
            concluidos.update(caminho)
        return ok

    def _ancestrais(self, nome):
        """Pais da classe, do mais próximo até Object (sem incluir a própria)."""
        resultado = []
        atual = self.classes[nome].parent
        while atual is not None:
            resultado.append(atual)
            atual = self.classes[atual].parent
        return resultado
