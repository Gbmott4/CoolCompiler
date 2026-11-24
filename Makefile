CC = gcc
CFLAGS = -Wall -g

cool-parser: cool.tab.c lex.yy.c ast.c ast.h
	$(CC) $(CFLAGS) -o $@ cool.tab.c lex.yy.c ast.c

cool.tab.c cool.tab.h: cool.y ast.h
	bison -d cool.y

lex.yy.c: cool.l cool.tab.h
	flex cool.l

# make run ARQ=exemplo.cl
run: cool-parser
	./cool-parser $(ARQ) | python3 semant.py

# make compile ARQ=exemplo.cl  -> gera out/*.j (assembly JVM) e out/*.class
compile: cool-parser
	python3 coolc.py $(ARQ)

# make exec ARQ=exemplo.cl     -> compila e executa na JVM
exec: cool-parser
	python3 coolc.py $(ARQ) --run

test: cool-parser
	python3 test_semant.py
	python3 test_codegen.py

clean:
	rm -f cool-parser cool.tab.c cool.tab.h lex.yy.c
	rm -rf out

.PHONY: run compile exec test clean
