"""Classe Analyzer: junta as etapas da análise semântica."""
from .classes import ClassesMixin
from .constantes import OBJECT
from .features import FeaturesMixin
from .modelos import SemanticError
from .tipos import TiposMixin


class Analyzer(ClassesMixin, FeaturesMixin, TiposMixin):
    def __init__(self, program):
        self.program = program
        self.errors = []
        self.classes = {}         # nome -> ClassInfo (básicas + usuário)
        self.user_classes = []    # ClassInfo das classes do usuário, na ordem do arquivo
        self.cur = OBJECT         # classe sendo verificada (para SELF_TYPE)

    # ------------------------------------------------------------ erros
    def error(self, line, msg):
        self.errors.append(SemanticError(line, msg))

    # -------------------------------------------------------------- run
    def run(self):
        self._criar_classes_basicas()
        self._registrar_classes()
        if self._checar_heranca():
            self._montar_features()
            self._checar_redefinicoes()
            self._checar_main()
            self._checar_tipos()
        self.errors.sort(key=lambda e: e.line)  
        return not self.errors

    # ----------------------------------------------------- relatório
    def info(self):
        linhas = []
        for c in self.user_classes:
            linhas.append(f"classe {c.name} herda de {c.parent}")
            for nome, (t, _) in c.attrs.items():
                linhas.append(f"    atributo {nome}: {t}")
            for sig in c.methods.values():
                linhas.append(f"    método   {sig}")
        return "\n".join(linhas)
