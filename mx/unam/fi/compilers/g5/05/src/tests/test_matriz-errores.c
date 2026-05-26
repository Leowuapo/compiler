// Matriz como array 1D
int matrixAs1DArray() {
    int m[2][2];

    int x = m[0];

    return x;
}

// Matriz con dimensiones negativas
int rowNegativeDimension() {
    int m[-2][3];

    return 0;
}

int columnNegativeDimension() {
    int m[2][-3];

    return 0;
}

// Elemento no inicializado
int elementNotDefined() {
    int m[2][2];

    return m[0][0];
}

// Acceso a índices fuera de límites
int rowOutofBounds() {
    int m[2][2];

    m[2][0] = 1;

    return 0;
}

int columnOutofBounds() {
    int m[2][2];

    m[0][2] = 1;

    return 0;
}

// Matriz como escalar
int matrixAsScalar() {
    int m[2][2];

    int x = m;

    return x;
}