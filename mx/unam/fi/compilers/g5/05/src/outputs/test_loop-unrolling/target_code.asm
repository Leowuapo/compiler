FUNC BasicLoopUnrolling
MOV total, 0
MOV i, 0
MOV total, 0
MOV total, 1
MOV total, 3
MOV i, 3
RET 3
END_FUNC BasicLoopUnrolling
FUNC LargeLoopUnrolling
MOV total, 0
MOV i, 0
for4:
LT t3, i, 20
JZ t3, endfor6
ADD t4, total, i
MOV total, t4
ADD i, i, 1
JMP for4
endfor6:
RET total
END_FUNC LargeLoopUnrolling
FUNC LoopWithContinue
MOV total, 0
MOV i, 0
for7:
LT t5, i, 3
JZ t5, endfor9
EQ t6, i, 1
JZ t6, endif10
JMP for_update8
endif10:
ADD t7, total, i
MOV total, t7
for_update8:
ADD i, i, 1
JMP for7
endfor9:
RET total
END_FUNC LoopWithContinue
