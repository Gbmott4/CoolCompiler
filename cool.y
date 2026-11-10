%code requires {
#include "ast.h"
}

%{
#include <stdio.h>
#include <stdlib.h>
#include "ast.h"

int yylex(void);
void yyerror(const char *s);

extern FILE *yyin;
Node *build_let(Node *decl, Node *body);

Node *ast_root = NULL;   /* raiz da AST, preenchida pela regra 'program' */
int error_count = 0;     /* erros léxicos + sintáticos (usado também por cool.l) */
%}

%locations
%define parse.error verbose

%union {
    char *str;           /* lexemas: identificadores e constantes */
    struct Node *node;   /* nós da AST */
}


/* =========================
   TOKENS
   ========================= */

/* Palavras-chave da linguagem */
%token CLASS ELSE FI IF IN INHERITS ISVOID
%token LET LOOP POOL THEN WHILE CASE ESAC
%token NEW OF NOT

/* Constantes e identificadores reconhecidos pelo analisador */
%token <str> BOOL_CONST
%token <str> INT_CONST
%token <str> STR_CONST
%token <str> OBJECT_ID
%token <str> TYPE_ID

/* Operadores compostos */
%token LE      /* <= */
%token ASSIGN  /* <- */
%token DARROW  /* => */


/* =========================
   PRECEDÊNCIA
   ========================= */

/* Define a precedência e associatividade dos operadores.
   As declarações mais abaixo possuem maior precedência. */

%precedence LET_PREC     /* Precedência especial usada na expressão LET */
%right ASSIGN            /* Associativo à direita */
%right NOT
%nonassoc '<' LE '='     /* Operadores de comparação não associativos */
%left '+' '-'            /* Associativos à esquerda */
%left '*' '/'
%right ISVOID
%right '~'
%left '@'
%left '.'


%type <node> class_list class feature_list feature
%type <node> formal_list formals formal
%type <node> expr argument_list arguments expr_list
%type <node> let_list let_decl case_list case_branch


%%


/* =========================
   PROGRAMA
   ========================= */

program:
    class_list
        {
            ast_root = node_new("program", @1.first_line);
            node_list(ast_root, "classes", $1);
        }
;

class_list:
    class                 { $$ = $1; }
    | class_list class    { $$ = list_append($1, $2); }
;


/* =========================
   CLASSE
   ========================= */

/* Uma classe pode ser declarada com ou sem herança */
class:
    CLASS TYPE_ID '{' feature_list '}' ';'
        {
            $$ = node_new("class", @1.first_line);
            node_str($$, "name", $2);
            node_str($$, "parent", "Object");
            node_list($$, "features", $4);
        }
    | CLASS TYPE_ID INHERITS TYPE_ID '{' feature_list '}' ';'
        {
            $$ = node_new("class", @1.first_line);
            node_str($$, "name", $2);
            node_str($$, "parent", $4);
            node_list($$, "features", $6);
        }
;


/* =========================
   FEATURES
   ========================= */

/* Lista de atributos e métodos da classe.
   Também pode ser vazia. */
feature_list:
    /* vazio */           { $$ = NULL; }
    | feature_list feature { $$ = list_append($1, $2); }
;


/* Uma feature pode representar:
   - um atributo sem inicialização
   - um atributo com inicialização
   - um método
*/
feature:
    OBJECT_ID ':' TYPE_ID ';'
        {
            $$ = node_new("attr", @1.first_line);
            node_str($$, "name", $1);
            node_str($$, "type", $3);
            node_node($$, "init", NULL);
        }

    | OBJECT_ID ':' TYPE_ID ASSIGN expr ';'
        {
            $$ = node_new("attr", @1.first_line);
            node_str($$, "name", $1);
            node_str($$, "type", $3);
            node_node($$, "init", $5);
        }

    | OBJECT_ID '(' formal_list ')' ':' TYPE_ID
      '{' expr '}' ';'
        {
            $$ = node_new("method", @1.first_line);
            node_str($$, "name", $1);
            node_list($$, "formals", $3);
            node_str($$, "return_type", $6);
            node_node($$, "body", $8);
        }
;


/* =========================
   PARÂMETROS DE MÉTODOS
   ========================= */

/*
    soma(a : Int, b : Int) : Int {
        a + b
    };
*/

