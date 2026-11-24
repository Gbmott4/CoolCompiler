class Main inherits IO {
  n : Int;
  main() : Object {
    let i : Int <- 0, soma : Int <- 0, x : Int in {
      out_int(2 + 3 * 4); out_string("\n");
      out_int(~7 / 2); out_string("\n");
      out_int(2147483647 + 1); out_string("\n");
      if 1 < 2 then out_string("then constante\n") else out_string("errado\n") fi;
      if not (1 = 1) then out_string("errado\n") else out_string("else constante\n") fi;
      while false loop out_string("errado\n") pool;
      while i < 10 loop { i <- i + 1; soma <- soma + i; 42; "ignorado"; i; } pool;
      out_int(soma); out_string("\n");
      x <- 100; x <- x - 3; x <- 5 + x; x <- x - 200; x <- x + 1000;
      out_int(x); out_string("\n");
      out_int(i <- i + 5); out_string("\n");
      n <- n + 1; n <- n + 1;
      out_int(n); out_string("\n");
      if not (i <= 3) then out_string("not com desvio\n") else out_string("errado\n") fi;
      if i = 15 then out_string("igualdade com desvio\n") else out_string("errado\n") fi;
      if isvoid self then out_string("errado\n") else out_string("isvoid com desvio\n") fi;
      { { soma <- 0; }; soma <- soma + 7; };
      out_int(soma); out_string("\n");
    }
  };
};
