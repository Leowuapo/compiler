FUNC suma
PARAM a
PARAM b
ADD t1, a, b
RET t1
END_FUNC suma
FUNC cuadrado
PARAM x
MUL t2, x, x
RET t2
END_FUNC cuadrado
FUNC max2
PARAM a
PARAM b
GT t3, a, b
JZ t3, else1
RET a
else1:
RET b
END_FUNC max2
FUNC acum_for
MOV total, 0
MOV i, 0
MOV total, 0
MOV total, 1
MOV total, 3
MOV total, 6
MOV i, 4
RET 6
END_FUNC acum_for
FUNC acum_while
PARAM limite
MOV i, 0
MOV total, 0
while6:
LT t6, i, limite
JZ t6, endwhile7
ADD t7, total, i
MOV total, t7
ADD t8, i, 1
MOV i, t8
JMP while6
endwhile7:
RET total
END_FUNC acum_while
FUNC es_valido
PARAM x
GT t9, x, 10
LT t10, x, 50
AND t11, t9, t10
RET t11
END_FUNC es_valido
FUNC imprimir_valor
PARAM v
PRINTF 'valor=%d', v
END_FUNC imprimir_valor
FUNC main
ARG 10
ARG 5
CALL t12, suma, 2
MOV a, t12
ARG 4
CALL t13, cuadrado, 1
MOV b, t13
ARG a
ARG b
CALL t14, max2, 2
MOV c, t14
CALL t15, acum_for, 0
MOV total_for, t15
ARG 4
CALL t16, acum_while, 1
MOV total_while, t16
STORE_ARRAY arr, 0, 1
STORE_ARRAY arr, 1, 2
STORE_ARRAY arr, 2, 3
STORE_ARRAY arr, 3, 4
STORE_MATRIX m, 0, 0, a
STORE_MATRIX m, 0, 1, b
LOAD_ARRAY t17, arr, 0
LOAD_ARRAY t18, arr, 1
ADD t19, t17, t18
STORE_MATRIX m, 1, 0, t19
LOAD_ARRAY t20, arr, 2
LOAD_ARRAY t21, arr, 3
ADD t22, t20, t21
STORE_MATRIX m, 1, 1, t22
LOAD_MATRIX t23, m, 0, 0
LOAD_MATRIX t24, m, 0, 1
ADD t25, t23, t24
LOAD_MATRIX t26, m, 1, 0
ADD t27, t25, t26
LOAD_MATRIX t28, m, 1, 1
ADD t29, t27, t28
MOV matriz_total, t29
ARG matriz_total
CALL t30, es_valido, 1
MOV ok, t30
JZ ok, else8
PRINTF 'matriz_total=%d', matriz_total
JMP endif9
else8:
PRINTF 'matriz_total_invalido=%d', matriz_total
endif9:
ARG c
CALL imprimir_valor, 1
ADD t31, matriz_total, total_for
ADD t32, t31, total_while
MOV resultado, t32
PRINTF 'a=%d b=%d c=%d', a, b, c
PRINTF 'for=%d while=%d', total_for, total_while
PRINTF 'resultado=%d', resultado
PRINT resultado
RET resultado
END_FUNC main
