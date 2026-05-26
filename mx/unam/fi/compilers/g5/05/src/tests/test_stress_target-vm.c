int suma(int a, int b) {
    return a + b;
}

int cuadrado(int x) {
    return x * x;
}

int max2(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

int acum_for() {
    int total = 0;

    for (int i = 0; i < 4; i++) {
        total = total + i;
    }

    return total;
}

int acum_while(int limite) {
    int i = 0;
    int total = 0;

    while (i < limite) {
        total = total + i;
        i = i + 1;
    }

    return total;
}

bool es_valido(int x) {
    return x > 10 && x < 50;
}

void imprimir_valor(int v) {
    printf("valor=%d", v);
}

int main() {
    int a = suma(10, 5);
    int b = cuadrado(4);
    int c = max2(a, b);

    int total_for = acum_for();
    int total_while = acum_while(4);

    int arr[4] = {1, 2, 3, 4};
    int m[2][2];

    m[0][0] = a;
    m[0][1] = b;
    m[1][0] = arr[0] + arr[1];
    m[1][1] = arr[2] + arr[3];

    int matriz_total = m[0][0] + m[0][1] + m[1][0] + m[1][1];

    bool ok = es_valido(matriz_total);

    if (ok) {
        printf("matriz_total=%d", matriz_total);
    } else {
        printf("matriz_total_invalido=%d", matriz_total);
    }

    imprimir_valor(c);

    int resultado = matriz_total + total_for + total_while;

    printf("a=%d b=%d c=%d", a, b, c);
    printf("for=%d while=%d", total_for, total_while);
    printf("resultado=%d", resultado);

    print(resultado);

    return resultado;
}