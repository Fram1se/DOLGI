import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from psycopg2 import sql
import pandas as pd
import os


DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "sever_bd"
DB_USER = "postgres"
DB_PASSWORD = "your_password"  # ЗАМЕНИТЕ НА СВОЙ ПАРОЛЬ

BG_WHITE = "#FFFFFF"
BG_BLOCK = "#BFD6F6"
BTN_COLOR = "#405C73"
BTN_GREEN = "#2E7D32"
BTN_RED = "#B3261E"
FONT_NAME = "Constantia"
FONT_SIZE = 12

def get_connection():
    """Возвращает подключение к PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )

def create_database_and_tables():
    """Создает БД и таблицы, если их нет."""
    # Подключаемся к служебной БД postgres, чтобы создать sever_bd
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname="postgres",
        user=DB_USER, password=DB_PASSWORD
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
    cur.close()
    conn.close()

    # Подключаемся к sever_bd и создаем таблицы
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_types (
            id SERIAL PRIMARY KEY,
            тип VARCHAR(100) NOT NULL,
            коэффициент DECIMAL(5,2) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS material_types (
            id SERIAL PRIMARY KEY,
            материал VARCHAR(100) NOT NULL,
            потери DECIMAL(5,2) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS materials (
            id SERIAL PRIMARY KEY,
            материал VARCHAR(100) NOT NULL,
            id_type INT REFERENCES material_types(id),
            склад DECIMAL(10,2)
        );
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            артикул VARCHAR(50) NOT NULL,
            id_type INT REFERENCES product_types(id),
            цена_для_партнёра DECIMAL(10,2)
        );
        CREATE TABLE IF NOT EXISTS material_products (
            id SERIAL PRIMARY KEY,
            id_product INT REFERENCES products(id),
            id_material INT REFERENCES materials(id),
            расход DECIMAL(10,2)
        );
        CREATE TABLE IF NOT EXISTS partners (
            id SERIAL PRIMARY KEY,
            название VARCHAR(200) NOT NULL,
            тип VARCHAR(50),
            телефон VARCHAR(20),
            рейтинг INT CHECK (рейтинг BETWEEN 0 AND 10)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            id_partner INT REFERENCES partners(id),
            дата DATE,
            статус VARCHAR(50),
            сумма DECIMAL(12,2)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            id_order INT REFERENCES orders(id),
            id_product INT REFERENCES products(id),
            шт INT,
            цена DECIMAL(10,2)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def import_excel_data():
    """Импорт данных из Excel в БД (упрощенная версия)."""
    files = {
        "product_types": "resources/Product_type_import.xlsx",
        "products": "resources/Products_import.xlsx",
        "material_types": "resources/Material_type_import.xlsx",
        "materials": "resources/Materials_import.xlsx",
        "material_products": "resources/Material_products__import.xlsx",
    }
    conn = get_connection()
    cur = conn.cursor()
    
    for table, path in files.items():
        if os.path.exists(path):
            try:
                df = pd.read_excel(path)
                # Очищаем таблицу перед импортом
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                # Вставляем данные (предполагаем, что порядок колонок совпадает)
                cols = list(df.columns)
                placeholders = ",".join(["%s"] * len(cols))
                for _, row in df.iterrows():
                    cur.execute(
                        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})",
                        tuple(row)
                    )
                conn.commit()
                print(f"Импортировано: {table}")
            except Exception as e:
                conn.rollback()
                print(f"Ошибка импорта {table}: {e}")
    cur.close()
    conn.close()

def calculate_order_sum(order_id):

    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT 
            SUM(oi.цена * oi.шт) AS total_sum,
            p.рейтинг,
            (SELECT COALESCE(SUM(сумма), 0) FROM orders 
             WHERE id_partner = o.id_partner AND статус = 'выполнена') AS done_sum
        FROM orders o
        JOIN partners p ON o.id_partner = p.id
        JOIN order_items oi ON oi.id_order = o.id
        WHERE o.id = %s
        GROUP BY o.id, p.рейтинг, o.id_partner;
    """
    cur.execute(query, (order_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or row[0] is None:
        return 0, 0, 0

    total_sum = float(row[0])
    rating = row[1]
    done_sum = float(row[2])

    discount = 0
    if rating >= 5:
        if done_sum >= 50000:
            discount = 10
        elif done_sum >= 10000:
            discount = 5
    
    to_pay = round(total_sum * (1 - discount / 100))
    return total_sum, discount, to_pay

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Партнёры — Северный свет")
        self.root.configure(bg=BG_WHITE)
        self.root.geometry("900x600")
        self.font = (FONT_NAME, FONT_SIZE)
        
        # Загрузка логотипа (если файл есть)
        try:
            self.logo_img = tk.PhotoImage(file="logo.png")
            # Уменьшаем, если слишком большой, сохраняя пропорции
            self.logo_img = self.logo_img.subsample(2, 2) 
        except Exception:
            self.logo_img = None

        self.current_partner_id = None
        self.create_main_window()

    def create_main_window(self):
        """Главное окно: список партнёров и кнопки."""
        self.clear_window()
        
        # Логотип
        if self.logo_img:
            lbl_logo = tk.Label(self.root, image=self.logo_img, bg=BG_WHITE)
            lbl_logo.pack(pady=10)
        
        # Список партнёров
        frame_list = tk.Frame(self.root, bg=BG_WHITE)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.listbox = tk.Listbox(frame_list, font=self.font, bg=BG_BLOCK, 
                                  selectbackground=BTN_COLOR, height=12)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(frame_list, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Кнопки
        btn_frame = tk.Frame(self.root, bg=BG_WHITE)
        btn_frame.pack(pady=10)
        
        self.btn_add = tk.Button(btn_frame, text="Добавить", font=self.font,
                                 bg=BTN_COLOR, fg="white", width=15, command=self.open_add_card)
        self.btn_add.pack(side=tk.LEFT, padx=10)
        
        self.btn_card = tk.Button(btn_frame, text="Карточка", font=self.font,
                                  bg=BTN_COLOR, fg="white", width=15, command=self.open_card)
        self.btn_card.pack(side=tk.LEFT, padx=10)
        
        self.btn_orders = tk.Button(btn_frame, text="Заявки", font=self.font,
                                    bg=BTN_COLOR, fg="white", width=15, command=self.open_orders)
        self.btn_orders.pack(side=tk.LEFT, padx=10)
        
        self.load_partners()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def load_partners(self):
        self.listbox.delete(0, tk.END)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, название, тип, рейтинг FROM partners ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        self.partners_data = rows
        for row in rows:
            self.listbox.insert(tk.END, f"{row[0]}. {row[1]} | {row[2]} | рейтинг {row[3]}")

    def get_selected_partner(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self.partners_data[sel[0]]

    def open_add_card(self):
        self.current_partner_id = None
        self.show_card_window(partner=None)

    def open_card(self):
        partner = self.get_selected_partner()
        if not partner:
            messagebox.showwarning("Внимание", "Выберите партнёра!")
            return
        self.current_partner_id = partner[0]
        self.show_card_window(partner)

    def open_orders(self):
        partner = self.get_selected_partner()
        if not partner:
            messagebox.showwarning("Внимание", "Выберите партнёра!")
            return
        self.current_partner_id = partner[0]
        self.show_order_window(partner)

    def show_card_window(self, partner=None):
        self.clear_window()
        tk.Label(self.root, text="Карточка партнёра", font=(FONT_NAME, 16, "bold"), 
                 bg=BG_WHITE, fg=BTN_COLOR).pack(pady=10)

        frame = tk.Frame(self.root, bg=BG_WHITE)
        frame.pack(pady=20)

        # Поля
        labels = ["Название:", "Тип:", "Телефон:", "Рейтинг:"]
        self.entries = {}
        for i, text in enumerate(labels):
            tk.Label(frame, text=text, font=self.font, bg=BG_WHITE, anchor="w").grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(frame, font=self.font, bg=BG_BLOCK, width=40)
            entry.grid(row=i, column=1, pady=5)
            self.entries[text] = entry

        # Заполнение, если редактируем
        if partner:
            self.entries["Название:"].insert(0, partner[1])
            self.entries["Тип:"].insert(0, partner[2])
            # Телефон и рейтинг нужно достать из БД отдельно
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT телефон, рейтинг FROM partners WHERE id = %s;", (partner[0],))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                self.entries["Телефон:"].insert(0, row[0] or "")
                self.entries["Рейтинг:"].insert(0, str(row[1] or ""))

        # Надпись скидки
        self.lbl_discount = tk.Label(frame, text="Скидка: 0%", font=self.font, bg=BG_WHITE, fg=BTN_COLOR)
        self.lbl_discount.grid(row=4, column=1, sticky="w", pady=10)

        # Кнопки
        btn_frame = tk.Frame(self.root, bg=BG_WHITE)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Назад", font=self.font, bg=BTN_COLOR, fg="white", 
                  width=15, command=self.create_main_window).pack(side=tk.LEFT, padx=10)

        self.btn_save = tk.Button(btn_frame, text="Сохранить", font=self.font, 
                                  bg=BTN_COLOR, fg="white", width=15, command=self.save_partner)
        self.btn_save.pack(side=tk.LEFT, padx=10)

    def save_partner(self):
        name = self.entries["Название:"].get().strip()
        ptype = self.entries["Тип:"].get().strip()
        phone = self.entries["Телефон:"].get().strip()
        rating_str = self.entries["Рейтинг:"].get().strip()

        # Валидация
        if not name:
            messagebox.showerror("Ошибка", "Введите название!")
            return
        if len(phone) != 11 or not phone.isdigit():
            messagebox.showerror("Ошибка", "Телефон должен состоять из 11 цифр!")
            return
        try:
            rating = int(rating_str)
            if not (0 <= rating <= 10):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Рейтинг должен быть числом от 0 до 10!")
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            if self.current_partner_id is None:
                # INSERT
                cur.execute("""
                    INSERT INTO partners (название, тип, телефон, рейтинг)
                    VALUES (%s, %s, %s, %s) RETURNING id;
                """, (name, ptype, phone, rating))
                self.current_partner_id = cur.fetchone()[0]
            else:
                # UPDATE
                cur.execute("""
                    UPDATE partners SET название=%s, тип=%s, телефон=%s, рейтинг=%s
                    WHERE id=%s;
                """, (name, ptype, phone, rating, self.current_partner_id))
            conn.commit()
            
            # Меняем кнопку на зеленую
            self.btn_save.config(bg=BTN_GREEN, text="Сохранено")
            messagebox.showinfo("Успех", "Партнёр сохранён!")
            
            # Обновляем надпись скидки
            self.lbl_discount.config(text=f"Скидка: {self.calculate_discount_for_partner(self.current_partner_id)}%")
            
        except Exception as e:
            conn.rollback()
            self.btn_save.config(bg=BTN_RED, text="Ошибка")
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cur.close()
            conn.close()

    def calculate_discount_for_partner(self, partner_id):
        """Вспомогательный метод для отображения скидки."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT рейтинг FROM partners WHERE id=%s;", (partner_id,))
        rating = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(сумма),0) FROM orders WHERE id_partner=%s AND статус='выполнена';", (partner_id,))
        done_sum = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if rating < 5:
            return 0
        if done_sum >= 50000:
            return 10
        if done_sum >= 10000:
            return 5
        return 0

    def show_order_window(self, partner):
        self.clear_window()
        tk.Label(self.root, text="Заявка", font=(FONT_NAME, 16, "bold"), 
                 bg=BG_WHITE, fg=BTN_COLOR).pack(pady=10)

        frame = tk.Frame(self.root, bg=BG_WHITE)
        frame.pack(pady=20)

        # Партнёр (только чтение)
        tk.Label(frame, text="Партнёр:", font=self.font, bg=BG_WHITE).grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(frame, text=partner[1], font=self.font, bg=BG_BLOCK, width=40, anchor="w").grid(row=0, column=1, pady=5)

        # Изделие (выпадающий список)
        tk.Label(frame, text="Изделие:", font=self.font, bg=BG_WHITE).grid(row=1, column=0, sticky="w", pady=5)
        self.combo_product = ttk.Combobox(frame, font=self.font, width=38)
        self.combo_product.grid(row=1, column=1, pady=5)
        self.load_products()
        self.combo_product.bind("<<ComboboxSelected>>", self.on_product_select)

        # Количество
        tk.Label(frame, text="Количество:", font=self.font, bg=BG_WHITE).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_qty = tk.Entry(frame, font=self.font, bg=BG_BLOCK, width=40)
        self.entry_qty.grid(row=2, column=1, pady=5)

        # Цена
        tk.Label(frame, text="Цена:", font=self.font, bg=BG_WHITE).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_price = tk.Entry(frame, font=self.font, bg=BG_BLOCK, width=40, state="readonly")
        self.entry_price.grid(row=3, column=1, pady=5)

        # Итоговые надписи
        self.lbl_sum = tk.Label(frame, text="Сумма: 0", font=self.font, bg=BG_WHITE, fg=BTN_COLOR)
        self.lbl_sum.grid(row=4, column=1, sticky="w", pady=5)

        self.lbl_discount = tk.Label(frame, text="Скидка: 0%", font=self.font, bg=BG_WHITE, fg=BTN_COLOR)
        self.lbl_discount.grid(row=5, column=1, sticky="w", pady=5)

        self.lbl_to_pay = tk.Label(frame, text="К оплате: 0", font=self.font, bg=BG_WHITE, fg=BTN_COLOR)
        self.lbl_to_pay.grid(row=6, column=1, sticky="w", pady=5)

        # Кнопка "Рассчитать" (для удобства)
        tk.Button(frame, text="Рассчитать", font=self.font, bg=BTN_COLOR, fg="white",
                  command=self.calculate_order).grid(row=7, column=1, sticky="w", pady=10)

        # Кнопки управления
        btn_frame = tk.Frame(self.root, bg=BG_WHITE)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Назад", font=self.font, bg=BTN_COLOR, fg="white", 
                  width=15, command=self.create_main_window).pack(side=tk.LEFT, padx=10)

        self.btn_write = tk.Button(btn_frame, text="Записать", font=self.font, 
                                   bg=BTN_COLOR, fg="white", width=15, command=self.write_order)
        self.btn_write.pack(side=tk.LEFT, padx=10)

    def load_products(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, артикул, цена_для_партнёра FROM products ORDER BY артикул;")
        self.products_data = cur.fetchall()
        cur.close()
        conn.close()
        self.combo_product['values'] = [f"{p[1]} (цена: {p[2]})" for p in self.products_data]
        if self.products_data:
            self.combo_product.current(0)
            self.on_product_select(None)

    def on_product_select(self, event):
        idx = self.combo_product.current()
        if idx >= 0:
            product = self.products_data[idx]
            self.entry_price.config(state="normal")
            self.entry_price.delete(0, tk.END)
            self.entry_price.insert(0, str(product[2]))
            self.entry_price.config(state="readonly")

    def calculate_order(self):
        try:
            qty = int(self.entry_qty.get())
            price = float(self.entry_price.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество!")
            return

        total_sum = qty * price
        self.lbl_sum.config(text=f"Сумма: {total_sum}")

        # Скидка
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT рейтинг FROM partners WHERE id=%s;", (self.current_partner_id,))
        rating = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(сумма),0) FROM orders WHERE id_partner=%s AND статус='выполнена';", (self.current_partner_id,))
        done_sum = float(cur.fetchone()[0])
        cur.close()
        conn.close()

        discount = 0
        if rating >= 5:
            if done_sum >= 50000:
                discount = 10
            elif done_sum >= 10000:
                discount = 5
        
        to_pay = round(total_sum * (1 - discount / 100))
        self.lbl_discount.config(text=f"Скидка: {discount}%")
        self.lbl_to_pay.config(text=f"К оплате: {to_pay}")

    def write_order(self):
        # Проверяем, рассчитано ли
        if "0" in self.lbl_to_pay.cget("text"):
            messagebox.showwarning("Внимание", "Сначала нажмите 'Рассчитать'!")
            return

        idx = self.combo_product.current()
        if idx < 0:
            messagebox.showerror("Ошибка", "Выберите изделие!")
            return
        
        product = self.products_data[idx]
        try:
            qty = int(self.entry_qty.get())
            price = float(product[2])
        except ValueError:
            messagebox.showerror("Ошибка", "Неверное количество!")
            return

        # Извлекаем сумму и скидку из надписей
        total_sum = float(self.lbl_sum.cget("text").split(": ")[1])
        to_pay = float(self.lbl_to_pay.cget("text").split(": ")[1])

        conn = get_connection()
        cur = conn.cursor()
        try:
            # Создаем заявку
            cur.execute("""
                INSERT INTO orders (id_partner, дата, статус, сумма)
                VALUES (%s, CURRENT_DATE, 'новая', %s) RETURNING id;
            """, (self.current_partner_id, to_pay))
            order_id = cur.fetchone()[0]

            # Создаем строку заявки
            cur.execute("""
                INSERT INTO order_items (id_order, id_product, шт, цена)
                VALUES (%s, %s, %s, %s);
            """, (order_id, product[0], qty, price))

            conn.commit()
            self.btn_write.config(bg=BTN_GREEN, text="Записано")
            messagebox.showinfo("Успех", f"Заявка №{order_id} записана!")
        except Exception as e:
            conn.rollback()
            self.btn_write.config(bg=BTN_RED, text="Ошибка")
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    # 1. Создаем БД и таблицы (если их нет)
    create_database_and_tables()
    # 2. Импортируем данные из Excel (если файлы есть)
    import_excel_data()
    
    # 3. Запускаем GUI
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()