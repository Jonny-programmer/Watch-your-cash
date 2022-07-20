# -*- encoding: UTF-8 -*-
import os
import sys
from time import sleep
from functools import wraps
from pprint import pp
from traceback import print_exception

import plotly.graph_objs as go
import plotly.offline

from PyQt5 import QtWebEngineWidgets
from PyQt5 import uic
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap, QFont, QPalette, QBrush, QDoubleValidator
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import *

import sqlite3
import requests
import csv


def handle_exception(exc_type, exc_value, exc_traceback):
    with open(r"log.txt", "a") as f:
        print_exception(exc_type, exc_value, exc_traceback, file=f)
    return sys.__excepthook__(exc_type, exc_value, exc_traceback)


def dbg(filename):
    # Декоратор, который записывает в файл [filename] входные и выходные параметры функции
    # Нужен для корректной сборки .exe-шника
    def decorator(func):
        @wraps(func)
        def wrapper(*a, **kwa):
            res = func(*a, **kwa)
            with open(filename, "a") as f:
                pp({"Args": a}, stream=f)
                pp({"Kwargs": kwa}, stream=f)
                print("Output: " + res, file=f)
                print("=" * 50, file=f)
            return res
        return wrapper
    return decorator


# @dbg(r"files_resource_path_log.txt")
def resource_path(relative):
    # Чтобы программа всегда могла найти путь к файлам
    # Подменяет путь для .exe-файла, находя местоположение временной папки
    # Например, C:\Users\eremin\AppData\Local\Temp\_MEI92242\data_files\lang.txt
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        """Если вы хотите подключить собственный API-ключ, расскомментируйте 
               следующие две строки"""
        # self.API_KEY = your_api_key
        # self.API_lineedit.setText(self.API_KEY)
        self.API_KEY = None
        # Размеры окна
        self.x = 700
        self.y = 600
        # БД
        self.con, self.cur = None, None
        self.cash = 0
        # Установка языка
        self.lang = "Русский"
        # Загрузка интерфейса
        self.my_setupUI()

    def my_setupUI(self):
        # Создание окна
        self.setWindowTitle("Watch your cash!")
        self.setFixedSize(700, 600)
        # Установка фона
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap(resource_path("backgrounds/vector_5.jpeg"))))
        self.setPalette(palette)
        # Кнопка старта
        self.start_btn = QPushButton("Let's start!", self)
        self.start_btn.setStyleSheet("""QPushButton{font-style: oblique; 
                                        font-weight: bold; border: 1px solid #1DA1F2;
                                        border-radius: 15px; color: #1DA1F2; 
                                        background-color: #fff;}""")
        self.start_btn.resize(100, 50)
        self.start_btn.move(self.x // 2 - 40, self.y // 2 - 20)
        self.start_btn.clicked.connect(self.start_all)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(self.x // 2 - 125, self.y // 2 - 30, 250, 60)
        self.progress.hide()

    def start_all(self):
        # Загрузка
        self.start_btn.hide()
        self.progress.show()
        for count in range(100):
            self.progress.setValue(count)
            sleep(0.001)
        if os.path.isfile(resource_path("data_files/lang.txt")):
            with open(resource_path("data_files/lang.txt"), "r") as lang_file:
                self.lang = lang_file.readlines()[0].strip()
        else:
            with open("data_files/lang.txt", "w") as lang_file:
                lang_file.write("Русский")
                self.lang = "Русский"
        # Реальная загрузка (из .ui файла)
        uic.loadUi(resource_path("templates/MainWindowTemplate.ui"), self)
        self.setCentralWidget(self.gridLayoutWidget)
        self.setWindowTitle("Watch your cash")
        # Подключение БД
        self.con = sqlite3.connect(resource_path("db/cash_data.db"), check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS earnings ("
                         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                         "title VARCHAR(50) NOT NULL,"
                         "summ INTEGER )")
        self.con.commit()
        self.cur.execute("CREATE TABLE IF NOT EXISTS expenses ("
                         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                         "title VARCHAR(50) NOT NULL,"
                         "summ INTEGER )")
        self.con.commit()
        # Установка значений из БД в окошки выбора
        self.earned = [int(el[0]) for el in self.cur.execute("""SELECT summ FROM earnings""").fetchall()]
        earn_cats = [el[0] for el in self.cur.execute("""SELECT title FROM earnings""").fetchall()]
        self.expensed = [int(el[0]) for el in self.cur.execute("""SELECT summ FROM expenses""").fetchall()]
        exp_cats = [el[0] for el in self.cur.execute("""SELECT title FROM expenses""").fetchall()]        
        # Деньги на счету
        self.cash = sum(self.earned) - sum(self.expensed)
        # Настройка QLCDNUmber
        self.balance.setDigitCount(10)
        self.conv_result.setDigitCount(9)
        self.balance.display(self.cash)     
        
        self.tabWidget.usesScrollButtons = True
        # Ставим домашнюю страницу по умолчанию
        self.tabWidget.setCurrentIndex(0)
        # Настройка крутилки выбора фона
        self.dial.setMinimum(1)
        self.dial.setMaximum(7)
        value = 5
        self.dial.setValue(value)
        self.dial.valueChanged.connect(lambda: self.change_background())
        # Поставим ограничение на ввод в поле для конвертации (только числа)
        self.start_value.setValidator(QDoubleValidator()) 
        # Подключение кнопок
        self.add_earning.setFont(QFont("Arial", 18))
        self.add_earning.clicked.connect(self.earn)
        self.add_expense.setFont(QFont("Arial", 18))
        self.add_expense.clicked.connect(self.spend)
        self.delete_all_data.clicked.connect(self.delete_all)
        self.save_settings.clicked.connect(self.save)
        self.btn_convert.clicked.connect(self.convert)
        self.btn_change_places.clicked.connect(self.exchange_places)
        # Cделаем график расходов видимым
        self.update_expenses_plot()
        # Проверка требуемого языка
        if self.lang == "English":
            code_lang = 'en'
            earn_cats.append("Other...")
            exp_cats.append("Other...")
            self.balance_label.setText("Your current balance:")
            self.backg_label.setText("Select a background:")
            self.app_language_label.setText("App language:")
            self.save_settings.setText("Save changes")
            self.delete_all_data.setText("Erase all data")
            self.btn_convert.setText("Convert")
            self.add_earning.setText("Add an earning")
            self.add_expense.setText("Add an expense")
            self.language_menu.setCurrentIndex(1)
            self.tabWidget.setTabText(0, "Homepage")
            self.tabWidget.setTabText(1, "Settings")
            self.tabWidget.setTabText(2, "Currency converter")        
        else:
            code_lang = 'ru'
            earn_cats.append("Другое...")
            exp_cats.append("Другое...")          
        # Установим значения валют в выпадающие меню
        all_currencies = []
        self.choose_earning_category.addItems(earn_cats)
        self.choose_expense_category.addItems(exp_cats)        
        with open(resource_path(f"data_files/currencies_{code_lang}.csv"), "r") as curr_data_file:
            reader = list(csv.reader(curr_data_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL))[1:]
            for line in reader:
                all_currencies.append(f"{line[1]} - {line[0]}")
        self.start_curr.addItems(all_currencies)
        self.res_curr.addItems(all_currencies)
        
    def earn(self):
        # Добавление дохода и запись этого в БД
        if self.lang == 'English':
            money_dialog = ["Input a summ", "How much did you recieve?"]
            category_dialog = ["Input a category", "What category to append?"]
        else:
            money_dialog = ["Введите сумму", "Сколько денег вы получили?"]
            category_dialog = ["Введите категорию", "Какую категорию добавить?"]
        category = self.choose_earning_category.currentText()
        if category not in ("Другое...", "Other..."):
            summ, ok_pressed = QInputDialog.getInt(
                self, money_dialog[0], money_dialog[1],
                20000, 0, 10000000, 1)
            if ok_pressed:
                existing_summ = int(self.cur.execute("""SELECT summ FROM earnings WHERE title=?""",
                                                     (category,)).fetchall()[0][0])
                self.cur.execute("""UPDATE earnings SET summ = ? WHERE title=?;""",
                                 (summ + existing_summ, category))
                self.con.commit()                
        else:
            category, ok_pressed = QInputDialog.getText(self, category_dialog[0], category_dialog[1])
            if ok_pressed:
                summ, ok2_pressed = QInputDialog.getInt(self, money_dialog[0], money_dialog[1],
                                                        20000, 0, 10000000, 1)
                if ok2_pressed:
                    self.cur.execute("""INSERT INTO earnings(title, summ) VALUES (?, ?)""",
                                     (str(category), summ))
                    self.con.commit()
                    self.choose_earning_category.addItem(category)
        self.earned = [int(el[0]) for el in self.cur.execute("""SELECT summ FROM earnings""").fetchall()]
        self.cash = sum(self.earned) - sum(self.expensed)        
        self.balance.display(self.cash)        

    def spend(self):
        # Добавление расхода и запись этого в БД
        if self.lang == 'English':
            money_dialog = ["Input a summ", "How much did you spend?"]
            category_dialog = ["Input a category", "What category to append?"]
        else:
            money_dialog = ["Введите сумму", "Сколько денег вы потратили?"]
            category_dialog = ["Введите категорию", "Какую категорию добавить?"]        
        category_2 = str(self.choose_expense_category.currentText())
        if category_2 not in ("Другое...", "Other..."):
            summ_2, ok_pressed = QInputDialog.getInt(
                self, money_dialog[0], money_dialog[1],
                20000, 0, 10000000, 1)
            if ok_pressed:
                existing_summ_2 = int(self.cur.execute("""SELECT summ 
                FROM expenses 
                WHERE title=?""", (category_2,)).fetchall()[0][0])
                self.con.commit()     
                self.cur.execute("""UPDATE expenses
                SET summ = ? WHERE title=?;""", (summ_2 + int(existing_summ_2), category_2))
                self.con.commit()                
        else:
            category_2, ok_pressed = QInputDialog.getText(self, category_dialog[0], category_dialog[1])
            if ok_pressed:
                summ_2, ok2_pressed = QInputDialog.getInt(self, money_dialog[0], money_dialog[1],
                                                          20000, 0, 10000000, 1)
                if ok2_pressed:
                    self.cur.execute("""INSERT INTO expenses(title, summ) VALUES (?, ?)""",
                                     (str(category_2), summ_2))
                    self.con.commit()                    
                    self.choose_expense_category.addItem(category_2)
                    
        self.expensed = [int(el[0]) for el in self.cur.execute("""SELECT summ FROM expenses""").fetchall()]
        self.cash = sum(self.earned) - sum(self.expensed)        
        self.balance.display(self.cash)
        self.update_expenses_plot()

    def delete_all(self):
        # Cброс до базовых настроек
        try:
            # Закрыть вкладку с графиком расходов
            self.tabWidget.removeTab(3)
        except Exception as e:
            # Если не получилось
            pass        
        pixmap = QPixmap(resource_path("img/splash.png"))
        splash = QSplashScreen(pixmap)
        splash.show()
        if self.lang == "Русский":
            default_earn_categories = ["Зарплата", "Подарок", "Субсидия", "Грант", "Премия"]
            default_exp_categories = ["Книги", "Одежда", "Семья", "Подарки", "Еда", 
                                      "Дорога", "Развлечения/отдых", "Лечение", "ЖКХ"]
        else:
            default_earn_categories = ["Salary", "Present", "Subsidy", "Grant", "Premium"]
            default_exp_categories = ["Books", "Clothes", "Family", "Presents", 
                                      "Food", "Road", "Entertainments", 
                                      "Treatment", "Communal services"]
        # Обновление соединения
        self.con.close()
        sleep(1)
        self.con = sqlite3.connect(resource_path('db/cash_data.db'), check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS earnings ("
                         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                         "title VARCHAR(50) NOT NULL,"
                         "summ INTEGER )")
        self.con.commit()
        self.cur.execute("""DELETE FROM earnings""")
        self.con.commit()
        self.cur.execute("CREATE TABLE IF NOT EXISTS expenses ("
                         "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                         "title VARCHAR(50) NOT NULL,"
                         "summ INTEGER )")
        self.con.commit()
        self.cur.execute("""DELETE FROM expenses""")
        self.con.commit()
        for i in range(len(default_earn_categories)):
            self.cur.execute("""INSERT INTO earnings(title, summ) 
            VALUES (?, ?)""", (default_earn_categories[i], 0))
            self.con.commit()
        for i in range(len(default_exp_categories)):
            self.cur.execute("""INSERT INTO expenses(title, summ) 
            VALUES (?, ?)""", (default_exp_categories[i], 0))
            self.con.commit() 
        self.earned = [0]
        self.expensed = [0]
        self.cash = 0
        self.balance.display("0")
        
        earn_cats = [el[0] for el in self.cur.execute("""SELECT title FROM earnings""").fetchall()]
        self.choose_earning_category.clear()
        self.choose_earning_category.addItems(earn_cats)
        exp_cats = [el[0] for el in self.cur.execute("""SELECT title FROM expenses""").fetchall()]
        if self.lang == "Русский":
            earn_cats.append("Другое...")            
            exp_cats.append("Другое...")  
        else:
            earn_cats.append("Other...")        
            exp_cats.append("Other...")        
        self.choose_expense_category.clear()
        self.choose_expense_category.addItems(exp_cats)
        sleep(1)
        splash.finish(self)

    def change_background(self):
        # Изменение фона
        value = int(self.dial.value())
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap(resource_path(f"vector_{value}.jpeg"))))
        self.setPalette(palette)        

    def update_expenses_plot(self):
        # Обновление (создание) графика расходов
        try:
            self.tabWidget.removeTab(3)
        except Exception as e:
            # Если не получилось
            pass
        # Если получилось
        exps = {el[0]: int(el[1]) for el in self.cur.execute("""SELECT title, summ FROM expenses""").fetchall()}
        check = []
        for key, val in exps.items():
            if val == 0:
                check.append(key)
        for i in check:
            del exps[i]
        if exps:
            fig = go.Figure()        
            pull = [0] * len(exps)
            search_val = max(exps.values())
            maximum_value_ind = [idx for idx, smth in enumerate(exps.items()) if smth[1]==search_val][0]
            pull[maximum_value_ind] = 0.1  
            fig.add_trace(go.Pie(values=list(exps.values()),
                                 labels=list(exps.keys()),
                                 pull=pull, hole=0.3))
            graph_expenses = PlotlyViewer(fig)
            if self.lang == "English":
                self.tabWidget.addTab(graph_expenses, 'Expenses schedule') 
            else:
                self.tabWidget.addTab(graph_expenses, 'Информация о расходах') 
            
    def save(self):
        # Перевод приложения на русский/английский языки
        lang = self.language_menu.currentText()      
        if lang == "English":
            self.lang = 'English'
            self.balance_label.setText("Your current balance:")
            self.backg_label.setText("Select a background:")
            self.app_language_label.setText("App language:")
            self.save_settings.setText("Save changes")
            self.delete_all_data.setText("Erase all data")
            self.btn_convert.setText("Convert")
            self.add_earning.setText("Add an earning")
            self.add_expense.setText("Add an expense")
            
            default_earn_categories = (("Salary", 1), ("Present", 2), ("Subsidy", 3), 
                                       ("Grant", 4), ("Premium", 5))
            default_exp_categories = (("Books", 1), ("Clothes", 2), ("Family", 3), ("Presents", 4), 
                                      ("Food", 5), ("Road", 6), ("Entertainments", 7), 
                                      ("Treatment", 8), ("Communal services", 9))
            # Обновление соединения
            self.con.commit()
            self.cur.executemany("""UPDATE earnings SET title=? WHERE id=?""",
                                 default_earn_categories)
            self.con.commit()
            self.cur.executemany("""UPDATE expenses SET title=? WHERE id=?""",
                                 default_exp_categories)
            self.con.commit()
            # Обновление выпадающих списков
            earn_cats = [el[0] for el in self.cur.execute("""SELECT title FROM earnings""").fetchall()]
            earn_cats.append("Other...")        
            exp_cats = [el[0] for el in self.cur.execute("""SELECT title FROM expenses""").fetchall()]
            exp_cats.append("Other...")        
            all_currs = []
            with open(resource_path(f"currencies_en.csv"), "r") as curr_data_file:
                reader = list(csv.reader(curr_data_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, encoding='UTF-8'))[1:]
                for line in reader:
                    all_currs.append(f"{line[1]} - {line[0]}")
            self.tabWidget.setTabText(0, "Homepage")
            self.tabWidget.setTabText(1, "Settings")
            self.tabWidget.setTabText(2, "Currency converter")
            try:
                self.tabWidget.setTabText(3, "Expenses schedule")
            except Exception as e:
                pass          
        else:
            self.lang = 'Русский'
            self.balance_label.setText("Ваш текущий баланс:")
            self.backg_label.setText("Выберите фон:")
            self.app_language_label.setText("Язык приложения:")
            self.save_settings.setText("Сохранить изменения")
            self.delete_all_data.setText("Очистить все данныe")
            self.btn_convert.setText("Перевести")
            self.add_earning.setText("Добавить доход")
            self.add_expense.setText("Добавить расход")
            
            default_earn_categories = (("Зарплата", 1), ("Подарок", 2), ("Субсидия", 3), 
                                       ("Грант", 4), ("Премия", 5))
            default_exp_categories = (("Книги", 1), ("Одежда", 2), ("Семья", 3), ("Подарки", 4), 
                                      ("Еда", 5), ("Дорога", 6), ("Развлечения/отдых", 7), 
                                      ("Лечение", 8), ("ЖКХ", 9))
            # Обновление соединения
            self.con.commit()            
            self.cur.executemany("""UPDATE earnings SET title=? WHERE id=?""",
                                 default_earn_categories)
            self.con.commit()            
            self.cur.executemany("""UPDATE expenses SET title=? WHERE id=?""",
                                 default_exp_categories)
            self.con.commit()
            # Обновление выпадающих списков
            self.choose_earning_category.clear()
            self.choose_expense_category.clear()
            
            earn_cats = [el[0] for el in self.cur.execute("""SELECT title FROM earnings""").fetchall()]
            earn_cats.append("Другое...")        
            exp_cats = [el[0] for el in self.cur.execute("""SELECT title FROM expenses""").fetchall()]
            exp_cats.append("Другое...")
            all_currs = []
            with open(resource_path(f"currencies_ru.csv"), "r") as curr_data_file:
                reader = list(csv.reader(curr_data_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, encoding='UTF-8'))[1:]
                for line in reader:
                    all_currs.append(f"{line[1]} - {line[0]}")
            self.tabWidget.setTabText(0, "Домашняя страница")
            self.tabWidget.setTabText(1, "Настройки")
            self.tabWidget.setTabText(2, "Конвертер валют")
            try:
                self.tabWidget.setTabText(3, "Информация о расходах")
            except Exception as e:
                pass
        # Обновление выпадающих списков категорий
        self.choose_earning_category.clear()
        self.choose_expense_category.clear()                    
        self.choose_earning_category.addItems(earn_cats)
        self.choose_expense_category.addItems(exp_cats)
        # Обновление выпадающих списков валют    
        self.start_curr.clear()
        self.res_curr.clear()
        self.start_curr.addItems(all_currs)
        self.res_curr.addItems(all_currs)            
        self.tabWidget.setCurrentIndex(0)
        with open('data_files/lang.txt', "w") as lang_place:
            lang_place.write(self.lang)
        self.con.commit()
        self.update_expenses_plot()
        
    def convert(self):
        # Конвертирование валют
        curr_from = self.start_curr.currentText().strip()[-3:]
        curr_to = self.res_curr.currentText().strip()[-3:]
        if not self.API_KEY:
            self.API_KEY = self.API_lineedit.text()
        """ 
        По умолчанию:
        f936e6b9bd9014380b12ac3bbb882d94
        """
        # Think of user changing the key....
        amount = float(self.start_value.text().strip().replace(",", "."))
        url = f'http://api.currencylayer.com/live?access_key={self.API_KEY}&currencies={curr_from},{curr_to}&format=1'
        data = requests.get(url).json()
        if not data["success"]:
            self.conv_result.display("Error")
            self.error_lbl.setText(f"Error {data['error']['code']}: {data['error']['info']}")
        else:
            rate_1st_to_USD = data['quotes']['USD' + curr_from]
            rate_2nd_to_USD = data['quotes']['USD' + curr_to]
            USDS = amount / rate_1st_to_USD
            ans = round(USDS * rate_2nd_to_USD, 3)
            self.conv_result.display(str(ans))
            
    def exchange_places(self):
        # self..setCurrentIndex
        # Обмен местами названий валют в поле конвертации 
        ind_1 = self.start_curr.currentIndex()
        ind_2 = self.res_curr.currentIndex()
        self.start_curr.setCurrentIndex(ind_2)
        self.res_curr.setCurrentIndex(ind_1)
        res_val = str(self.conv_result.value())
        start_val = self.start_value.text()
        self.start_value.setText(res_val)
        self.conv_result.display(start_val)
    

class PlotlyViewer(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, fig, exec=True):        
        # Создать QApplication instance или использовать существующий, если он есть
        self.app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)
        super().__init__()
        self.file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), resource_path("temp.html")))
        plotly.offline.plot(fig, filename=self.file_path, auto_open=False)
        self.load(QUrl.fromLocalFile(self.file_path))
        self.show()
        if exec:
            self.app.exec_()

    def closeEvent(self, event):
        os.remove(self.file_path)


if __name__ == '__main__':
    sys.excepthook = handle_exception
    app = QApplication(sys.argv)
    main_window = Window()
    main_window.show()
    sys.exit(app.exec_())