def ticket(age):    
    if age < 0 or age > 120:
        kind = "Возраст не подходит"
    elif age <= 6:
        kind = "Бесплатно"
    elif age <= 17:
        kind = "Детский билет"
    elif age <= 64:
        kind = "Обычный билет"
    else:
        kind = "Льготный билет"
    return kind

try:
    age = int(input("Возраст: "))
    print(ticket(age))
except ValueError:
    print("Нужно целое число")