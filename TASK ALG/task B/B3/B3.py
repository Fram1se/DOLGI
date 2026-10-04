def mode(hour):
    if hour < 0 or hour > 23:
        text = "Нет такого часа"
    elif hour <= 5:
        text = "Ночной режим"
    elif hour <= 11:
        text = "Утренний режим"
    elif hour <= 17:
        text = "Дневной режим"
    else:
        text = "Вечерний режим"
    return text

try:
    hour = int(input("Час: "))
    print(mode(hour))
except ValueError:
    print("Нужно целое число")