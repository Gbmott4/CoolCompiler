; "Caixa" de um Int: usada quando um Int vai para uma variavel de tipo Object
; (ex.: atributo Object, argumento Object, ramo de if/case com tipos diferentes).

.class public CoolInt
.super CoolObject

.field public val I

.method public <init>(I)V
    .limit stack 2
    .limit locals 2
    aload_0
    invokespecial CoolObject/<init>()V
    aload_0
    iload_1
    putfield CoolInt/val I
    return
.end method

.method public static box(I)LCoolInt;
    .limit stack 3
    .limit locals 1
    new CoolInt
    dup
    iload_0
    invokespecial CoolInt/<init>(I)V
    areturn
.end method

.method public type_name()Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    ldc "Int"
    areturn
.end method

; igualdade por valor (usada pelo operador = em tempo de execucao)
.method public equals(Ljava/lang/Object;)Z
    .limit stack 2
    .limit locals 2
    aload_1
    instanceof CoolInt
    ifeq Falso
    aload_1
    checkcast CoolInt
    getfield CoolInt/val I
    aload_0
    getfield CoolInt/val I
    if_icmpne Falso
    iconst_1
    ireturn
Falso:
    iconst_0
    ireturn
.end method
