# CoolCompiler

Compilador para **COOL** (*Classroom Object-Oriented Language*), desenvolvido na disciplina de Compiladores.

O projeto implementa o *front-end* do compilador, dividido em duas linguagens:

- **Análise léxica e sintática** em C, com **Flex** e **Bison**.
- **Análise semântica** em Python.

As duas partes são programas separados que conversam por um formato intermediário: o parser em C constrói a **árvore sintática abstrata (AST)** e a imprime em **JSON**; o programa em Python lê esse JSON, reconstrói a árvore em objetos e faz a verificação semântica.

## Estado do projeto

| Fase | Situação |
|---|---|
| Análise léxica (Flex) | pronta |
| Análise sintática (Bison) e construção da AST | pronta |
| Ponte C → Python (AST em JSON) | pronta |
| Análise semântica (Python) | pronta |
| Geração de código | não implementada |

## Como funciona

```
programa.cl ─► [cool.l] ─► tokens ─► [cool.y] ─► AST em C ─► JSON ──pipe──► [semant.py] ─► resultado
                Flex                   Bison      ast.c      stdout          Python
```

1. O **lexer** (`cool.l`) quebra o texto em tokens e guarda o lexema e a linha de cada um.
2. O **parser** (`cool.y`) confere a gramática e, a cada regra reconhecida, cria os nós da AST usando as funções de `ast.c`. Os nós são criados dos filhos para a raiz.
3. Terminado o parsing, a árvore é impressa em JSON no `stdout`.
4. O **pipe** do shell liga o `stdout` do parser ao `stdin` do Python, sem arquivo intermediário.
5. O **semântico** converte o JSON em objetos (`ast_nodes.py`) e roda as verificações (`semantico/`).

Erros léxicos, sintáticos e semânticos saem no `stderr`, para não se misturarem com o JSON.

## Estrutura de arquivos

```
.
├── cool.l             # lexer (Flex)
├── cool.y             # parser (Bison) e construção da AST
├── ast.h / ast.c      # nó genérico da AST e saída em JSON
├── ast_nodes.py       # classes Python da AST e carregador do JSON
├── semant.py          # ponto de entrada da análise semântica
├── semantico/         # lógica da análise semântica
│   ├── analisador.py  #   classe Analyzer: estado, erros e run()
│   ├── classes.py     #   classes básicas, classes do usuário, herança
│   ├── features.py    #   atributos, métodos, redefinições, Main
│   ├── tipos.py       #   checagem de tipos das expressões
│   ├── modelos.py     #   ClassInfo, MethodSig, Scope, SemanticError
│   └── constantes.py  #   nomes de tipos e tabelas fixas
├── test_semant.py     # testes do analisador semântico
├── exemplo.cl         # programa COOL de exemplo
├── erro.cl            # programa COOL com erros semânticos
└── Makefile
```

Os arquivos gerados (`cool.tab.c`, `cool.tab.h`, `lex.yy.c`, `cool-parser`) não são versionados: o `make` os recria.

## Requisitos

- `gcc`
- `flex`
- `bison` 3.0 ou superior (a gramática usa `%precedence`)
- `make`
- `python3` 3.8 ou superior

No Ubuntu/Debian (ou WSL):

```bash
sudo apt install build-essential flex bison python3
```

## Como usar

```bash
make                      # compila o parser (gera ./cool-parser)
make run ARQ=exemplo.cl   # parser + análise semântica
make clean                # apaga os arquivos gerados
```

Também é possível rodar cada parte separadamente:

```bash
./cool-parser exemplo.cl                       # imprime a AST em JSON
./cool-parser exemplo.cl > ast.json            # grava o JSON em arquivo
python3 semant.py ast.json                     # análise semântica a partir do JSON
python3 semant.py ast.json --info              # também lista classes, atributos e métodos
./cool-parser exemplo.cl | python3 semant.py   # os dois ligados por pipe
```

Para rodar os testes do analisador semântico (não precisam do parser):

```bash
python3 test_semant.py
```

### Códigos de saída

| Programa | Código | Significado |
|---|---|---|
| `cool-parser` | 0 | sucesso (JSON impresso) |
| `cool-parser` | 1 | erro léxico ou sintático (nenhum JSON é impresso) |
| `cool-parser` | 2 | arquivo não pôde ser aberto |
| `semant.py` | 0 | nenhum erro semântico |
| `semant.py` | 1 | erro semântico, ou entrada vazia (o parser falhou) |

