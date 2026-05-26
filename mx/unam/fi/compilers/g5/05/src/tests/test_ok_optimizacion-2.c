int prueba_constantes() {
    int x = 2 + 3 * 4;
    int y = x + 0;
    int z = y * 1;

    if (true) {
        print(z);
    }

    return z;
}

int prueba_branch() {
    if (false) {
        print(1);
    } else {
        print(2);
    }

    return 0;
}

int prueba_temporales() {
    int x = 10;
    int y = x;
    int z = y;

    return z;
}

int prueba_for() {
    int total = 0;

    for (int i = 0; i < 3; i++) {
        total = total + i;
    }

    return total;
}

int main() {
    int a = prueba_constantes();
    int b = prueba_branch();
    int c = prueba_temporales();
    int d = prueba_for();

    printf("a=%d b=%d c=%d d=%d", a, b, c, d);

    return a + b + c + d;
}