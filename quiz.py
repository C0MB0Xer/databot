import os
import pandas as pd

QUESTIONS = [
{"question":"Для чего предназначен ODBC?", "options":["Доступ приложения к разным СУБД через драйвер","Построение графиков","Формат изображения"], "correct":0},
{"question":"Что такое JDBC?", "options":["Java API для работы с БД","Тип таблицы","Язык разметки"], "correct":0},
{"question":"Что обычно означает статическое подключение?", "options":["Параметры зафиксированы в коде/конфигурации","Пользователь меняет путь в интерфейсе","База не имеет адреса"], "correct":0},
{"question":"Что характеризует динамическое подключение?", "options":["Параметры можно задать во время работы","Путь нельзя изменить","Нет соединения"], "correct":0},
{"question":"Что нужно изменить при переносе SQLite-файла?", "options":["Путь к файлу","Цвет графика","Заголовок окна"], "correct":0},
{"question":"Для чего используется DataGridView?", "options":["Для отображения данных таблицей","Для хранения пароля","Для запуска ОС"], "correct":0},
{"question":"Какое свойство DataGridView запрещает редактирование?", "options":["ReadOnly","BackColor","Text"], "correct":0},
{"question":"Какой элемент запускает действие при нажатии?", "options":["Button","Label","Panel"], "correct":0},
{"question":"Для чего предназначен ComboBox?", "options":["Выбор значения из списка","Отображение графика","Открытие SQL-сервера"], "correct":0},
{"question":"Что делает BindingSource?", "options":["Посредничает при привязке данных к компонентам","Заменяет СУБД","Шифрует таблицы"], "correct":0},
{"question":"Что важно проверить при смене источника данных для графика?", "options":["Соответствие полей и типов данных","Цвет рабочего стола","Имя пользователя Windows"], "correct":0},
{"question":"Для чего нужен DataReader?", "options":["Последовательное чтение строк результата запроса","Редактирование меню","Построение формы"], "correct":0}
]

def grade_answers(answers):
    score = sum(1 for i, answer in enumerate(answers) if answer == QUESTIONS[i]["options"][QUESTIONS[i]["correct"]])
    return score, len(QUESTIONS)

def save_result(result):
    os.makedirs("data", exist_ok=True)
    path = "data/quiz_results.csv"
    row = pd.DataFrame([result])
    if os.path.exists(path):
        row.to_csv(path, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        row.to_csv(path, index=False, encoding="utf-8-sig")

def load_results():
    path = "data/quiz_results.csv"
    if not os.path.exists(path):
        return pd.DataFrame(columns=["name","email","score","total","percent"])
    return pd.read_csv(path)
