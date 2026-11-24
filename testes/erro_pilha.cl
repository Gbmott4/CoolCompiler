class Main inherits IO {
  infinito(n : Int) : Int { infinito(n + 1) + 1 };
  main() : Object { { out_string("antes\n"); out_int(infinito(0)); } };
};
