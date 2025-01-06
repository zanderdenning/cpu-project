add x10 x10 x10
.global main:
addi x1 x0 10
start:
addi x2 x2 1
blt x2 x1 start likely
addi x3 x0 1
beq x3 x3 main
beq x4 x4 func