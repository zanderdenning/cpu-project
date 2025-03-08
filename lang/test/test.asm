.section code
.global $test:
sw ra 0(fp)
lw ra 0(fp)
lw fp 8(fp)
jra zero ra
.global $main:
sw ra 0(fp)
li x9 str_2559356032
sw x9 -12(fp)
li x9 1
sw x9 -16(fp)
li x9 2
sw x9 -20(fp)
sw fp -24(fp)
sw fp -28(fp)
addi fp fp -32
ja ra $test
mv x9 a0
li x9 2
li t14 $a
sw x9 0(t14)
sw x9 -8(fp)
lbu x9 -4(fp)
lbu x9 -5(fp)
li x9 1
li x10 2
add x9 x9 x10
li x10 3
add x9 x9 x10
li x10 4
add x9 x9 x10
li x9 0
mv a0 x9
lw ra 0(fp)
lw fp 8(fp)
jra zero ra
lw ra 0(fp)
lw fp 8(fp)
jra zero ra
.section data
.padding 0
.global $a:
.padding 4
.global $b:
.padding 4
.global $c:
.padding 1
.global $d:
.padding 3
.global $e:
.padding 4
str_2559356032:
.bytes 616263
.padding 1
