// Bloques anidados y alcance de variables.

int a = 10;
int result;

{
    int x = a + 5;

    {
        int y = x * 2;
        result = y;
    }
}

int finalValue = result + a;