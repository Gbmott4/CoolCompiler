#!/usr/bin/env python3
import sys

import ast_nodes as A
from semantico import Analyzer


def main():
    sys.setrecursionlimit(10000)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mostrar_info = "--info" in sys.argv

    if args:
        with open(args[0], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        # o parser falhou e não imprimiu JSON; a mensagem já está no stderr dele
        sys.exit(1)

    program = A.load_ast(text)
    analyzer = Analyzer(program)
    ok = analyzer.run()

    for e in analyzer.errors:
        prefixo = f"linha {e.line}: " if e.line else ""
        print(prefixo + e.msg, file=sys.stderr)

    if not ok:
        print(f"Analise semantica falhou ({len(analyzer.errors)} erro(s)).", file=sys.stderr)
        sys.exit(1)

    if mostrar_info:
        print(analyzer.info())
    print(f"OK: analise semantica concluida ({len(program.classes)} classe(s)).", file=sys.stderr)


if __name__ == "__main__":
    main()
