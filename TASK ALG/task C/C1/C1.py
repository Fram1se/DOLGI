energy = 10
while True:
    cmd = input("Команда: ")
    if cmd == "стоп":
        print("Итог:", energy)
        break
    elif cmd == "шаг":
        energy = energy - 2
        if energy <= 0:
            print("Сел")
            break
        print("Заряд:", energy)
    elif cmd == "заряд":
        energy = energy + 3
        if energy > 10:
            energy = 10
        print("Заряд:", energy)
    else:
        print("Не понял")