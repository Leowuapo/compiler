// test_stress.c
// Prueba de estrés para parser + SDT actual

int suma(int a, int b) {
    return a + b;
}

int resta(int a, int b) {
    return a - b;
}

int mult(int a, int b) {
    return a * b;
}

int dividir_seguro(int a, int b) {
    if (b == 0) {
        return 0;
    } else {
        return a / b;
    }
}

bool es_par(int x) {
    return x % 2 == 0;
}

bool esta_en_rango(int x, int minimo, int maximo) {
    return x >= minimo && x <= maximo;
}

int clamp(int x, int minimo, int maximo) {
    if (x < minimo) {
        return minimo;
    } else {
        if (x > maximo) {
            return maximo;
        } else {
            return x;
        }
    }
}

char normalizar_char(char c) {
    if (c == 'a') {
        return 'A';
    } else {
        return c;
    }
}

float promedio(float a, float b) {
    return (a + b) / 2;
}

double mezcla_double(double a, int b, char c) {
    return a + b + c;
}

void imprimir_estado(int x, bool activo, char marca) {
    printf("estado x=%d activo=%b marca=%c", x, activo, marca);
    print(x);
    print(activo);
    print(marca);
}

void probar_switch(int codigo) {
    switch (codigo) {
        case 0: {
            printf("codigo cero");
            break;
        }

        case 1: {
            printf("codigo uno");
            break;
        }

        case 2: {
            printf("codigo dos");
            break;
        }

        default: {
            printf("codigo default");
            break;
        }
    }
}

int acumular_con_for(int limite) {
    int total = 0;

    for (int i = 0; i < limite; i++) {
        if (i == 2) {
            continue;
        }

        if (i > 6) {
            break;
        }

        total = total + i;
    }

    return total;
}

int contar_hacia_abajo(int inicio) {
    int total = 0;

    for (int i = inicio; i > 0; i--) {
        total = total + i;

        if (total > 20) {
            break;
        }
    }

    return total;
}

int probar_while(int limite) {
    int i = 0;
    int total = 0;

    while (i < limite) {
        i = i + 1;

        if (i == 3) {
            continue;
        }

        total = total + i;

        if (total > 15) {
            break;
        }
    }

    return total;
}

int logica_compleja(int a, int b, bool flag) {
    bool condicion = (a < b && flag) || !(a == b);

    if (condicion) {
        return suma(a, b);
    } else {
        return resta(a, b);
    }
}

int main() {
    int a = 10;
    int b = 3;
    int c = suma(a, b);
    int d = resta(a, b);
    int e = mult(c, d);
    int f = dividir_seguro(e, b);

    float pf = promedio(3.5, 2.5);
    double md = mezcla_double(1.5, a, 'A');

    char letra = normalizar_char('a');
    bool par = es_par(c);
    bool rango = esta_en_rango(c, 5, 20);
    bool activo = par || rango;

    unsigned u = 100;
    short s = 12;
    long l = 1000;

    printf("inicio stress");
    printf("a=%d b=%d c=%d d=%d e=%d f=%d", a, b, c, d, e, f);
    printf("pf=%f md=%f", pf, md);
    printf("letra=%c par=%b rango=%b activo=%b", letra, par, rango, activo);
    printf("unsigned=%u short=%d long=%d", u, s, l);
    printf("string literal=%s porcentaje=100%%", "ok");

    print(a);
    print(c + d * 2);
    print(a > b && activo);
    print("print string literal");

    imprimir_estado(c, activo, letra);

    probar_switch(0);
    probar_switch(1);
    probar_switch(2);
    probar_switch(99);

    int total_for = acumular_con_for(10);
    int total_down = contar_hacia_abajo(8);
    int total_while = probar_while(10);
    int logica = logica_compleja(total_for, total_while, activo);

    printf("total_for=%d", total_for);
    printf("total_down=%d", total_down);
    printf("total_while=%d", total_while);
    printf("logica=%d", logica);

    if (total_for > 0 && total_while > 0) {
        int interno = clamp(total_for + total_while, 0, 100);
        printf("interno=%d", interno);

        while (interno > 0) {
            interno = interno - 10;

            switch (interno) {
                case 50: {
                    printf("switch dentro while: 50");
                    continue;
                }

                case 20: {
                    printf("switch dentro while: 20");
                    break;
                }

                default: {
                    printf("switch dentro while default");
                    break;
                }
            }

            if (interno < 15) {
                break;
            }
        }
    } else {
        int alterno = 1;
        printf("alterno=%d", alterno);
    }

    for (int i = 0; i < 5; i++) {
        printf("for externo i=%d", i);

        for (int j = 3; j > 0; j--) {
            printf("for interno j=%d", j);

            if (i == j) {
                continue;
            }

            if (i + j > 5) {
                break;
            }
        }
    }

    int resultado = suma(total_for, total_while) + dividir_seguro(total_down, 2);

    printf("resultado=%d", resultado);

    return resultado;
}