## O que o analisador semântico verifica

Em ordem, as etapas do `Analyzer.run()`:

1. **Classes básicas**: cria `Object`, `IO`, `Int`, `String` e `Bool` com seus métodos.
2. **Classes do usuário**: classe repetida, redefinição de classe básica, `SELF_TYPE` como nome de classe.
3. **Herança**: pai não definido, herança de `Int`, `String` ou `Bool`, ciclos.
4. **Tabelas** de atributos e métodos de cada classe: nomes repetidos, parâmetros repetidos, `self` como nome, tipos não definidos.
5. **Redefinições**: atributo que já existe na classe herdada, método sobrescrito com assinatura diferente.
6. **`Main`**: a classe deve existir e ter o método `main` sem parâmetros.
7. **Tipos das expressões**: atribuição, chamadas (normal, estática e implícita), `if`, `while`, blocos, `let`, `case`, `new`, `isvoid`, operadores aritméticos e de comparação, `not` e `~`. Usa o menor ancestral comum (*join*) para `if` e `case`, trata `SELF_TYPE` e escopos aninhados, e preenche o `static_type` de cada nó.

Se a herança estiver inválida, as etapas seguintes são puladas para evitar erros em cascata. Os erros são acumulados (a análise não para no primeiro) e mostrados em ordem de linha.

### Exemplo

```
class Main {
  main() : Object { 1 + "a" };
};
```

Salvando o programa acima como `soma_errada.cl`:

```
$ ./cool-parser soma_errada.cl | python3 semant.py
linha 2: operador '+' exige operandos Int, mas recebeu 'Int' e 'String'
Analise semantica falhou (1 erro(s)).
```

## Formato da AST em JSON

Todo nó tem `kind` (o tipo do nó) e `line` (a linha de origem), seguidos dos campos próprios do tipo. Exemplo, para `x : Int <- 3;`:

```json
{
  "kind": "attr",
  "line": 2,
  "name": "x",
  "type": "Int",
  "init": { "kind": "int", "line": 2, "value": "3" }
}
```

<details>
<summary>Campos de cada tipo de nó</summary>

| kind | Campos |
|---|---|
| `program` | `classes` |
| `class` | `name`, `parent`, `features` |
| `attr` | `name`, `type`, `init` (nó ou `null`) |
| `method` | `name`, `formals`, `return_type`, `body` |
| `formal` | `name`, `type` |
| `assign` | `name`, `expr` |
| `dispatch` | `object`, `method`, `args` |
| `static_dispatch` | `object`, `type`, `method`, `args` |
| `if` | `cond`, `then_branch`, `else_branch` |
| `while` | `cond`, `body` |
| `block` | `exprs` |
| `let` | `name`, `type`, `init` (nó ou `null`), `body` |
| `case` | `expr`, `branches` |
| `branch` | `name`, `type`, `expr` |
| `new` | `type` |
| `isvoid`, `neg`, `not` | `expr` |
| `plus`, `sub`, `mul`, `div`, `lt`, `leq`, `eq` | `left`, `right` |
| `object` | `name` (inclui `self`) |
| `int`, `string`, `bool` | `value` |

</details>

O parser já resolve alguns açúcares sintáticos, para o analisador semântico lidar com menos casos:

- classe sem `inherits` recebe `parent` igual a `Object`;
- `f(x)` vira uma chamada em `self` (equivale a `self.f(x)`);
- `let a:T1, b:T2 in e` vira `let`s aninhados;
- parênteses não geram nó.

## Decisões de projeto

- **JSON como interface** entre C e Python: mantém as partes independentes, é fácil de inspecionar e depurar, e dispensa bibliotecas de ligação entre as duas linguagens.
- **Nó genérico em C**: uma única função recursiva imprime qualquer tipo de nó.
- **Linha em todo nó**: permite reportar os erros semânticos na posição certa.
- **`stdout` só com o JSON, `stderr` com as mensagens**: permite usar pipe sem contaminar os dados.

## Limitações

- O parser para no primeiro erro sintático (não há recuperação de erros).
- O formato das mensagens de erro é próprio deste projeto e não replica o do compilador de referência do COOL.
- A geração de código ainda não foi implementada.

---

Projeto acadêmico, desenvolvido por [@Gbmott4](https://github.com/Gbmott4).
