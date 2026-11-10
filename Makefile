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

clean:
	rm -f cool-parser cool.tab.c cool.tab.h lex.yy.c

.PHONY: run clean
