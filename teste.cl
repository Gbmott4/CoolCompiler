class Main inherits IO {

    x : Int <- 10;

    main() : Object {
        {
            -- Precedência: multiplicação antes da soma
            x <- 2 + 3 * 4;

            -- Parênteses
            x <- (2 + 3) * 4;

            -- Comparação
            if x <= 20 then
                out_string("OK\n")
            else
                out_string("ERRO\n")
            fi;

            -- Dispatch com ponto
            self.out_int(x);

            -- Dispatch estático com @
            self@IO.out_int(x);

            x;
        }
    };
};