class Main inherits IO {
  main() : Object {
    let nome : String <- in_string(), n : Int <- in_int() in {
      out_string("Ola, ".concat(nome).concat("! dobro = "));
      out_int(n * 2);
      out_string("\n");
    }
  };
};
