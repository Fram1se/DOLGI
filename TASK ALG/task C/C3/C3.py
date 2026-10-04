def price_of(gun):
    if gun == "G22":
        return 300
    if gun == "AKR":
        return 2700
    if gun == "M4":
        return 3100
    if gun == "AWM":
        return 4750
    return None

try:
    gold = int(input("Голда: "))
except ValueError:
    print("Голда — число")
    raise SystemExit
gun = input("Оружие: ")
price = price_of(gun)
if price is None:
    print("Нет такого оружия.")
elif gold < price:
    need = price - gold
    print("Не хватит. Нужно ещё", need)
else:
    left = gold - price
    print("Купил", gun + ". Остаток", left)