#!/usr/bin/env python3
"""Compilador COOL -> bytecode da JVM.

Etapas:
  1. cool-parser (C: léxico + sintático)  -> AST em JSON
  2. semantico (Python)                    -> AST com tipos
  3. codegen (Python)                      -> assembly JVM (.j, sintaxe Jasmin)
  4. Jasmin (assembler)                    -> .class

Uso:
  python3 coolc.py programa.cl            # gera out/*.j e out/*.class
  python3 coolc.py programa.cl --run      # compila e executa
  python3 coolc.py programa.cl -o pasta   # muda a pasta de saída
  python3 coolc.py programa.cl --sem-otimizacao   # desliga as otimizações
"""
import argparse
import glob
import os
import subprocess
import sys

import ast_nodes as A
from codegen import gerar
from semantico import Analyzer

RAIZ = os.path.dirname(os.path.abspath(__file__))
PARSER = os.path.join(RAIZ, "cool-parser")
JASMIN = os.path.join(RAIZ, "tools", "jasmin.jar")
RUNTIME = os.path.join(RAIZ, "runtime")


def falhar(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def compilar(arquivo, saida, otimizar=True):
    # 1. léxico + sintático
    r = subprocess.run([PARSER, arquivo], capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(1)

    # 2. semântico
    sys.setrecursionlimit(10000)
    program = A.load_ast(r.stdout)
    analyzer = Analyzer(program)
    if not analyzer.run():
        for e in analyzer.errors:
            prefixo = f"linha {e.line}: " if e.line else ""
            print(prefixo + e.msg, file=sys.stderr)
        falhar(f"Analise semantica falhou ({len(analyzer.errors)} erro(s)).")

    # 3. geração de código
    os.makedirs(saida, exist_ok=True)
    for antigo in glob.glob(os.path.join(saida, "*.j")) + glob.glob(os.path.join(saida, "*.class")):
        os.remove(antigo)
    arquivos_j = []
    for nome, texto in gerar(program, analyzer, otimizar).items():
        caminho = os.path.join(saida, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        arquivos_j.append(caminho)

    # 4. montagem (programa + runtime)
    runtime = sorted(glob.glob(os.path.join(RUNTIME, "*.j")))
    r = subprocess.run(["java", "-jar", JASMIN, "-d", saida] + runtime + arquivos_j,
                       capture_output=True, text=True)
    saida_jasmin = r.stdout + r.stderr
    linhas_erro = [l for l in saida_jasmin.splitlines()
                   if l.strip() and not l.startswith("Generated:")
                   and not l.startswith("Picked up JAVA_TOOL_OPTIONS")]
    if r.returncode != 0 or linhas_erro:
        print("\n".join(linhas_erro), file=sys.stderr)
        falhar("Erro ao montar o bytecode com o Jasmin.")

    print(f"OK: {len(arquivos_j)} classe(s) gerada(s) em {saida}/  "
          f"(execute com: java -cp {saida} Main)", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Compilador COOL para a JVM")
    ap.add_argument("arquivo", help="programa COOL (.cl)")
    ap.add_argument("-o", "--saida", default="out", help="pasta de saída (padrão: out)")
    ap.add_argument("--run", action="store_true", help="executa o programa depois de compilar")
    ap.add_argument("--sem-otimizacao", action="store_true",
                    help="gera o código sem as otimizações (para comparar)")
    args = ap.parse_args()

    compilar(args.arquivo, args.saida, not args.sem_otimizacao)
    if args.run:
        sys.stdout.flush()
        r = subprocess.run(["java", "-cp", args.saida, "Main"])
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
