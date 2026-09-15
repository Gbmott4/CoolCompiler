%{
#include <stdio.h>
#include <string.h>
#include "cool.tab.h"

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

%option noyywrap

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
    return BOOL_CONST;
}

f[aA][lL][sS][eE] {
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
    printf("ERRO: EOF dentro de comentario\n");
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
        printf("ERRO: string maior que 1024 caracteres\n");
        BEGIN(INITIAL);
    } else {
        string_buffer[string_pos] = '\0';
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
    printf("ERRO: newline dentro de string\n");
    BEGIN(INITIAL);
}

<STRING><<EOF>> {
    printf("ERRO: EOF dentro de string\n");
    return 0;
}


    /* INTEIROS */

[0-9]+ {
    return INT_CONST;
}


    /* IDENTIFICADORES DE OBJETO */

[a-z][A-Za-z0-9_]* {
    return OBJECT_ID;
}


    /* IDENTIFICADORES DE TIPO */

[A-Z][A-Za-z0-9_]* {
    return TYPE_ID;
}


    /* WHITESPACE */

[ \t\n\f\r\v]+ {
}


    /* ERRO LÉXICO */

. {
    printf("ERRO LEXICO: caractere invalido: %s\n", yytext);
}

%%