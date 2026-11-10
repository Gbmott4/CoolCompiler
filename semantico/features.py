"""Etapas 4 a 6: atributos, métodos, redefinições e a classe Main."""
import ast_nodes as A

from .constantes import OBJECT, SELF_TYPE
from .modelos import MethodSig


class FeaturesMixin:
    """Métodos do Analyzer que montam as tabelas de atributos e métodos."""

    # ------------------------------------------ 4. tabelas de features
    def _resolver_tipo(self, tipo, linha, permitir_self):
        if tipo == SELF_TYPE:
            if permitir_self:
                return tipo
            self.error(linha, "SELF_TYPE não pode ser usado neste contexto")
            return OBJECT
        if tipo not in self.classes:
            self.error(linha, f"tipo '{tipo}' não definido")
            return OBJECT
        return tipo

    def _montar_features(self):
        for info in self.user_classes:
            for f in info.node.features:
                if isinstance(f, A.Attr):
                    self._registrar_atributo(info, f)
                else:
                    self._registrar_metodo(info, f)

    def _registrar_atributo(self, info, f):
        if f.name == "self":
            self.error(f.line, "'self' não pode ser nome de atributo")
            return
        if f.name in info.attrs:
            self.error(f.line, f"atributo '{f.name}' já foi definido na classe '{info.name}'")
            return
        tipo = self._resolver_tipo(f.type, f.line, True)
        info.attrs[f.name] = (tipo, f.line)

    def _registrar_metodo(self, info, f):
        if f.name in info.methods:
            self.error(f.line, f"método '{f.name}' já foi definido na classe '{info.name}'")
            return
        formais, vistos = [], set()
        for fm in f.formals:
            if fm.name == "self":
                self.error(fm.line, "'self' não pode ser nome de parâmetro")
            if fm.name in vistos:
                self.error(fm.line, f"parâmetro '{fm.name}' repetido no método '{f.name}'")
            vistos.add(fm.name)
            tipo = self._resolver_tipo(fm.type, fm.line, False)
            formais.append((fm.name, tipo))
        ret = self._resolver_tipo(f.return_type, f.line, True)
        info.methods[f.name] = MethodSig(f.name, formais, ret, f.line)

    # ---------------------------------------------- 5. redefinições
    def _checar_redefinicoes(self):
        for info in self.user_classes:
            ancestrais = self._ancestrais(info.name)
            for nome, (_, linha) in info.attrs.items():
                for a in ancestrais:
                    if nome in self.classes[a].attrs:
                        self.error(linha, f"atributo '{nome}' já existe na classe herdada '{a}'")
                        break
            for nome, sig in info.methods.items():
                for a in ancestrais:
                    outro = self.classes[a].methods.get(nome)
                    if outro is None:
                        continue
                    if ([t for _, t in sig.formals] != [t for _, t in outro.formals]
                            or sig.ret != outro.ret):
                        self.error(sig.line,
                                    f"método '{nome}' redefinido com assinatura diferente da "
                                    f"classe '{a}': esperado {outro}, encontrado {sig}")
                    break

    # ------------------------------------------------------- 6. Main
    def _checar_main(self):
        main = self.classes.get("Main")
        if main is None or main.node is None:
            self.error(0, "a classe Main não foi definida")
            return
        sig = self._achar_metodo("Main", "main")
        if sig is None:
            self.error(main.line, "a classe Main não tem o método main")
        elif sig.formals:
            self.error(sig.line, "o método main não pode ter parâmetros")

    # ----------------------------------------- consultas nas tabelas
    def _todos_atributos(self, nome):
        """Atributos da classe, incluindo os herdados: nome -> tipo."""
        resultado = {}
        for c in reversed([nome] + self._ancestrais(nome)):
            for n, (t, _) in self.classes[c].attrs.items():
                resultado[n] = t
        return resultado

    def _achar_metodo(self, cls, nome):
        while cls is not None:
            sig = self.classes[cls].methods.get(nome)
            if sig is not None:
                return sig
            cls = self.classes[cls].parent
        return None
