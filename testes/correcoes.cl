class A inherits IO {
  type_name() : String { "sobrescrito" };
  copy() : SELF_TYPE { self };
  out_string(x : String) : SELF_TYPE { { out_int(x.length()); self; } };
};
class Main inherits IO {
  s : String <- "abc";
  prof(n : Int) : Int { if n = 0 then 0 else 1 + prof(n - 1) fi };
  main() : Object {
    let a : A <- new A in {
      -- 1. despacho estatico para metodos de Object/IO
      out_string(a.type_name()); out_string("\n");
      out_string(a@Object.type_name()); out_string("\n");
      out_string(a@A.type_name()); out_string("\n");
      if a.copy() = a then out_string("copy sobrescrito\n") else out_string("errado\n") fi;
      if a@Object.copy() = a then out_string("errado\n") else out_string("copy original\n") fi;
      a.out_string("xyz"); out_string("\n");
      a@IO.out_string("io original\n");
      out_string(5@Object.type_name()); out_string("\n");
      out_string((new Object).type_name()); out_string("\n");
      -- 2. argumentos avaliados antes do receptor
      out_string(s.substr(0, (s <- "xy").length())); out_string("\n");
      out_string(s.concat((s <- "!").concat(s))); out_string("\n");
      -- 3. recursao profunda
      out_int(prof(200000)); out_string("\n");
    }
  };
};
