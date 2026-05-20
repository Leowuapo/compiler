// Prueba de estrés para el compilador.

int a = 10, b = 20, c;
float x = 2.5;
double y;
bool flag = true;
char letter = 'A';

c = a + b * 2;
y = (x + c) / 2;

{
    int local = c + 10;

    {
        int nested = local * 2;
        c = nested + a;
    }

    float z = y + 1.5;
}

int result = c + letter;