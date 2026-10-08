import tkinter as tk
from tkinter import ttk
from tkinter import Label
import psycopg2

def connect():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="dostavka_bd",
        user="postgres",
        password="your_password"  # ЗАМЕНИТЕ НА СВОЙ ПАРОЛЬ
    )

okno1 = tk.Tk()
okno1.title("Окно 1. Посылка")
okno1.geometry("400x350")

tk.Label(okno1, text="Трек-номер", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
entry_nomer = ttk.Entry(okno1, width=40)
entry_nomer.pack(anchor="w", padx=10, pady=5)

tk.Label(okno1, text="Фамилия", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
entry_fam = ttk.Entry(okno1, width=40)
entry_fam.pack(anchor="w", padx=10, pady=5)

tk.Label(okno1, text="Имя", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
entry_imya = ttk.Entry(okno1, width=40)
entry_imya.pack(anchor="w", padx=10, pady=5)

label_err1 = tk.Label(okno1, text="", fg="red", font=("Arial", 11, "bold"))
label_err1.pack(anchor="w", padx=10, pady=5)

def naiti():
    global nomer, familiya, imya
    nomer = entry_nomer.get()
    familiya = entry_fam.get()
    imya = entry_imya.get()
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM parcels WHERE Трек = %s AND Фамилия = %s AND Имя = %s;",
        (nomer, familiya, imya)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        label_err1["text"] = "Посылка не найдена"
        return
    okno1.destroy()
    okno2()

ttk.Button(okno1, text="Далее", command=naiti).pack(anchor="w", padx=10, pady=15)

def okno2():
    win = tk.Tk()
    win.title("Окно 2. Вес")
    win.geometry("400x300")
    global win2, entry_ves, label_sum, label_err2
    win2 = win
    ttk.Label(win, text=familiya + " " + imya + " " + nomer, font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=6)
    ttk.Label(win, text="Вес, кг", font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=2)
    entry_ves = ttk.Entry(win, width=40)
    entry_ves.pack(anchor="w", padx=8, pady=2)
    entry_ves.bind("<KeyRelease>", obnovit_summu)
    label_sum = Label(win, text="Сумма: -", font=("Arial", 11, "bold"))
    label_sum.pack(anchor="w", padx=8, pady=6)
    label_err2 = Label(win, text="", fg="red", font=("Arial", 11, "bold"))
    label_err2.pack(anchor="w", padx=8, pady=2)
    ttk.Button(win, text="Далее", command=dalshe2).pack(anchor="w", padx=8, pady=6)

def obnovit_summu(event=None):
    global ves, summa
    tekst = entry_ves.get()
    try:
        ves = int(tekst)
        summa = ves * 90
        label_sum["text"] = "Сумма: " + str(summa)
    except ValueError:
        label_sum["text"] = "Сумма: -"

def dalshe2():
    global ves
    if 'ves' not in globals():
        label_err2["text"] = "Введите вес"
        return
    if ves < 1:
        label_err2["text"] = "Вес должен быть больше 0"
        return
    win2.destroy()
    okno3()

def okno3():
    win = tk.Tk()
    win.title("Окно 3. Выдача")
    win.geometry("400x400")
    global win3, entry_data, entry_yacheyka, label_err3
    win3 = win
    Label(win, text=familiya + " " + imya + " " + nomer, font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=4)
    Label(win, text="Вес: " + str(ves), font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=2)
    Label(win, text="Сумма: " + str(summa), font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=2)
    ttk.Label(win, text="Дата", font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=2)
    entry_data = ttk.Entry(win, width=40)
    entry_data.pack(anchor="w", padx=8, pady=2)
    ttk.Label(win, text="Ячейка", font=("Arial", 11, "bold")).pack(anchor="w", padx=8, pady=2)
    entry_yacheyka = ttk.Entry(win, width=40)
    entry_yacheyka.pack(anchor="w", padx=8, pady=2)
    label_err3 = Label(win, text="", fg="red", font=("Arial", 11, "bold"))
    label_err3.pack(anchor="w", padx=8, pady=2)
    ttk.Button(win, text="Записать в базу", command=sohranit).pack(anchor="w", padx=8, pady=6)

def sohranit():
    data = entry_data.get()
    yacheyka = entry_yacheyka.get()
    if data == "" or yacheyka == "":
        label_err3["text"] = "Заполните дату и ячейку"
        return
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO vydacha (трек, фамилия, имя, вес, сумма, дата, ячейка) VALUES (%s, %s, %s, %s, %s, %s, %s);",
        (nomer, familiya, imya, ves, summa, data, yacheyka)
    )
    conn.commit()
    cur.close()
    conn.close()
    label_err3["text"] = "Записано"

okno1.mainloop()