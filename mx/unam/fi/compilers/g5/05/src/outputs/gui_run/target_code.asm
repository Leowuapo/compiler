FUNC main
MOV y, 20
STORE_ARRAY values, 0, 10
LOAD_ARRAY t3, values, 0
GT t4, 20, t3
JZ t4, endif1
PRINTF 'result = %f', y
endif1:
RET 0
END_FUNC main
