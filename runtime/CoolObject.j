; Classe Object do COOL (runtime escrito a mao em assembly JVM).
; Todas as classes COOL herdam desta classe.
;
; Como nas classes do usuario, cada metodo tem duas versoes:
;   m$s(self, ...)  estatica, com o corpo   -> usada no despacho estatico (e@Object.m())
;   m(...)          virtual, chama m$s      -> usada no despacho dinamico

.class public CoolObject
.super java/lang/Object
.implements java/lang/Cloneable

.method public <init>()V
    .limit stack 1
    .limit locals 1
    aload_0
    invokespecial java/lang/Object/<init>()V
    return
.end method

; ---------------------------------------------------------------- abort
.method public static abort$s(LCoolObject;)LCoolObject;
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic CoolObject/type_name$s(LCoolObject;)Ljava/lang/String;
    invokestatic CoolRuntime/abort(Ljava/lang/String;)V
    aconst_null
    areturn
.end method

.method public abort()LCoolObject;
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic CoolObject/abort$s(LCoolObject;)LCoolObject;
    areturn
.end method

; ------------------------------------------------------------ type_name
; nome COOL da classe dinamica do objeto
.method public static type_name$s(LCoolObject;)Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    aload_0
    invokevirtual java/lang/Object/getClass()Ljava/lang/Class;
    invokevirtual java/lang/Class/getName()Ljava/lang/String;
    invokestatic CoolRuntime/nomeCool(Ljava/lang/String;)Ljava/lang/String;
    areturn
.end method

.method public type_name()Ljava/lang/String;
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic CoolObject/type_name$s(LCoolObject;)Ljava/lang/String;
    areturn
.end method

; ----------------------------------------------------------------- copy
; copia rasa do objeto
.method public static copy$s(LCoolObject;)LCoolObject;
    .limit stack 1
    .limit locals 1
    .catch java/lang/CloneNotSupportedException from Ini to Fim using Erro
Ini:
    aload_0
    invokevirtual java/lang/Object/clone()Ljava/lang/Object;
    checkcast CoolObject
Fim:
    areturn
Erro:
    pop
    aconst_null
    areturn
.end method

.method public copy()LCoolObject;
    .limit stack 1
    .limit locals 1
    aload_0
    invokestatic CoolObject/copy$s(LCoolObject;)LCoolObject;
    areturn
.end method

; usado por "new SELF_TYPE": cria um objeto da mesma classe dinamica
.method public $new()LCoolObject;
    .limit stack 2
    .limit locals 1
    new CoolObject
    dup
    invokespecial CoolObject/<init>()V
    areturn
.end method
