class Main inherits IO {
  fat(n : Int) : Int { if n <= 1 then 1 else n * fat(n - 1) fi };
  fib(n : Int) : Int {
    let a : Int <- 0, b : Int <- 1, i : Int <- 0, t : Int in {
      while i < n loop { t <- a + b; a <- b; b <- t; i <- i + 1; } pool;
      a;
    }
  };
  main() : Object {
    {
      out_int(2 + 3 * 4 - 10 / 3); out_string("\n");
      out_int(~5 + 2); out_string("\n");
      out_int(fat(10)); out_string("\n");
      out_int(fib(30)); out_string("\n");
      if not (3 < 2) then out_string("not ok\n") else out_string("errado\n") fi;
      if 5 = 5 then out_string("igual ok\n") else out_string("errado\n") fi;
      out_int(1000000); out_string("\n");
    }
  };
};
