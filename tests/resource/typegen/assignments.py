# Simple assignment, is lifted to AnnAssign
z = 0
# Resulting from math op, should not differ from simple assignment
y = 5.0 + z

# data structures
d = dict(zip("HelloWorld", range(10)))
s = set(range(10))
l = list(range(10))


# annotations in other chained and aug assignments are not (directly) supported 
# solution: declare variable beforehand
# a: float
# b: int
# i: float
# j: int
(a, b), (i, j) = (y, z), (y, z)

f = y = 10
f += y - 20
