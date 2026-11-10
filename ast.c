#include <stdio.h>
#include <stdlib.h>
#include "ast.h"

Node *node_new(const char *kind, int line) {
    Node *n = calloc(1, sizeof(Node));
    if (!n) { fprintf(stderr, "sem memoria\n"); exit(2); }
    n->kind = kind;
    n->line = line;
    return n;
}

static Field *add_field(Node *n, const char *key, int type) {
    if (n->nfields >= MAX_FIELDS) {
        fprintf(stderr, "ast: campos demais no no '%s'\n", n->kind);
        exit(2);
    }
    Field *f = &n->fields[n->nfields++];
    f->key = key;
    f->type = type;
    return f;
}

Node *node_str(Node *n, const char *key, char *val) {
    add_field(n, key, F_STR)->str = val;
    return n;
}

Node *node_node(Node *n, const char *key, Node *child) {
    add_field(n, key, F_NODE)->node = child;
    return n;
}

Node *node_list(Node *n, const char *key, Node *head) {
    add_field(n, key, F_LIST)->node = head;
    return n;
}

Node *list_append(Node *head, Node *item) {
    if (!head) return item;
    Node *p = head;
    while (p->next) p = p->next;
    p->next = item;
    return head;
}

/* ---------- saída JSON ---------- */

static void indent(FILE *out, int d) {
    for (int i = 0; i < d; i++) fputs("  ", out);
}

static void json_string(FILE *out, const char *s) {
    fputc('"', out);
    for (; *s; s++) {
        unsigned char c = (unsigned char)*s;
        switch (c) {
            case '"':  fputs("\\\"", out); break;
            case '\\': fputs("\\\\", out); break;
            case '\n': fputs("\\n", out);  break;
            case '\t': fputs("\\t", out);  break;
            case '\r': fputs("\\r", out);  break;
            case '\b': fputs("\\b", out);  break;
            case '\f': fputs("\\f", out);  break;
            default:
                if (c < 0x20) fprintf(out, "\\u%04x", c);
                else fputc(c, out);
        }
    }
    fputc('"', out);
}

static void print_node(FILE *out, Node *n, int d) {
    fputs("{\n", out);
    indent(out, d + 1);
    fprintf(out, "\"kind\": \"%s\",\n", n->kind);
    indent(out, d + 1);
    fprintf(out, "\"line\": %d", n->line);

    for (int i = 0; i < n->nfields; i++) {
        Field *f = &n->fields[i];
        fputs(",\n", out);
        indent(out, d + 1);
        fprintf(out, "\"%s\": ", f->key);

        if (f->type == F_STR) {
            if (f->str) json_string(out, f->str); else fputs("null", out);
        } else if (f->type == F_NODE) {
            if (f->node) print_node(out, f->node, d + 1); else fputs("null", out);
        } else {
            if (!f->node) {
                fputs("[]", out);
            } else {
                fputc('[', out);
                for (Node *p = f->node; p; p = p->next) {
                    fputs(p == f->node ? "\n" : ",\n", out);
                    indent(out, d + 2);
                    print_node(out, p, d + 2);
                }
                fputc('\n', out);
                indent(out, d + 1);
                fputc(']', out);
            }
        }
    }
    fputc('\n', out);
    indent(out, d);
    fputc('}', out);
}

void ast_print_json(FILE *out, Node *root) {
    print_node(out, root, 0);
    fputc('\n', out);
}
