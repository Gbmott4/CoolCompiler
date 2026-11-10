%{
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "cool.tab.h"

/* contador de erros definido em cool.y */
extern int error_count;

/* Antes de cada regra, guarda a linha atual em yylloc (usado pelo Bison) */
#define YY_USER_ACTION \
    yylloc.first_line = yylloc.last_line = yylineno;

int comment_depth = 0;

char string_buffer[2048];
int string_pos = 0;
int string_error = 0;

void add_char_to_string(char c) {
    if (string_pos < 1024) {
        string_buffer[string_pos++] = c;
    } else {
        string_error = 1;
    }
}
%}

%option noyywrap yylineno nounput noinput

%x COMMENT
%x STRING

%%

    /* PALAVRAS-CHAVE */

[cC][lL][aA][sS][sS]                 { return CLASS; }
[eE][lL][sS][eE]                     { return ELSE; }
[fF][iI]                             { return FI; }
[iI][fF]                             { return IF; }
[iI][nN]                             { return IN; }
[iI][nN][hH][eE][rR][iI][tT][sS]    { return INHERITS; }
[iI][sS][vV][oO][iI][dD]             { return ISVOID; }
[lL][eE][tT]                         { return LET; }
[lL][oO][oO][pP]                     { return LOOP; }
[pP][oO][oO][lL]                     { return POOL; }
[tT][hH][eE][nN]                     { return THEN; }
[wW][hH][iI][lL][eE]                 { return WHILE; }
[cC][aA][sS][eE]                     { return CASE; }
[eE][sS][aA][cC]                     { return ESAC; }
[nN][eE][wW]                         { return NEW; }
[oO][fF]                             { return OF; }
[nN][oO][tT]                         { return NOT; }


    /* BOOLEANOS */

t[rR][uU][eE] {
    yylval.str = strdup("true");
    return BOOL_CONST;
}

f[aA][lL][sS][eE] {
    yylval.str = strdup("false");
    return BOOL_CONST;
}


    /* COMENTÁRIO DE LINHA */

"--".* {
}


    /* COMENTÁRIO DE BLOCO */

"(*" {
    comment_depth = 1;
    BEGIN(COMMENT);
}

<COMMENT>"(*" {
    comment_depth++;
}

<COMMENT>"*)" {
    comment_depth--;

    if (comment_depth == 0) {
        BEGIN(INITIAL);
    }
}

<COMMENT>\n {
}

<COMMENT>. {
}

<COMMENT><<EOF>> {
    fprintf(stderr, "ERRO LEXICO (linha %d): EOF dentro de comentario\n", yylineno);
    error_count++;
    return 0;
}


    /* OPERADORES */

"<=" {
    return LE;
}

"<-" {
    return ASSIGN;
}

"=>" {
    return DARROW;
}

"+" {
    return '+';
}

"-" {
    return '-';
}

"*" {
    return '*';
}

"/" {
    return '/';
}

"<" {
    return '<';
}

"=" {
    return '=';
}

"~" {
    return '~';
}

"@" {
    return '@';
}


    /* SÍMBOLOS */

"(" {
    return '(';
}

")" {
    return ')';
}

"{" {
    return '{';
}

"}" {
    return '}';
}

";" {
    return ';';
}

":" {
    return ':';
}

"," {
    return ',';
}

"." {
    return '.';
}


    /* STRINGS */

\" {
    string_pos = 0;
    string_error = 0;
    BEGIN(STRING);
}

<STRING>\" {
    if (string_error) {
        fprintf(stderr, "ERRO LEXICO (linha %d): string maior que 1024 caracteres\n", yylineno);
        error_count++;
        BEGIN(INITIAL);
    } else {
        string_buffer[string_pos] = '\0';
        yylval.str = strdup(string_buffer);
        BEGIN(INITIAL);
        return STR_CONST;
    }
}

<STRING>\\n {
    add_char_to_string('\n');
}

<STRING>\\t {
    add_char_to_string('\t');
}

<STRING>\\b {
    add_char_to_string('\b');
}

<STRING>\\f {
    add_char_to_string('\f');
}

<STRING>\\. {
    add_char_to_string(yytext[1]);
}

<STRING>[^\\\"\n]+ {
    int i;

    for (i = 0; i < yyleng; i++) {
        add_char_to_string(yytext[i]);
    }
}

<STRING>\n {
    fprintf(stderr, "ERRO LEXICO (linha %d): newline dentro de string\n", yylineno - 1);
    error_count++;
    BEGIN(INITIAL);
}

<STRING><<EOF>> {
    fprintf(stderr, "ERRO LEXICO (linha %d): EOF dentro de string\n", yylineno);
    error_count++;
    return 0;
}


    /* INTEIROS */

[0-9]+ {
    yylval.str = strdup(yytext);
    return INT_CONST;
}


    /* IDENTIFICADORES DE OBJETO */

[a-z][A-Za-z0-9_]* {
    yylval.str = strdup(yytext);
    return OBJECT_ID;
}


    /* IDENTIFICADORES DE TIPO */

[A-Z][A-Za-z0-9_]* {
    yylval.str = strdup(yytext);
    return TYPE_ID;
}


    /* WHITESPACE */

[ \t\n\f\r\v]+ {
}


    /* ERRO LÉXICO */

. {
    fprintf(stderr, "ERRO LEXICO (linha %d): caractere invalido: %s\n", yylineno, yytext);
    error_count++;
}

%%