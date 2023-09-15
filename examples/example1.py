def func(a, b) -> int:
    x = 1
    return x


x = 1
if x > 10:  # cond name
    x += 10
elif x < 5:
    x += 20
else:
    x += 4

while x < 100:  # while name
    x += 10

for i in range(1, 5, 1):  # for-name
    print(i)
    func(1, 10)
    x = func(1, 10)
    y = func(1, 10) + 5 * 42 << 5 + func(func(1, 1), 20, func(func(7, 1), 0))

lst = []
for x in lst:  # for-each-name
    pass

# blocks without name
for x in lst:
    a = 5 + func(x, 3)

for i in range(1, 4 * a, a):
    i += 1

if "emptyname_condition":
    pass

print("Call function")
