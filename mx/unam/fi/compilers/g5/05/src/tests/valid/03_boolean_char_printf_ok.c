int main() {
    char start = 'A';
    char next = 66;
    bool ok = (start != next) && true;
    int code = start + 1;

    printf("start=%c next=%c ok=%b code=%d", start, next, ok, code);
    return code;
}
