// Variable fuera de bloque no es accesible dentro del bloque.

int a = 10;

{
    int x = a + 1;
}

a = x + 5;