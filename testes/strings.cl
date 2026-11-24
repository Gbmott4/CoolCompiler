class Main inherits IO {
  s : String <- "Compiladores";
  vazio : String;
  main() : Object {
    {
      out_string(s.concat(" com COOL")); out_string("\n");
      out_int(s.length()); out_string("\n");
      out_string(s.substr(0, 8)); out_string("\n");
      out_int(vazio.length()); out_string("\n");
      out_string(s.type_name()); out_string("\n");
      if s = "Compiladores" then out_string("str igual\n") else out_string("errado\n") fi;
      out_string("aspas \"e\" barra \\ tab\tfim\n");
    }
  };
};