/* Um método pode não possuir parâmetros */
formal_list:
    /* vazio */   { $$ = NULL; }
    | formals     { $$ = $1; }
;

/* Permite um ou vários parâmetros separados por vírgula */
formals:
    formal                { $$ = $1; }
    | formals ',' formal  { $$ = list_append($1, $3); }
;

/* Cada parâmetro possui um nome e um tipo */
formal:
    OBJECT_ID ':' TYPE_ID
        {
            $$ = node_new("formal", @1.first_line);
            node_str($$, "name", $1);
            node_str($$, "type", $3);
        }
;


/* =========================
   EXPRESSÕES
   ========================= */

/* Define as diferentes formas de expressão permitidas pela gramática */
expr:

      /* Atribuição: x <- expressão */
      OBJECT_ID ASSIGN expr
        {
            $$ = node_new("assign", @$.first_line);
            node_str($$, "name", $1);
            node_node($$, "expr", $3);
        }


      /* Chamadas de método */
    | expr '.' OBJECT_ID '(' argument_list ')'
        {
            $$ = node_new("dispatch", @$.first_line);
            node_node($$, "object", $1);
            node_str($$, "method", $3);
            node_list($$, "args", $5);
        }
    | expr '@' TYPE_ID '.' OBJECT_ID '(' argument_list ')'
        {
            $$ = node_new("static_dispatch", @$.first_line);
            node_node($$, "object", $1);
            node_str($$, "type", $3);
            node_str($$, "method", $5);
            node_list($$, "args", $7);
        }
    | OBJECT_ID '(' argument_list ')'
        {
            /* f(x) é açúcar para self.f(x) */
            Node *self = node_new("object", @1.first_line);
            node_str(self, "name", "self");
            $$ = node_new("dispatch", @$.first_line);
            node_node($$, "object", self);
            node_str($$, "method", $1);
            node_list($$, "args", $3);
        }


      /* Estrutura condicional */
    | IF expr THEN expr ELSE expr FI
        {
            $$ = node_new("if", @$.first_line);
            node_node($$, "cond", $2);
            node_node($$, "then_branch", $4);
            node_node($$, "else_branch", $6);
        }


      /* Estrutura de repetição */
    | WHILE expr LOOP expr POOL
        {
            $$ = node_new("while", @$.first_line);
            node_node($$, "cond", $2);
            node_node($$, "body", $4);
        }


      /* Bloco contendo uma ou mais expressões */
    | '{' expr_list '}'
        {
            $$ = node_new("block", @$.first_line);
            node_list($$, "exprs", $2);
        }


      /* Declaração de variáveis locais.
         LET_PREC resolve conflitos de precedência envolvendo LET. */
    | LET let_list IN expr %prec LET_PREC
        {
            /* let a:T1, b:T2 in e  ==>  let a:T1 in (let b:T2 in e) */
            $$ = build_let($2, $4);
        }


      /* Seleção por tipos */
    | CASE expr OF case_list ESAC
        {
            $$ = node_new("case", @$.first_line);
            node_node($$, "expr", $2);
            node_list($$, "branches", $4);
        }


      /* Criação de um novo objeto */
    | NEW TYPE_ID
        {
            $$ = node_new("new", @$.first_line);
            node_str($$, "type", $2);
        }


      /* Verifica se uma expressão é void */
    | ISVOID expr
        {
            $$ = node_new("isvoid", @$.first_line);
            node_node($$, "expr", $2);
        }


      /* Operações aritméticas */
    | expr '+' expr
        {
            $$ = node_new("plus", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }
    | expr '-' expr
        {
            $$ = node_new("sub", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }
    | expr '*' expr
        {
            $$ = node_new("mul", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }
    | expr '/' expr
        {
            $$ = node_new("div", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }


      /* Complemento aritmético */
    | '~' expr
        {
            $$ = node_new("neg", @$.first_line);
            node_node($$, "expr", $2);
        }


      /* Comparações */
    | expr '<' expr
        {
            $$ = node_new("lt", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }
    | expr LE expr
        {
            $$ = node_new("leq", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }
    | expr '=' expr
        {
            $$ = node_new("eq", @$.first_line);
            node_node($$, "left", $1);
            node_node($$, "right", $3);
        }


      /* Negação lógica */
    | NOT expr
        {
            $$ = node_new("not", @$.first_line);
            node_node($$, "expr", $2);
        }


      /* Expressão entre parênteses */
    | '(' expr ')'   { $$ = $2; }


      /* Identificadores e constantes */
    | OBJECT_ID
        {
            $$ = node_new("object", @1.first_line);
            node_str($$, "name", $1);
        }
    | INT_CONST
        {
            $$ = node_new("int", @1.first_line);
            node_str($$, "value", $1);
        }
    | STR_CONST
        {
            $$ = node_new("string", @1.first_line);
            node_str($$, "value", $1);
        }
    | BOOL_CONST
        {
            $$ = node_new("bool", @1.first_line);
            node_str($$, "value", $1);
        }
;


/* =========================
   ARGUMENTOS DE MÉTODOS
   ========================= */

/* Uma chamada de método pode possuir zero ou mais argumentos */
argument_list:
    /* vazio */   { $$ = NULL; }
    | arguments   { $$ = $1; }
;

/* Argumentos são expressões separadas por vírgula */
arguments:
    expr                  { $$ = $1; }
    | arguments ',' expr  { $$ = list_append($1, $3); }
;


/* =========================
   LISTA DE EXPRESSÕES
   ========================= */

/* Usada nos blocos { ... }.
   Cada expressão do bloco deve terminar com ';'. */
expr_list:
    expr ';'              { $$ = $1; }
    | expr_list expr ';'  { $$ = list_append($1, $2); }
;


/* =========================
   LET
   ========================= */

/* Permite declarar uma ou várias variáveis no LET */
let_list:
    let_decl                  { $$ = $1; }
    | let_list ',' let_decl   { $$ = list_append($1, $3); }
;

/* Uma variável do LET pode ser declarada com ou sem expressão de inicialização */
let_decl:
    OBJECT_ID ':' TYPE_ID
        {
            $$ = node_new("let", @1.first_line);
            node_str($$, "name", $1);
            node_str($$, "type", $3);
            node_node($$, "init", NULL);
        }
    | OBJECT_ID ':' TYPE_ID ASSIGN expr
        {
            $$ = node_new("let", @1.first_line);
            node_str($$, "name", $1);
            node_str($$, "type", $3);
            node_node($$, "init", $5);
        }
;


/* =========================
   CASE
   ========================= */

/* Um CASE possui uma ou mais alternativas */
case_list:
    case_branch               { $$ = $1; }
    | case_list case_branch   { $$ = list_append($1, $2); }
;

/* Cada alternativa possui variável, tipo e expressão correspondente */
case_branch:
    OBJECT_ID ':' TYPE_ID DARROW expr ';'
        {
            $$ = node_new("branch", @1.first_line);
            node_str($$, "name", $1);
            node_str($$, "type", $3);
            node_node($$, "expr", $5);
        }
;


%%


/* =========================
   AUXILIAR: LET com várias variáveis
   ========================= */

/* Transforma a lista de declarações (ligadas por next) em lets aninhados,
   colocando 'body' dentro do último. */
Node *build_let(Node *decl, Node *body) {
    Node *rest = decl->next;
    decl->next = NULL;
    if (rest)
        body = build_let(rest, body);
    node_node(decl, "body", body);
    return decl;
}


/* =========================
   ERRO SINTÁTICO
   ========================= */

/* Executada automaticamente pelo Bison quando ocorre um erro sintático.
   Vai para stderr para não misturar com o JSON que sai em stdout. */
void yyerror(const char *s) {
    fprintf(stderr, "ERRO SINTATICO (linha %d): %s\n", yylloc.first_line, s);
    error_count++;
}


/* =========================
   MAIN
   ========================= */

/* 
Uso: ./cool-parser [arquivo.cl]
Sem argumento lê de stdin. Em caso de sucesso imprime a AST em JSON
no stdout e retorna 0; se houver qualquer erro retorna 1 sem imprimir JSON. 
*/

int main(int argc, char **argv) {

    if (argc > 1) {
        yyin = fopen(argv[1], "r");
        if (!yyin) {
            perror(argv[1]);
            return 2;
        }
    }

    int result = yyparse();

    if (result != 0 || error_count > 0 || ast_root == NULL) {
        fprintf(stderr, "Analise lexica/sintatica falhou (%d erro(s)).\n", error_count);
        return 1;
    }

    ast_print_json(stdout, ast_root);
    return 0;
}
