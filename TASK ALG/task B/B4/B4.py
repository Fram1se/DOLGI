total = 0
while True:
    try:
        n = int(input("Число: "))
    except ValueError:
        print("Нужно целое число")
        continue
    if n == 0:
        break
    total = total + n
print(total)