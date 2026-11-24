; "Caixa" de uma String (o valor e um java/lang/String).

.class public CoolString
.super CoolObject

.field public val Ljava/lang/String;

.method public <init>(Ljava/lang/String;)V
    .limit stack 2
    .limit locals 2
    aload_0
    invokespecial CoolObject/<init>()V
    aload_0
    aload_1
    putfield CoolString/val Ljava/lang/String;
    return
.end method

.method public static box(Ljava/lang/String;)LCoolString;
    .limit stack 3
    .limit locals 1
    new CoolString
    dup
    aload_0
    invokespecial CoolString/<init>(Ljava/lang/String;)V
    areturn
.end method

.method public type_name()Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    ldc "String"
    areturn
.end method

.method public equals(Ljava/lang/Object;)Z
    .limit stack 2
    .limit locals 2
    aload_1
    instanceof CoolString
    ifeq Falso
    aload_1
    checkcast CoolString
    getfield CoolString/val Ljava/lang/String;
    aload_0
    getfield CoolString/val Ljava/lang/String;
    invokevirtual java/lang/String/equals(Ljava/lang/Object;)Z
    ireturn
Falso:
    iconst_0
    ireturn
.end method
