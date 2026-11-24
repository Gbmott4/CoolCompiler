"""Utilitários para emitir assembly JVM na sintaxe do Jasmin."""

# Palavras que o Jasmin entende como modificadores numa linha ".field"
_PALAVRAS_JASMIN = {
    "public", "private", "protected", "static", "final", "volatile",
    "transient", "synchronized", "native", "abstract", "interface",
    "strict", "synthetic", "enum", "annotation", "bridge", "varargs",
    "from", "to", "using", "is", "default", "signature", "stack", "locals",
    "method", "field", "class", "super", "limit", "line", "var", "catch",
    "throws", "end", "source", "implements",
}


def nome_campo(nome):
    """Nome do campo JVM de um atributo COOL (evita colidir com palavras do Jasmin)."""
    return nome + "$" if nome in _PALAVRAS_JASMIN else nome


def string_jasmin(s):
    """Literal de string para a instrução ldc."""
    partes = ['"']
    for ch in s:
        c = ord(ch)
        if ch == '"':
            partes.append('\\"')
        elif ch == "\\":
            partes.append("\\\\")
        elif ch == "\n":
            partes.append("\\n")
        elif ch == "\t":
            partes.append("\\t")
        elif ch == "\r":
            partes.append("\\r")
        elif ch == "\b":
            partes.append("\\b")
        elif ch == "\f":
            partes.append("\\f")
        elif c < 0x20 or c > 0x7E:
            partes.append(f"\\u{c:04x}")
        else:
            partes.append(ch)
    partes.append('"')
    return "".join(partes)


class Metodo:
    """Corpo de um método JVM sendo montado.

    Controla a altura da pilha de operandos (para calcular .limit stack),
    o número de variáveis locais (.limit locals) e os rótulos.
    """

    def __init__(self, cabecalho, n_locais=1):
        self.cabecalho = cabecalho
        self.codigo = []
        self.altura = 0          # altura atual da pilha de operandos
        self.altura_max = 0
        self.n_locais = n_locais
        self._rotulos = 0

    def emit(self, instr, delta=0):
        """Emite uma instrução; delta = variação da pilha que ela causa."""
        self.codigo.append("    " + instr)
        self.altura += delta
        if self.altura > self.altura_max:
            self.altura_max = self.altura

    def rotulo(self):
        self._rotulos += 1
        return f"L{self._rotulos}"

    def marca(self, rotulo, altura=None):
        """Posiciona um rótulo. 'altura' redefine a altura da pilha nesse ponto
        (necessário depois de um goto, quando o código seguinte só é alcançado
        por desvio)."""
        self.codigo.append(rotulo + ":")
        if altura is not None:
            self.altura = altura

    def nova_local(self):
        n = self.n_locais
        self.n_locais += 1
        return n

    def comentario(self, texto):
        self.codigo.append("    ; " + texto)

    # ---- atalhos
    def push_int(self, v):
        if -1 <= v <= 5:
            self.emit("iconst_m1" if v == -1 else f"iconst_{v}", 1)
        elif -128 <= v <= 127:
            self.emit(f"bipush {v}", 1)
        elif -32768 <= v <= 32767:
            self.emit(f"sipush {v}", 1)
        else:
            self.emit(f"ldc {v}", 1)

    def push_str(self, s):
        self.emit("ldc " + string_jasmin(s), 1)

    def texto(self):
        linhas = [self.cabecalho,
                  f"    .limit stack {max(self.altura_max, 1)}",
                  f"    .limit locals {max(self.n_locais, 1)}"]
        linhas += self.codigo
        linhas.append(".end method")
        return "\n".join(linhas) + "\n"
