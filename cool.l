%{
#include <stdio.h>
#include <string.h>

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

[cC][lL][aA][sS][sS] {
    printf("CLASS\n");
}

[eE][lL][sS][eE] {
    printf("ELSE\n");
}

[fF][iI] {
    printf("FI\n");
}

[iI][fF] {
    printf("IF\n");
}

[iI][nN] {
    printf("IN\n");
}

[iI][nN][hH][eE][rR][iI][tT][sS] {
    printf("INHERITS\n");
}

[iI][sS][vV][oO][iI][dD] {
    printf("ISVOID\n");
}

[lL][eE][tT] {
    printf("LET\n");
}

[lL][oO][oO][pP] {
    printf("LOOP\n");
}

[pP][oO][oO][lL] {
    printf("POOL\n");
}

[tT][hH][eE][nN] {
    printf("THEN\n");
}

[wW][hH][iI][lL][eE] {
    printf("WHILE\n");
}

[cC][aA][sS][eE] {
    printf("CASE\n");
}

[eE][sS][aA][cC] {
    printf("ESAC\n");
}

[nN][eE][wW] {
    printf("NEW\n");
}

[oO][fF] {
    printf("OF\n");
}

[nN][oO][tT] {
    printf("NOT\n");
}


    /* BOOLEANOS */

t[rR][uU][eE] {
    printf("BOOL_CONST: true\n");
}

f[aA][lL][sS][eE] {
    printf("BOOL_CONST: false\n");
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

"+" {
    printf("PLUS\n");
}

"-" {
    printf("MINUS\n");
}

"*" {
    printf("MULT\n");
}

"/" {
    printf("DIV\n");
}

"<=" {
    printf("LE\n");
}

"<-" {
    printf("ASSIGN\n");
}

"<" {
    printf("LT\n");
}

"=" {
    printf("EQ\n");
}

"~" {
    printf("NEG\n");
}

"@" {
    printf("AT\n");
}

"=>" {
    printf("DARROW\n");
}


    /* SÍMBOLOS */

"(" {
    printf("LPAREN\n");
}

")" {
    printf("RPAREN\n");
}

"{" {
    printf("LBRACE\n");
}

"}" {
    printf("RBRACE\n");
}

";" {
    printf("SEMICOLON\n");
}

":" {
    printf("COLON\n");
}

"," {
    printf("COMMA\n");
}

"." {
    printf("DOT\n");
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
    } else {
        string_buffer[string_pos] = '\0';
        printf("STR_CONST: \"%s\"\n", string_buffer);
    }

    BEGIN(INITIAL);
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
    printf("INTEIRO: %s\n", yytext);
}


    /* IDENTIFICADORES DE OBJETO */

[a-z][A-Za-z0-9_]* {
    printf("OBJECT_ID: %s\n", yytext);
}


    /* IDENTIFICADORES DE TIPO */

[A-Z][A-Za-z0-9_]* {
    printf("TYPE_ID: %s\n", yytext);
}


    /* WHITESPACE */

[ \t\n\f\r\v]+ {
}


    /* ERRO LÉXICO */

. {
    printf("ERRO LEXICO: caractere invalido: %s\n", yytext);
}

%%

int main() {
    yylex();
    return 0;
}