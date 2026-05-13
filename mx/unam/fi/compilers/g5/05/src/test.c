int a = 10, b = 2;
int result;

{
    int x = a + b;
    int y = x * 3;

    {
        int z = y + a;
        result = z - b;
    }

    int w = result + x;

    {
        int q = w / 2;
        result = q + y;
    }
}

int finalValue = result + a;
