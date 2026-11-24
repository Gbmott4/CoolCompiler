; Funcoes de suporte chamadas pelo codigo gerado (erros em tempo de execucao,
; leitura da entrada, divisao, substr e igualdade).

.class public CoolRuntime
.super java/lang/Object

.field public static leitor Ljava/io/BufferedReader;

.method public static flush()V
    .limit stack 1
    .limit locals 0
    getstatic java/lang/System/out Ljava/io/PrintStream;
    invokevirtual java/io/PrintStream/flush()V
    return
.end method

; error(msg, linha): imprime o erro e encerra com codigo 1 (linha <= 0: sem linha)
.method public static error(Ljava/lang/String;I)V
    .limit stack 3
    .limit locals 3
    invokestatic CoolRuntime/flush()V
    new java/lang/StringBuilder
    dup
    invokespecial java/lang/StringBuilder/<init>()V
    ldc "Erro em tempo de execucao"
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    astore_2
    iload_1
    ifle SemLinha
    aload_2
    ldc " (linha "
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    iload_1
    invokevirtual java/lang/StringBuilder/append(I)Ljava/lang/StringBuilder;
    ldc ")"
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    pop
SemLinha:
    getstatic java/lang/System/err Ljava/io/PrintStream;
    aload_2
    ldc ": "
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    aload_0
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invokevirtual java/lang/StringBuilder/toString()Ljava/lang/String;
    invokevirtual java/io/PrintStream/println(Ljava/lang/String;)V
    iconst_1
    invokestatic java/lang/System/exit(I)V
    return
.end method

; erro de estouro da pilha (recursao muito profunda)
.method public static erroPilha()V
    .limit stack 2
    .limit locals 0
    ldc "estouro da pilha de execucao (recursao muito profunda)"
    iconst_0
    invokestatic CoolRuntime/error(Ljava/lang/String;I)V
    return
.end method

; nomeCool(nomeJVM): nome COOL de uma classe (CoolObject -> Object, CoolInt -> Int ...)
.method public static nomeCool(Ljava/lang/String;)Ljava/lang/String;
    .limit stack 2
    .limit locals 1
    aload_0
    ldc "CoolObject"
    invokevirtual java/lang/String/equals(Ljava/lang/Object;)Z
    ifeq NaoObject
    ldc "Object"
    areturn
NaoObject:
    aload_0
    ldc "CoolInt"
    invokevirtual java/lang/String/equals(Ljava/lang/Object;)Z
    ifeq NaoInt
    ldc "Int"
    areturn
NaoInt:
    aload_0
    ldc "CoolBool"
    invokevirtual java/lang/String/equals(Ljava/lang/Object;)Z
    ifeq NaoBool
    ldc "Bool"
    areturn
NaoBool:
    aload_0
    ldc "CoolString"
    invokevirtual java/lang/String/equals(Ljava/lang/Object;)Z
    ifeq NaoString
    ldc "String"
    areturn
NaoString:
    aload_0
    areturn
.end method

; abort(nomeClasse)
.method public static abort(Ljava/lang/String;)V
    .limit stack 3
    .limit locals 1
    invokestatic CoolRuntime/flush()V
    getstatic java/lang/System/err Ljava/io/PrintStream;
    new java/lang/StringBuilder
    dup
    invokespecial java/lang/StringBuilder/<init>()V
    ldc "abort() chamado a partir da classe "
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    aload_0
    invokevirtual java/lang/StringBuilder/append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invokevirtual java/lang/StringBuilder/toString()Ljava/lang/String;
    invokevirtual java/io/PrintStream/println(Ljava/lang/String;)V
    iconst_1
    invokestatic java/lang/System/exit(I)V
    return
.end method

; checkVoid(obj, linha): erro se o objeto receptor de um despacho for void
.method public static checkVoid(Ljava/lang/Object;I)V
    .limit stack 2
    .limit locals 2
    aload_0
    ifnonnull Ok
    ldc "despacho (chamada de metodo) em objeto void"
    iload_1
    invokestatic CoolRuntime/error(Ljava/lang/String;I)V
Ok:
    return
.end method

; div(a, b, linha)
.method public static div(III)I
    .limit stack 2
    .limit locals 3
    iload_1
    ifne Ok
    ldc "divisao por zero"
    iload_2
    invokestatic CoolRuntime/error(Ljava/lang/String;I)V
Ok:
    iload_0
    iload_1
    idiv
    ireturn
.end method

; substr(s, i, l, linha)
.method public static substr(Ljava/lang/String;III)Ljava/lang/String;
    .limit stack 4
    .limit locals 4
    iload_1
    iflt Erro
    iload_2
    iflt Erro
    iload_1
    iload_2
    iadd
    aload_0
    invokevirtual java/lang/String/length()I
    if_icmpgt Erro
    aload_0
    iload_1
    iload_1
    iload_2
    iadd
    invokevirtual java/lang/String/substring(II)Ljava/lang/String;
    areturn
Erro:
    ldc "substr fora dos limites da string"
    iload_3
    invokestatic CoolRuntime/error(Ljava/lang/String;I)V
    ldc ""
    areturn
.end method

; eq(a, b): operador = entre objetos (Int/Bool/String encaixotados comparam por valor)
.method public static eq(Ljava/lang/Object;Ljava/lang/Object;)I
    .limit stack 2
    .limit locals 2
    aload_0
    aload_1
    if_acmpeq Verdadeiro
    aload_0
    ifnull Falso
    aload_0
    aload_1
    invokevirtual java/lang/Object/equals(Ljava/lang/Object;)Z
    ireturn
Verdadeiro:
    iconst_1
    ireturn
Falso:
    iconst_0
    ireturn
.end method

; le uma linha da entrada padrao ("" no fim da entrada)
.method public static readLine()Ljava/lang/String;
    .limit stack 5
    .limit locals 0
    .catch java/io/IOException from Ini to Fim using Erro
    invokestatic CoolRuntime/flush()V
    getstatic CoolRuntime/leitor Ljava/io/BufferedReader;
    ifnonnull Ini
    new java/io/BufferedReader
    dup
    new java/io/InputStreamReader
    dup
    getstatic java/lang/System/in Ljava/io/InputStream;
    invokespecial java/io/InputStreamReader/<init>(Ljava/io/InputStream;)V
    invokespecial java/io/BufferedReader/<init>(Ljava/io/Reader;)V
    putstatic CoolRuntime/leitor Ljava/io/BufferedReader;
Ini:
    getstatic CoolRuntime/leitor Ljava/io/BufferedReader;
    invokevirtual java/io/BufferedReader/readLine()Ljava/lang/String;
Fim:
    dup
    ifnonnull Ok
    pop
    ldc ""
Ok:
    areturn
Erro:
    pop
    ldc ""
    areturn
.end method

; le um inteiro (0 se a linha nao for um numero)
.method public static readInt()I
    .limit stack 1
    .limit locals 1
    .catch java/lang/NumberFormatException from Ini to Fim using Erro
    invokestatic CoolRuntime/readLine()Ljava/lang/String;
    invokevirtual java/lang/String/trim()Ljava/lang/String;
    astore_0
Ini:
    aload_0
    invokestatic java/lang/Integer/parseInt(Ljava/lang/String;)I
Fim:
    ireturn
Erro:
    pop
    iconst_0
    ireturn
.end method
