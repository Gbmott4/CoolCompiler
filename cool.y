%{
#include <stdio.h>

int yylex(void);
void yyerror(const char *s);
%}


/* =========================
   TOKENS
   ========================= */

/* Palavras-chave da linguagem */
%token CLASS ELSE FI IF IN INHERITS ISVOID
%token LET LOOP POOL THEN WHILE CASE ESAC
%token NEW OF NOT

/* Constantes e identificadores reconhecidos pelo analisador */
%token BOOL_CONST
%token INT_CONST
%token STR_CONST
%token OBJECT_ID
%token TYPE_ID

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


%%


/* =========================
   PROGRAMA
   ========================= */

program:
    class_list
;

class_list:
    class
    | class_list class
;


/* =========================
   CLASSE
   ========================= */

/* Uma classe pode ser declarada com ou sem herança */
class:
    CLASS TYPE_ID '{' feature_list '}' ';'
    | CLASS TYPE_ID INHERITS TYPE_ID '{' feature_list '}' ';'
;


/* =========================
   FEATURES
   ========================= */

/* Lista de atributos e métodos da classe.
   Também pode ser vazia. */
feature_list:
    /* vazio */
    | feature_list feature
;


/* Uma feature pode representar:
   - um atributo sem inicialização
   - um atributo com inicialização
   - um método
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

/* Um método pode não possuir parâmetros */
formal_list:
    /* vazio */
    | formals
;

/* Permite um ou vários parâmetros separados por vírgula */
formals:
    formal
    | formals ',' formal
;

/* Cada parâmetro possui um nome e um tipo */
formal:
    OBJECT_ID ':' TYPE_ID
;


/* =========================
   EXPRESSÕES
   ========================= */

/* Define as diferentes formas de expressão permitidas pela gramática */
expr:

      /* Atribuição: x <- expressão */
      OBJECT_ID ASSIGN expr


      /* Chamadas de método */
    | expr '.' OBJECT_ID '(' argument_list ')'
    | expr '@' TYPE_ID '.' OBJECT_ID '(' argument_list ')'
    | OBJECT_ID '(' argument_list ')'


      /* Estrutura condicional */
    | IF expr THEN expr ELSE expr FI


      /* Estrutura de repetição */
    | WHILE expr LOOP expr POOL


      /* Bloco contendo uma ou mais expressões */
    | '{' expr_list '}'


      /* Declaração de variáveis locais.
         LET_PREC resolve conflitos de precedência envolvendo LET. */
    | LET let_list IN expr %prec LET_PREC


      /* Seleção por tipos */
    | CASE expr OF case_list ESAC


      /* Criação de um novo objeto */
    | NEW TYPE_ID


      /* Verifica se uma expressão é void */
    | ISVOID expr


      /* Operações aritméticas */
    | expr '+' expr
    | expr '-' expr
    | expr '*' expr
    | expr '/' expr


      /* Complemento aritmético */
    | '~' expr


      /* Comparações */
    | expr '<' expr
    | expr LE expr
    | expr '=' expr


      /* Negação lógica */
    | NOT expr


      /* Expressão entre parênteses */
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

/* Uma chamada de método pode possuir zero ou mais argumentos */
argument_list:
    /* vazio */
    | arguments
;

/* Argumentos são expressões separadas por vírgula */
arguments:
    expr
    | arguments ',' expr
;


/* =========================
   LISTA DE EXPRESSÕES
   ========================= */

/* Usada nos blocos { ... }.
   Cada expressão do bloco deve terminar com ';'. */
expr_list:
    expr ';'
    | expr_list expr ';'
;


/* =========================
   LET
   ========================= */

/* Permite declarar uma ou várias variáveis no LET */
let_list:
    let_decl
    | let_list ',' let_decl
;

/* Uma variável do LET pode ser declarada com ou sem expressão de inicialização */
let_decl:
    OBJECT_ID ':' TYPE_ID
    | OBJECT_ID ':' TYPE_ID ASSIGN expr
;


/* =========================
   CASE
   ========================= */

/* Um CASE possui uma ou mais alternativas */
case_list:
    case_branch
    | case_list case_branch
;

/* Cada alternativa possui variável, tipo e expressão correspondente */
case_branch:
    OBJECT_ID ':' TYPE_ID DARROW expr ';'
;


%%


/* =========================
   ERRO SINTÁTICO
   ========================= */

/* Executada automaticamente pelo Bison quando ocorre um erro sintático */
void yyerror(const char *s) {
    printf("ERRO SINTATICO: %s\n", s);
}


/* =========================
   MAIN
   ========================= */

int main() {

    /* yyparse inicia a análise sintática.
       Retorna 0 quando a entrada é aceita pela gramática. */
    if (yyparse() == 0) {
        printf("Analise sintatica concluida com sucesso.\n");
    }

    return 0;
}