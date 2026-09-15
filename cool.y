%{
#include <stdio.h>

int yylex(void);
void yyerror(const char *s);
%}


/* =========================
   TOKENS
   ========================= */

%token CLASS ELSE FI IF IN INHERITS ISVOID
%token LET LOOP POOL THEN WHILE CASE ESAC
%token NEW OF NOT

%token BOOL_CONST
%token INT_CONST
%token STR_CONST
%token OBJECT_ID
%token TYPE_ID

%token LE
%token ASSIGN
%token DARROW


/* =========================
   PRECEDÊNCIA
   ========================= */

%precedence LET_PREC
%right ASSIGN
%right NOT
%nonassoc '<' LE '='
%left '+' '-'
%left '*' '/'
%right ISVOID
%right '~'
%left '@'
%left '.'


%%


/* =========================
   PROGRAMA
   ========================= */

program:
    class_list
;


/* =========================
   LISTA DE CLASSES
   ========================= */

class_list:
    class
    | class_list class
;


/* =========================
   CLASSE
   ========================= */

class:
    CLASS TYPE_ID '{' feature_list '}' ';'
    | CLASS TYPE_ID INHERITS TYPE_ID '{' feature_list '}' ';'
;


/* =========================
   FEATURES
   ========================= */

feature_list:
    /* vazio */
    | feature_list feature
;


/* Uma feature pode ser:
   - atributo
   - método
*/

feature:
    OBJECT_ID ':' TYPE_ID ';'

    | OBJECT_ID ':' TYPE_ID ASSIGN expr ';'

    | OBJECT_ID '(' formal_list ')' ':' TYPE_ID
      '{' expr '}' ';'
;


/* =========================
   PARÂMETROS DE MÉTODOS
   ========================= */

formal_list:
    /* vazio */
    | formals
;

formals:
    formal
    | formals ',' formal
;

formal:
    OBJECT_ID ':' TYPE_ID
;


/* =========================
   EXPRESSÕES
   ========================= */

expr:

      /* Atribuição */

      OBJECT_ID ASSIGN expr


      /* Chamada de método */

    | expr '.' OBJECT_ID '(' argument_list ')'

    | expr '@' TYPE_ID '.' OBJECT_ID '(' argument_list ')'

    | OBJECT_ID '(' argument_list ')'


      /* IF */

    | IF expr THEN expr ELSE expr FI


      /* WHILE */

    | WHILE expr LOOP expr POOL


      /* Bloco */

    | '{' expr_list '}'


      /* LET */

    | LET let_list IN expr %prec LET_PREC


      /* CASE */

    | CASE expr OF case_list ESAC


      /* NEW */

    | NEW TYPE_ID


      /* ISVOID */

    | ISVOID expr


      /* Operações aritméticas */

    | expr '+' expr

    | expr '-' expr

    | expr '*' expr

    | expr '/' expr


      /* Negação */

    | '~' expr


      /* Comparações */

    | expr '<' expr

    | expr LE expr

    | expr '=' expr


      /* NOT */

    | NOT expr


      /* Parênteses */

    | '(' expr ')'


      /* Identificadores e constantes */

    | OBJECT_ID

    | INT_CONST

    | STR_CONST

    | BOOL_CONST
;


/* =========================
   ARGUMENTOS DE MÉTODOS
   ========================= */

argument_list:
    /* vazio */
    | arguments
;

arguments:
    expr
    | arguments ',' expr
;


/* =========================
   LISTA DE EXPRESSÕES
   ========================= */

expr_list:
    expr ';'
    | expr_list expr ';'
;


/* =========================
   LET
   ========================= */

let_list:
    let_decl
    | let_list ',' let_decl
;

let_decl:
    OBJECT_ID ':' TYPE_ID
    | OBJECT_ID ':' TYPE_ID ASSIGN expr
;


/* =========================
   CASE
   ========================= */

case_list:
    case_branch
    | case_list case_branch
;

case_branch:
    OBJECT_ID ':' TYPE_ID DARROW expr ';'
;


%%


/* =========================
   ERRO SINTÁTICO
   ========================= */

void yyerror(const char *s) {
    printf("ERRO SINTATICO: %s\n", s);
}


/* =========================
   MAIN
   ========================= */

int main() {

    if (yyparse() == 0) {
        printf("Analise sintatica concluida com sucesso.\n");
    }

    return 0;
}