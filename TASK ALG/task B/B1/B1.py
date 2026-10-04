def rub_word(n):
    last_two = n % 100
    last_one = n % 10
    if 11 <= last_two <= 14:
        word = "рублей"
    elif last_one == 1:
        word = "рубль"
    elif last_one in (2, 3, 4):
        word = "рубля"
    else:
        word = "рублей"
    return word

try:
    money = int(input("Сумма: "))
    print(money, rub_word(money))
except ValueError:
    print("Нужно целое число")