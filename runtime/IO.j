; Classe IO do COOL (runtime escrito a mao em assembly JVM).
; Cada metodo tem a versao estatica m$s (corpo, para e@IO.m()) e a virtual m.

.class public IO
.super CoolObject

.method public <init>()V
    .limit stack 1
    .limit locals 1
    aload_0
    invokespecial CoolObject/<init>()V
    return
.end method

; ----------------------------------------------- out_string(x: String): SELF_TYPE
.method public static out_string$s(LIO;Ljava/lang/String;)LCoolObject;
    .limit stack 2
    .limit locals 2
    getstatic java/lang/System/out Ljava/io/PrintStream;
    aload_1
    invokevirtual java/io/PrintStream/print(Ljava/lang/String;)V
    aload_0
    areturn
.end method

.method public out_string(Ljava/lang/String;)LCoolObject;
    .limit stack 2
    .limit locals 2
    aload_0
    aload_1
    invokestatic IO/out_string$s(LIO;Ljava/lang/String;)LCoolObject;
    areturn
.end method

; ----------------------------------------------------- out_int(x: Int): SELF_TYPE
.method public static out_int$s(LIO;I)LCoolObject;
    .limit stack 2
    .limit locals 2
    getstatic java/lang/System/out Ljava/io/PrintStream;
    iload_1
    invokevirtual java/io/PrintStream/print(I)V
    aload_0
    areturn
.end method

.method public out_int(I)LCoolObject;
    .limit stack 2
    .limit locals 2
    aload_0
    iload_1
    invokestatic IO/out_int$s(LIO;I)LCoolObject;
    areturn
.end method

; ------------------------------------------------------------ in_string(): String
.method public static in_string$s(LIO;)Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    invokestatic CoolRuntime/readLine()Ljava/lang/String;
    areturn
.end method

.method public in_string()Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic IO/in_string$s(LIO;)Ljava/lang/String;
    areturn
.end method

; ------------------------------------------------------------------ in_int(): Int
.method public static in_int$s(LIO;)I
    .limit stack 1
    .limit locals 1
    invokestatic CoolRuntime/readInt()I
    ireturn
.end method

.method public in_int()I
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic IO/in_int$s(LIO;)I
    ireturn
.end method

.method public $new()LCoolObject;
    .limit stack 2
    .limit locals 1
    new IO
    dup
    invokespecial IO/<init>()V
    areturn
.end method
