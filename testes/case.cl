class A { };
class B inherits A { };
class C inherits B { };
class Main inherits IO {
  qual(x : Object) : String {
    case x of
      i : Int => "Int ".concat(if i < 0 then "negativo" else "positivo" fi);
      s : String => "String de tamanho ".concat(if s.length() = 0 then "zero" else "maior" fi);
      b : Bool => if b then "Bool true" else "Bool false" fi;
      c : C => "C";
      a : A => "A ou B";
      o : Object => "outro: ".concat(o.type_name());
    esac
  };
  main() : Object {
    {
      out_string(qual(5)); out_string("\n");
      out_string(qual(~5)); out_string("\n");
      out_string(qual("")); out_string("\n");
      out_string(qual(true)); out_string("\n");
      out_string(qual(new C)); out_string("\n");
      out_string(qual(new B)); out_string("\n");
      out_string(qual(new A)); out_string("\n");
      out_string(qual(self)); out_string("\n");
      let o : Object <- 3, p : Object <- 3 in
        if o = p then out_string("ints encaixotados iguais\n") else out_string("errado\n") fi;
      let o : Object <- if true then 1 else "x" fi in out_string(o.type_name());
      out_string("\n");
    }
  };
};
