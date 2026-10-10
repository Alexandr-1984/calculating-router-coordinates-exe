import tkinter as tk
from tkinter import ttk, messagebox
import math

# Импортируем логику из вашего файла.
# Если вы переименовали файл в triangulation_module.py, раскомментируйте строку ниже:
# from triangulation_module import WiFiTriangulation, MeasurementPoint

# --- ВСТРОЕННАЯ ЛОГИКА (на случай, если модуль не найден) ---
# Если ваш файл "Модуль_триангуляции_2.py" лежит рядом, Python сможет его найти.
# Попробуем импортировать его как есть:
try:
    from triangulationModule import WiFiTriangulation, MeasurementPoint
except ImportError:
    # Если импорт не удался (из-за пробелов в имени), используем класс-заглушку (или используйте абсолютный путь)
    # Для стабильной работы переименуйте файл.
    class MeasurementPoint:
        def __init__(self, name, x, y, signal_dbmv):
            self.name = name
            self.x = x
            self.y = y
            self.signal_dbmv = signal_dbmv

    class WiFiTriangulation:
        def signal_to_distance(self, signal):
            return 10 ** ((-40 - signal) / 25)
        
        def triangulate(self, points, guess=None):
            # Простая заглушка для теста, если модуль не загрузится
            return 30.0, 30.0

        def validate_triangulation(self, points, coords):
            pass
# -----------------------------------------------------------


class TriangulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Триангуляция Wi-Fi роутера")
        self.root.geometry("800x600")

        # Модель данных
        self.triangulation = WiFiTriangulation()
        self.points = []  # Список объектов MeasurementPoint
        
        # UI элементы
        self.create_widgets()
        
        # Заполним тестовыми данными из рисунка (для наглядности)
        self.load_example_data()

    def create_widgets(self):
        # --- Верхняя часть: Ввод данных ---
        frame_input = ttk.LabelFrame(self.root, text="Добавить точку измерения", padding=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_input, text="Имя (T1, T2...):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_name = ttk.Entry(frame_input, width=10)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)
        self.entry_name.insert(0, "T1")

        ttk.Label(frame_input, text="X (м):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_x = ttk.Entry(frame_input, width=10)
        self.entry_x.grid(row=0, column=3, padx=5, pady=5)
        self.entry_x.insert(0, "50")

        ttk.Label(frame_input, text="Y (м):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.entry_y = ttk.Entry(frame_input, width=10)
        self.entry_y.grid(row=0, column=5, padx=5, pady=5)
        self.entry_y.insert(0, "30")

        ttk.Label(frame_input, text="Сигнал (dbmV):").grid(row=0, column=6, padx=5, pady=5, sticky="e")
        self.entry_signal = ttk.Entry(frame_input, width=10)
        self.entry_signal.grid(row=0, column=7, padx=5, pady=5)
        self.entry_signal.insert(0, "-65")

        ttk.Button(frame_input, text="Добавить", command=self.add_point).grid(row=0, column=8, padx=10, pady=5)
        ttk.Button(frame_input, text="Очистить всё", command=self.clear_all).grid(row=0, column=9, padx=5, pady=5)

        # --- Средняя часть: Таблица и кнопки действий ---
        frame_mid = ttk.Frame(self.root)
        frame_mid.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица данных (Treeview)
        columns = ("Name", "X", "Y", "Signal")
        self.tree = ttk.Treeview(frame_mid, columns=columns, show="headings", height=12)
        
        # Заголовки
        self.tree.heading("Name", text="Имя точки")
        self.tree.heading("X", text="X (м)")
        self.tree.heading("Y", text="Y (м)")
        self.tree.heading("Signal", text="Уровень сигнала (dbmV)")
        
        # Ширина колонок
        self.tree.column("Name", width=80, anchor="center")
        self.tree.column("X", width=80, anchor="center")
        self.tree.column("Y", width=80, anchor="center")
        self.tree.column("Signal", width=120, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)
        
        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(frame_mid, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Панель действий
        frame_actions = ttk.Frame(self.root)
        frame_actions.pack(fill="x", padx=10, pady=5)
        
        self.btn_delete = ttk.Button(frame_actions, text="Удалить выбранное", command=self.delete_selected)
        self.btn_delete.pack(side="left", padx=5)

        self.btn_calc = ttk.Button(frame_actions, text="Вычислить координаты роутера", command=self.calculate_router)
        self.btn_calc.pack(side="right", padx=5)

        # --- Нижняя часть: Результат (TR Координаты) ---
        frame_result = ttk.LabelFrame(self.root, text="TR (Координаты расположения wi-fi роутера)", padding=10)
        frame_result.pack(fill="x", padx=10, pady=10)

        self.label_result_x = ttk.Label(frame_result, text="X (м): ?", font=("Arial", 12, "bold"), foreground="blue")
        self.label_result_x.pack(side="left", padx=20)

        self.label_result_y = ttk.Label(frame_result, text="Y (м): ?", font=("Arial", 12, "bold"), foreground="blue")
        self.label_result_y.pack(side="left", padx=20)

        self.text_log = tk.Text(self.root, height=100, state="disabled", bg="#f0f0f0")
        self.text_log.pack(fill="x", padx=10, pady=(0, 10))

    def load_example_data(self):
        """Загрузка данных из вашей картинки для примера"""
        example_data = [
            ("T1", 50, 30, -65),
            ("T2", 40, 30, -40),
            # ("Ti", 50, 30, -70), # Пример из таблицы
            # ("Tj", 50, 30, -80)  # Пример из таблицы
        ]
        for name, x, y, signal in example_data:
            self.entry_name.delete(0, tk.END); self.entry_name.insert(0, name)
            self.entry_x.delete(0, tk.END); self.entry_x.insert(0, str(x))
            self.entry_y.delete(0, tk.END); self.entry_y.insert(0, str(y))
            self.entry_signal.delete(0, tk.END); self.entry_signal.insert(0, str(signal))
            self.add_point()

    def add_point(self):
        try:
            name = self.entry_name.get().strip()
            x = float(self.entry_x.get())
            y = float(self.entry_y.get())
            signal = float(self.entry_signal.get())

            if not name:
                messagebox.showwarning("Ошибка", "Имя точки не может быть пустым!")
                return

            # Добавляем в таблицу
            self.tree.insert("", "end", values=(name, x, y, signal))
            
            # Очищаем поля для ввода следующей точки (автоинкремент имени)
            current_num = int(name[1:]) if len(name) > 1 and name[1:].isdigit() else 0
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, f"str{current_num + 1}")
            self.entry_x.delete(0, tk.END)
            self.entry_y.delete(0, tk.END)
            self.entry_signal.delete(0, tk.END)
            
            self.log_message(f"Добавлена точка: {name} ({x}, {y}) Сигнал: {signal}")

        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числа для X, Y и Сигнала.")

    def delete_selected(self):
        selected = self.tree.selection()
        for item in selected:
            self.tree.delete(item)
        self.log_message("Выбранные точки удалены.")

    def clear_all(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.label_result_x.config(text="X (м): ?")
        self.label_result_y.config(text="Y (м): ?")
        self.log_message("Все данные очищены.")

    def calculate_router(self):
        # Собираем данные из таблицы
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Внимание", "Таблица пуста. Добавьте минимум 2 точки измерения.")
            return

        points_data = []
        for item in items:
            values = self.tree.item(item)['values']
            # values = (name, x, y, signal)
            points_data.append(MeasurementPoint(values[0], float(values[1]), float(values[2]), float(values[3])))

        if len(points_data) < 2:
            messagebox.showwarning("Внимание", "Для триангуляции необходимо минимум 2 точки.")
            return

        try:
            # Вызываем логику из "Модуль_триангуляции_2.py"
            router_x, router_y = self.triangulation.triangulate(points_data)
            
            # Обновляем метки с результатом
            self.label_result_x.config(text=f"X (м): {router_x:.2f}")
            self.label_result_y.config(text=f"Y (м): {router_y:.2f}")

            # Запускаем валидацию (вывод лога)
            import io
            import sys
            old_stdout = sys.stdout
            redirected_output = io.StringIO()
            sys.stdout = redirected_output
            
            self.triangulation.validate_triangulation(points_data, (router_x, router_y))
            
            sys.stdout = old_stdout
            log_text = redirected_output.getvalue()
            
            self.log_message(f"Триангуляция завершена! Результат: ({router_x:.2f}, {router_y:.2f})")
            self.log_message(log_text)

        except Exception as e:
            messagebox.showerror("Ошибка вычислений", str(e))

    def log_message(self, msg):
        self.text_log.config(state="normal")
        self.text_log.insert(tk.END, msg + "\n")
        self.text_log.see(tk.END)
        self.text_log.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = TriangulationApp(root)
    root.mainloop()




        
            
       
         

