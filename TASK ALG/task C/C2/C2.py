secret = "421"
tries = 3
while tries > 0:
    code = input("Код: ")
    if code == secret:
        print("Открыт")
        break
    tries = tries - 1
    if tries == 0:
        print("Закрыт")
    else:
        print("Осталось:", tries)