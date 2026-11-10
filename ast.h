#ifndef AST_H
#define AST_H

#include <stdio.h>

/* Nó genérico da AST.
 * Cada nó tem um "kind" (ex.: "class", "plus"), a linha de origem e uma
 * lista de campos nomeados. Um campo é: string, nó filho ou lista de nós
 * (lista encadeada pelo ponteiro "next"). */

typedef struct Node Node;

enum
{
    F_STR,
    F_NODE,
    F_LIST
};

typedef struct
{
    const char *key; // nome do campo, ex.: "name"
    int type;        // F_STR vale 0, F_NODE vale 1 e F_LIST vale 2.
    char *str;
    Node *node;
} Field;

#define MAX_FIELDS 6

struct Node
{
    const char *kind; // "attr", "plus", "class"...
    int line;
    int nfields; // quantos campos já foram preenchidos
    Field fields[MAX_FIELDS];
    Node *next; /* usado só para encadear listas */
};

Node *node_new(const char *kind, int line);
Node *node_str(Node *n, const char *key, char *val);
Node *node_node(Node *n, const char *key, Node *child); /* child pode ser NULL */
Node *node_list(Node *n, const char *key, Node *head);  /* head pode ser NULL  */
Node *list_append(Node *head, Node *item);              /* retorna a cabeça    */

void ast_print_json(FILE *out, Node *root);

#endif
