def func(a, b) -> int:
    x = 1
    return x


x = 1
if x > 10:  # cond name
    x += 10
elif x < 5:  # cond2 name
    x += 20
else:
    x += 4

while x < 100:  # while name
    x += 10

for i in range(1, 5, 1):  # for-name
    print(i)
    func(1, 10)
    x = func(1, 10)
    y = func(1, 10) + 5 * 42 << 5 + func(2, 20)

lst = []
for x in lst:
    pass

print("Call function")
