; "Caixa" de um Bool (0 = false, 1 = true).

.class public CoolBool
.super CoolObject

.field public val I

.method public <init>(I)V
    .limit stack 2
    .limit locals 2
    aload_0
    invokespecial CoolObject/<init>()V
    aload_0
    iload_1
    putfield CoolBool/val I
    return
.end method

.method public static box(I)LCoolBool;
    .limit stack 3
    .limit locals 1
    new CoolBool
    dup
    iload_0
    invokespecial CoolBool/<init>(I)V
    areturn
.end method

.method public type_name()Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    ldc "Bool"
    areturn
.end method

.method public equals(Ljava/lang/Object;)Z
    .limit stack 2
    .limit locals 2
    aload_1
    instanceof CoolBool
    ifeq Falso
    aload_1
    checkcast CoolBool
    getfield CoolBool/val I
    aload_0
    getfield CoolBool/val I
    if_icmpne Falso
    iconst_1
    ireturn
Falso:
    iconst_0
    ireturn
.end method
