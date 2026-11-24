# CoolCompiler

Compilador completo da linguagem **COOL** (*Classroom Object-Oriented Language*), desenvolvido na disciplina de Compiladores, que gera **bytecode da Java Virtual Machine**. O programa COOL passa pelas análises léxica, sintática e semântica, é traduzido para assembly da JVM (sintaxe do assembler **Jasmin**) e montado em arquivos `.class`, que rodam em qualquer JVM.

> **Não é transpilação.** Em nenhuma etapa é gerado código Java. O compilador emite instruções da máquina virtual (`iload`, `iadd`, `invokevirtual`, `getfield`…), e o Jasmin apenas converte esse texto no formato binário `.class`, assim como o `as` faz com assembly de x86. Até o runtime (as classes básicas do COOL) foi escrito à mão em assembly da JVM.

## Estado do projeto

| Fase | Situação |
|---|---|
| Análise léxica (Flex) | pronta |
| Análise sintática (Bison) e construção da AST | pronta |
| Ponte C → Python (AST em JSON) | pronta |
| Análise semântica (Python) | pronta |
| Geração de código para a JVM (Python + Jasmin) | pronta |
| Otimizações | prontas |

---

## Sumário

1. [Requisitos](#requisitos)
2. [Como usar](#como-usar)
3. [Arquitetura](#arquitetura)
4. [Etapa 1 — Análise léxica](#etapa-1--análise-léxica-cooll)
5. [Etapa 2 — Análise sintática](#etapa-2--análise-sintática-cooly)
6. [Etapa 3 — Análise semântica](#etapa-3--análise-semântica-semantico)
7. [Etapa 4 — Geração de código](#etapa-4--geração-de-código-codegen)
8. [Runtime](#runtime-runtime)
9. [Otimizações](#otimizações)
10. [Erros em tempo de execução](#erros-em-tempo-de-execução)
11. [Testes](#testes)
12. [Estrutura dos arquivos](#estrutura-dos-arquivos)
13. [Decisões de projeto](#decisões-de-projeto)
14. [Limitações conhecidas](#limitações-conhecidas)

---

## Requisitos

Testado no Ubuntu (WSL).

| Ferramenta | Para quê | Instalação |
|---|---|---|
| `gcc`, `make`, `flex`, `bison` (3.0+, a gramática usa `%precedence`) | compilar o analisador léxico/sintático | `sudo apt install build-essential flex bison` |
| `python3` (3.8+) | análise semântica e geração de código | `sudo apt install python3` |
| JDK 8+ | executar o Jasmin e os programas gerados (o `javap` ajuda a inspecionar os `.class`) | `sudo apt install openjdk-21-jdk-headless` |
| Jasmin 2.4 | assembler da JVM | já incluído em `tools/jasmin.jar` |

---

## Como usar

```bash
make                         # compila o cool-parser (léxico + sintático, em C)

make exec ARQ=exemplo.cl     # compila o programa COOL e executa
make compile ARQ=exemplo.cl  # só compila: gera out/*.j (assembly) e out/*.class
make test                    # roda todos os testes (semântico + geração de código)
make run ARQ=exemplo.cl      # só até a análise semântica
make clean                   # apaga os arquivos gerados
```

Ou diretamente com o driver:

```bash
python3 coolc.py programa.cl                    # gera out/*.j e out/*.class
python3 coolc.py programa.cl --run              # compila e executa
python3 coolc.py programa.cl -o pasta           # muda a pasta de saída
python3 coolc.py programa.cl --sem-otimizacao   # desliga as otimizações (para comparar)

java -cp out Main                               # executa um programa já compilado
javap -c -cp out Main                           # mostra o bytecode de uma classe
```

Também é possível rodar só as primeiras etapas, separadamente:

```bash
./cool-parser exemplo.cl                       # imprime a AST em JSON
./cool-parser exemplo.cl > ast.json            # grava o JSON em arquivo
python3 semant.py ast.json                     # análise semântica a partir do JSON
python3 semant.py ast.json --info              # também lista classes, atributos e métodos
./cool-parser exemplo.cl | python3 semant.py   # os dois ligados por pipe
```

Exemplo:

```
$ make exec ARQ=exemplo.cl
OK: 3 classe(s) gerada(s) em out/  (execute com: java -cp out Main)
5 4 3 2 1
4 3 2 1
3 2 1
2 1
1
```

### Códigos de saída

| Programa | Código | Significado |
|---|---|---|
| `cool-parser` | 0 | sucesso (JSON impresso) |
| `cool-parser` | 1 | erro léxico ou sintático (nenhum JSON é impresso) |
| `cool-parser` | 2 | o arquivo não pôde ser aberto |
| `semant.py` | 0 | nenhum erro semântico |
| `semant.py` | 1 | erro semântico, ou entrada vazia (o parser falhou) |
| `coolc.py` | 0 | compilação concluída |
| `coolc.py` | 1 | erro em alguma etapa (léxica, sintática, semântica ou montagem) |
| programa compilado | 0 | execução normal |
| programa compilado | 1 | erro em tempo de execução ou `abort()` |

Erros léxicos, sintáticos e semânticos saem no `stderr`, para não se misturarem com o JSON no `stdout`.

---

## Arquitetura

```
 programa.cl
     │
     ▼
 ┌────────────────────────────┐
 │ cool-parser  (C)           │  léxico (Flex) + sintático (Bison)
 └────────────────────────────┘
     │  AST em JSON (stdout)
     ▼
 ┌────────────────────────────┐
 │ ast_nodes.py  (Python)     │  JSON → objetos da AST
 └────────────────────────────┘
     ▼
 ┌────────────────────────────┐
 │ semantico/   (Python)      │  classes, herança, escopos, tipos
 └────────────────────────────┘
     │  AST com tipos (static_type em cada expressão)
     ▼
 ┌────────────────────────────┐
 │ codegen/     (Python)      │  AST tipada → assembly JVM + otimizações
 └────────────────────────────┘
     │  out/*.j        (+ runtime/*.j)
     ▼
 ┌────────────────────────────┐
 │ Jasmin                     │  assembler: .j → .class
 └────────────────────────────┘
     │  out/*.class
     ▼
   java -cp out Main
```

O `coolc.py` encadeia todas as etapas e para na primeira que encontrar erro.

A fronteira entre C e Python é a AST em **JSON**: o parser escreve a árvore na saída padrão e o Python a reconstrói. Assim, cada parte fica na linguagem mais adequada: Flex/Bison para a gramática, Python para as análises sobre a árvore.

---

## Etapa 1 — Análise léxica (`cool.l`)

Escrita com **Flex**. Reconhece:

- palavras-chave (sem distinção de maiúsculas, exceto `true`/`false`, que precisam começar com minúscula);
- identificadores de tipo (`TYPE_ID`, com inicial maiúscula) e de objeto (`OBJECT_ID`, com inicial minúscula);
- constantes inteiras, strings e booleanas;
- operadores, incluindo os compostos `<-`, `<=` e `=>`;
- comentários de linha (`-- ...`) e de bloco (`(* ... *)`), com **aninhamento** (um contador de profundidade).

Nas strings, as sequências de escape (`\n`, `\t`, `\b`, `\f`, `\"`…) já são convertidas para os caracteres reais.

**Erros léxicos detectados:** string com mais de 1024 caracteres, quebra de linha dentro de string, fim de arquivo dentro de string ou de comentário, e caracteres inválidos. Cada erro mostra a linha.

## Etapa 2 — Análise sintática (`cool.y`)

Escrita com **Bison**, cobrindo a gramática completa do COOL, com as precedências e associatividades de operadores do manual da linguagem. Mensagens de erro em modo `verbose`, com a linha.

Durante o reconhecimento, a gramática monta a **AST** com os nós genéricos de `ast.c`/`ast.h`. Cada nó tem um tipo (`kind`), a linha de origem e campos nomeados. Algumas simplificações já acontecem aqui:

- `let` com várias variáveis vira uma sequência de `let`s aninhados;
- uma classe sem `inherits` recebe `Object` como pai;
- uma chamada sem objeto, `f(x)`, vira `self.f(x)`;
- parênteses não geram nó.

Ao final, a árvore é impressa em JSON (`ast_print_json`). O parser para no primeiro erro sintático.

### Formato da AST em JSON

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

## Etapa 3 — Análise semântica (`semantico/`)

Escrita em Python, organizada em etapas (uma classe `Analyzer` composta por *mixins*):

| Arquivo | O que verifica |
|---|---|
| `classes.py` | Cria as classes básicas (Object, IO, Int, String, Bool e seus métodos). Registra as classes do usuário: classe redefinida, `SELF_TYPE` ou nome reservado do runtime como nome de classe. Valida a herança: pai inexistente, herança de Int/String/Bool, **ciclos**. |
| `features.py` | Monta as tabelas de atributos e métodos: nomes duplicados, `self` como nome, parâmetros repetidos, tipos inexistentes. Verifica **redefinições**: atributo herdado redeclarado, método sobrescrito com assinatura diferente. Verifica a classe `Main` e o método `main()`. |
| `tipos.py` | **Checagem de tipos** de todas as expressões, com escopos (atributos, parâmetros, `let`, `case`): conformidade (subtipagem), menor ancestral comum (`if` e `case`), `SELF_TYPE`, despacho dinâmico e estático, aritmética e comparações, constantes inteiras fora do intervalo de 32 bits. Preenche `static_type` em cada nó da AST, que é a informação usada pela geração de código. |

Se a herança estiver inválida, as etapas seguintes são puladas para evitar erros em cascata. Os erros são acumulados (a análise não para no primeiro), ordenados por linha e mostrados com a mensagem em português.

```
class Main {
  main() : Object { 1 + "a" };
};
```

```
$ ./cool-parser soma_errada.cl | python3 semant.py
linha 2: operador '+' exige operandos Int, mas recebeu 'Int' e 'String'
Analise semantica falhou (1 erro(s)).
```

## Etapa 4 — Geração de código (`codegen/`)

Percorre a AST tipada e gera um arquivo `.j` (assembly JVM, sintaxe Jasmin) por classe COOL.

### Representação dos valores

| COOL | JVM |
|---|---|
| `Int` | `int` |
| `Bool` | `int` (0 = false, 1 = true) |
| `String` | `java/lang/String` |
| Object, IO, classes do usuário | referência (classe `CoolObject` e subclasses) |
| `void` | `null` |

**Encaixotamento (boxing):** em COOL, um Int pode ser guardado numa variável do tipo Object (`x : Object <- 42`), mas na JVM um `int` não é uma referência. Quando um Int, Bool ou String vai para um lugar do tipo Object, ele é embrulhado num objeto `CoolInt`, `CoolBool` ou `CoolString`. No `case`, o caminho inverso desembrulha o valor. Quem decide isso é a função `_converter(de, para)`, a partir dos tipos estáticos.

### Mapeamento COOL → JVM

| COOL | JVM |
|---|---|
| classe `C inherits P` | `.class public C` / `.super P` (herança da própria JVM) |
| atributo | campo (`getfield` / `putfield`) |
| método `m` | `static m$s(C self, ...)` com o corpo + `m(...)` virtual que chama `m$s` |
| despacho dinâmico `e.m()` | `invokevirtual C/m` (a JVM escolhe a versão pela classe real do objeto) |
| despacho estático `e@T.m()` | `invokestatic D/m$s`, onde `D` é a classe que define `m` a partir de `T` |
| `new C` | `new C` + `<init>()` (valores padrão) + `$init_C()` (inicializadores) |
| `new SELF_TYPE` | método virtual `$new()`, que cada classe implementa |
| parâmetros, `let`, variáveis do `case` | variáveis locais da JVM (*slots*) |
| `if` / `while` | desvios condicionais (`ifeq`, `if_icmpge`…) e `goto` |
| `case` | testes `instanceof`, da classe mais específica para a mais geral |
| `isvoid e` | `ifnull` |

**Por que dois métodos JVM por método COOL?** O despacho dinâmico precisa de um método virtual, para o polimorfismo funcionar com `invokevirtual`. O despacho estático (`e@T.m()`) precisa chamar exatamente a versão de `T`, mesmo que o objeto seja de uma subclasse. Com o corpo num método estático, basta um `invokestatic`. A alternativa da JVM (`invokespecial`) só é permitida dentro de subclasses e esbarra no verificador.

**Inicialização dos objetos:** o construtor JVM `<init>()` só atribui os valores padrão (0, `""` ou `null`). Depois, `$init_C()` executa os inicializadores dos atributos, chamando antes o `$init` da classe pai. Isso segue a semântica do COOL: todos os atributos recebem o valor padrão antes de qualquer inicializador rodar, e os inicializadores rodam do pai para o filho, na ordem do arquivo.

**Ordem de avaliação:** em COOL, os argumentos de `e.f(a, b)` são avaliados **antes** do objeto `e`. Como a JVM exige o objeto embaixo dos argumentos na pilha, os argumentos são avaliados primeiro e guardados em variáveis locais temporárias (exceto quando o objeto é `self`, caso em que a ordem não faz diferença).

**Ponto de entrada:** a classe `Main` ganha o `public static main(String[])` exigido pela JVM. Ele executa `(new Main).main()` numa thread com pilha de 32 MB. A pilha padrão da JVM estoura com cerca de 200 mil chamadas recursivas; com 32 MB, aguenta cerca de 1 milhão.

**Pilha e variáveis locais:** todo método JVM precisa declarar `.limit stack` e `.limit locals`. A classe `Metodo` (`codegen/jvm.py`) acompanha a variação da pilha causada por cada instrução emitida e calcula esses valores automaticamente.

### Exemplo de código gerado

```cool
class Cons inherits List {
   car : Int;
   cdr : List;
   head() : Int { car };
   ...
};
```

```
.class public Cons
.super List

.field public car I
.field public cdr LList;

; metodo head(): Int
.method public static head$s(LCons;)I
    .limit stack 1
    .limit locals 1
    aload_0
    getfield Cons/car I
    ireturn
.end method

.method public head()I
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic Cons/head$s(LCons;)I
    ireturn
.end method
```

---

## Runtime (`runtime/`)

As classes básicas do COOL, escritas **à mão em assembly da JVM** e montadas junto com cada programa:

| Arquivo | Conteúdo |
|---|---|
| `CoolObject.j` | Classe Object do COOL: `abort()`, `type_name()`, `copy()` (cópia rasa via `clone`) |
| `IO.j` | `out_string`, `out_int`, `in_string`, `in_int` |
| `CoolInt.j`, `CoolBool.j`, `CoolString.j` | as "caixas" de Int, Bool e String (comparação por valor e `type_name` corretos) |
| `CoolRuntime.j` | rotinas de suporte: erros de execução, checagem de void, divisão, `substr` com checagem de limites, igualdade entre objetos, leitura da entrada |

Assim como as classes do usuário, os métodos de Object e IO têm a versão estática `m$s`. Por isso o despacho estático funciona também para eles: `(new A)@Object.type_name()` chama o `type_name` original, mesmo que `A` o sobrescreva.

---

## Otimizações

Ligadas por padrão; desligue com `--sem-otimizacao` para comparar o código gerado.

1. **Constant folding:** expressões só com constantes são calculadas na compilação (`2 + 3 * 4` vira `14`), com a aritmética de 32 bits da JVM. `if` e `while` com condição constante geram só o que pode ser executado. A divisão por zero não é calculada antes, para que o erro aconteça na execução.
2. **Valores descartados:** em blocos e no corpo do `while`, as atribuições não fazem `dup`/`pop`, e expressões sem efeito colateral (`42;`, `x;`) não geram código.
3. **Desvios diretos:** em `if`/`while`, comparações viram um único desvio (`a < b` → `if_icmpge`), sem calcular 0/1 antes. O mesmo vale para `<=`, `=` entre inteiros, `not` e `isvoid`.
4. **Instruções curtas:** `iload_1`/`astore_2` no lugar das formas longas, e `iinc` para `x <- x + c`.

**Resultado (número de instruções geradas):**

| Programa | Sem otimização | Otimizado | Redução |
|---|---|---|---|
| `testes/otimizacao.cl` | 305 | 196 | 36% |
| `testes/aritmetica.cl` | 189 | 130 | 31% |
| `exemplo.cl` | 231 | 221 | 4% |
| `testes/objetos.cl` | 444 | 430 | 3% |

Programas formados quase só por chamadas de método têm pouco a simplificar.

**Antes e depois** (laço do `fib`, em `testes/aritmetica.cl`):

```
; sem otimização                  ; otimizado
L1:                               L1:
    iload 4                           iload 4
    iload 1                           iload_1
    if_icmplt L3                      if_icmpge L2
    iconst_0                          iload_2
    goto L4                           iload_3
L3: iconst_1                          iadd
L4: ifeq L2                           istore 5
    iload 2                           iload_3
    iload 3                           istore_2
    iadd                              iload 5
    dup                               istore_3
    istore 5                          iinc 4 1
    pop                               goto L1
    ...  (mais 13 instruções)
    goto L1
```

---

## Erros em tempo de execução

Detectados conforme a especificação do COOL. Todos mostram a mensagem (com a linha do programa COOL, quando se aplica) e encerram com código 1:

| Situação | Mensagem |
|---|---|
| chamada de método em objeto void | `Erro em tempo de execucao (linha N): despacho (chamada de metodo) em objeto void` |
| divisão por zero | `... (linha N): divisao por zero` |
| `case` sobre void | `... (linha N): case em objeto void` |
| `case` sem ramo compatível | `... (linha N): nenhum ramo do case corresponde ao tipo do valor` |
| `substr` fora dos limites | `... (linha N): substr fora dos limites da string` |
| recursão profunda demais | `Erro em tempo de execucao: estouro da pilha de execucao (recursao muito profunda)` |
| `abort()` | `abort() chamado a partir da classe X` |

---

## Testes

```bash
make test
```

- **`test_semant.py`**: monta ASTs diretamente e confere as mensagens de erro da análise semântica, cobrindo cada tipo de erro e programas válidos.
- **`test_codegen.py`**: compila cada programa de `testes/*.cl`, executa na JVM e compara a saída com `testes/*.esperado`. A entrada padrão vem de `testes/*.entrada`, quando existe. Cada programa é testado **com e sem otimizações**: 11 programas, 22 casos.

| Programa de teste | O que cobre |
|---|---|
| `aritmetica.cl` | operadores, precedência, recursão, `while`, `let` |
| `strings.cl` | `length`, `concat`, `substr`, igualdade, caracteres de escape |
| `objetos.cl` | herança, sobrescrita, despacho estático, `SELF_TYPE`, `new SELF_TYPE`, `copy`, `isvoid` |
| `case.cl` | `case` com tipos básicos e classes, encaixotamento, igualdade de valores encaixotados |
| `entrada.cl` | `in_string` e `in_int` |
| `otimizacao.cl` | cada uma das otimizações (constant folding, `iinc`, desvios, descarte) |
| `correcoes.cl` | despacho estático para métodos de Object/IO, ordem de avaliação, recursão de 200 mil níveis |
| `erro_div.cl`, `erro_void.cl`, `erro_pilha.cl`, `abort.cl` | erros em tempo de execução |

Para adicionar um teste, crie `testes/nome.cl` e `testes/nome.esperado` com a saída exata esperada (e, se precisar, `testes/nome.entrada`).

---

## Estrutura dos arquivos

```
Compilador/
├── Makefile
├── coolc.py              driver: executa todas as etapas
│
├── cool.l                analisador léxico (Flex)
├── cool.y                analisador sintático (Bison) + construção da AST
├── ast.c, ast.h          nós da AST em C e impressão em JSON
├── ast_nodes.py          AST em Python (leitura do JSON)
│
├── semant.py             executa só até a análise semântica
├── semantico/
│   ├── analisador.py     classe Analyzer (junta as etapas)
│   ├── classes.py        classes básicas, registro, herança
│   ├── features.py       atributos, métodos, redefinições, Main
│   ├── tipos.py          checagem de tipos
│   ├── modelos.py        erro, assinatura de método, info de classe, escopos
│   └── constantes.py     nomes de tipos e tabelas fixas
│
├── codegen/
│   ├── gerador.py        AST tipada → assembly JVM, e otimizações
│   └── jvm.py            montagem dos métodos (pilha, locais, rótulos, strings)
├── runtime/              classes básicas do COOL em assembly JVM (à mão)
├── tools/jasmin.jar      assembler da JVM
│
├── test_semant.py        testes da análise semântica
├── test_codegen.py       testes da geração de código
├── testes/               programas de teste e saídas esperadas
├── exemplo.cl            programa de exemplo (listas)
├── teste.cl              programa de teste do parser (precedência, despachos)
└── erro.cl               programa com erros semânticos (demonstração)
```

Os arquivos gerados (`cool.tab.c`, `cool.tab.h`, `lex.yy.c`, `cool-parser`, `out/`) não são versionados: o `make` e o `coolc.py` os recriam.

---

## Decisões de projeto

- **JSON como interface entre C e Python:** mantém as partes independentes, é fácil de inspecionar e depurar, e dispensa bibliotecas de ligação entre as duas linguagens.
- **Nó genérico em C:** uma única função recursiva imprime qualquer tipo de nó.
- **Linha em todo nó:** permite reportar os erros semânticos e de execução na posição certa.
- **`stdout` só com o JSON, `stderr` com as mensagens:** permite usar pipe sem contaminar os dados.
- **JVM como alvo, via Jasmin:** a JVM já é orientada a objetos (herança, métodos virtuais, coletor de lixo), o que se encaixa bem no COOL, e o programa compilado roda em qualquer sistema com Java. O Jasmin gera `.class` no formato clássico, que não exige *stack map frames*.
- **Runtime em assembly, não em Java:** mantém o projeto inteiro como geração de código, sem nenhuma etapa de transpilação.
- **Corpo dos métodos em versões estáticas (`m$s`):** permite implementar o despacho estático do COOL com `invokestatic`, sem depender de `invokespecial`.
- **Otimizações desligáveis:** a opção `--sem-otimizacao` permite comparar o código gerado e conferir que as otimizações não mudam o comportamento (os testes rodam nos dois modos).

---

## Limitações conhecidas

- **Erros sintáticos:** o parser para no primeiro erro (não há recuperação de erros).
- **Mensagens:** o formato das mensagens de erro é próprio deste projeto e não replica o do compilador de referência do COOL.
- **Nomes reservados:** classes do usuário não podem se chamar `CoolObject`, `CoolInt`, `CoolBool`, `CoolString` ou `CoolRuntime`, que são as classes do runtime. A análise semântica rejeita esses nomes com uma mensagem clara.
- **Profundidade de recursão:** limitada pela pilha de 32 MB (cerca de 1 milhão de chamadas). Além disso, o programa termina com erro de estouro de pilha.
- **`in_int`:** lê uma linha inteira e a converte em número. Se a linha não for um inteiro válido, o resultado é 0.
- **Memória:** a liberação de memória fica a cargo do coletor de lixo da própria JVM.

---

Projeto acadêmico, desenvolvido por [@Gbmott4](https://github.com/Gbmott4).
