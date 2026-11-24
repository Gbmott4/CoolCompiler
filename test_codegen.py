#!/usr/bin/env python3
"""Testes da geração de código: compila cada testes/*.cl, executa na JVM e
compara a saída com testes/*.esperado (a entrada padrão vem de *.entrada,
se existir). Cada programa é testado com e sem otimizações.
Rodar:  python3 test_codegen.py
"""
import glob
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))


def main():
    falhas = 0
    programas = sorted(glob.glob(os.path.join(RAIZ, "testes", "*.cl")))
    casos = [(p, modo) for p in programas for modo in ("otimizado", "sem otimizacao")]
    for prog, modo in casos:
        base = prog[:-3]
        nome = f"{os.path.basename(base)} ({modo})"
        opcoes = ["--sem-otimizacao"] if modo == "sem otimizacao" else []
        with tempfile.TemporaryDirectory() as saida:
            c = subprocess.run([sys.executable, os.path.join(RAIZ, "coolc.py"), prog, "-o", saida]
                                + opcoes, capture_output=True, text=True)
            if c.returncode != 0:
                print(f"FALHOU {nome}: erro de compilação\n{c.stderr}")
                falhas += 1
                continue
            entrada = ""
            if os.path.exists(base + ".entrada"):
                with open(base + ".entrada", encoding="utf-8") as f:
                    entrada = f.read()
            r = subprocess.run(["java", "-cp", saida, "Main"], input=entrada,
                                capture_output=True, text=True)
        with open(base + ".esperado", encoding="utf-8") as f:
            esperado = f.read()
        if r.stdout == esperado:
            erro = [l for l in r.stderr.splitlines() if not l.startswith("Picked up")]
            extra = f"   [{erro[0]}]" if erro else ""
            print(f"OK    {nome}{extra}")
        else:
            falhas += 1
            print(f"FALHOU {nome}\n--- esperado ---\n{esperado}--- obtido ---\n{r.stdout}"
                    f"--- stderr ---\n{r.stderr}")
    print()
    if falhas:
        print(f"{falhas} de {len(casos)} teste(s) falharam.")
        sys.exit(1)
    print(f"Todos os {len(casos)} testes passaram.")


if __name__ == "__main__":
    main()
