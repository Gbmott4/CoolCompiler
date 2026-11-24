class Animal {
  nome : String <- "bicho";
  som() : String { "..." };
  falar(io : IO) : Object { io.out_string(nome.concat(": ").concat(som()).concat("\n")) };
  setNome(n : String) : SELF_TYPE { { nome <- n; self; } };
  clone_novo() : SELF_TYPE { new SELF_TYPE };
  getNome() : String { nome };
};
class Cachorro inherits Animal {
  som() : String { "au au" };
};
class Gato inherits Animal {
  vidas : Int <- 7;
  som() : String { "miau" };
  getVidas() : Int { vidas };
};
class Contador {
  n : Int;
  inc() : SELF_TYPE { { n <- n + 1; self; } };
  valor() : Int { n };
};
class Main inherits IO {
  x : Object <- 42;
  a : Animal;
  main() : Object {
    {
      (new Animal).falar(self);
      (new Cachorro).setNome("Rex").falar(self);
      a <- new Gato;
      a.falar(self);
      a@Animal.falar(self);
      out_string(a.type_name()); out_string("\n");
      out_string((new Cachorro).clone_novo().type_name()); out_string("\n");
      out_int((new Contador).inc().inc().inc().valor()); out_string("\n");
      out_string(x.type_name()); out_string("\n");
      out_string(type_name()); out_string("\n");
      if isvoid a then out_string("errado\n") else out_string("nao void\n") fi;
      if isvoid (let z : Animal in z) then out_string("void\n") else out_string("errado\n") fi;
      let c : Animal <- (new Gato).setNome("Tom"), d : Animal <- c.copy() in {
        d.setNome("Copia");
        out_string(c.getNome().concat(" ").concat(d.getNome())); out_string("\n");
        if c = c then out_string("mesmo objeto\n") else out_string("errado\n") fi;
        if c = d then out_string("errado\n") else out_string("objetos diferentes\n") fi;
      };
    }
  };
};
