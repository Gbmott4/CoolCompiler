class Animal {
  nome : String <- "bicho";
  idade : Int;

  falar() : String { "..." };
  somar(a : Int, b : Int) : Int { a + b };
};

class Cachorro inherits Animal {
  idade : Int;

  falar() : Int { 1 };
  somar(a : String, b : Int) : Int { b };
};

class Main inherits IO {
  main() : Object {
    {
      x <- 5;
      out_string(10);
      1 + "a";
      if 3 then 1 else 2 fi;
      new Gato;
      somar(1);
    }
  };
};