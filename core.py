# -*- coding: utf-8 -*-
import os
import re
from dotenv import load_dotenv

def load_env():
    load_dotenv()

def get_openai_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None

NEUTRAL = [
    r"^(привет|здравствуй|доброе утро|добрый день|добрый вечер|хай|здравствуйте)[!. ]*$",
    r"^(как дела|как ты|что делаешь|кто ты|что ты умеешь)[?!. ]*$",
    r"^(спасибо|благодарю|понятно|ок|окей|ладно|пока|до свидания)[!. ]*$"
]
TOPIC = [
    "баз", "данн", "бд", "sql", "sqlite", "mysql", "postgres", "oracle",
    "odbc", "jdbc", "драйвер", "подключ", "соединен", "сервер", "хост",
    "порт", "dataset", "datareader", "datagrid", "таблиц", "запрос",
    "визуализац", "график", "диаграм", "компонент", "форма", "окно",
    "меню", "textbox", "combobox", "button", "label", "panel", "chart",
    "pandas", "источник данных", "управлени данными", "адаптер",
    "пул соединений", "connection string", "entity framework", "свойств"
]

def local_classify(text):
    t = text.lower().strip()
    if any(re.match(p, t) for p in NEUTRAL):
        return "neutral"
    if any(word in t for word in TOPIC):
        return "topic"
    return "other"

def classify_message(text, history, client):
    if client is None:
        return local_classify(text)
    try:
        context = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in history[-6:])
        prompt = f"""Классифицируй сообщение. TOPIC — базы данных, соединения, SQL,
драйверы, перенос/путь БД, компоненты визуализации и управления данными и их свойства.
NEUTRAL — приветствие, благодарность, короткая социальная реплика.
OTHER — всё остальное. Не расширяй тему из-за предыдущего контекста.
Контекст: {context}
Сообщение: {text}
Ответь строго одним словом TOPIC, NEUTRAL или OTHER."""
        r = client.responses.create(model="gpt-4.1-mini", input=prompt)
        v = r.output_text.strip().upper()
        return {"TOPIC":"topic", "NEUTRAL":"neutral", "OTHER":"other"}.get(v, local_classify(text))
    except Exception:
        return local_classify(text)

def neutral_answer(text):
    t = text.lower()
    if "как дела" in t or "как ты" in t:
        return "Отлично, спасибо! 😊 Готов помогать с базами данных. Что изучаем?"
    if "что делаешь" in t:
        return "Помогаю разбираться с подключением к БД, визуализацией и управлением данными. 🤖"
    if "спасибо" in t or "благодар" in t:
        return "Всегда пожалуйста! 😊 Обращайся, если появятся вопросы по теме."
    if "пока" in t or "до свид" in t:
        return "До встречи! Успехов в изучении! 👋"
    if "кто ты" in t or "что ты умеешь" in t:
        return "Я DataBot — учебный помощник по компонентам связи с БД, визуализации и управления данными."
    return "Привет! 😊 Рад тебя видеть. Какую тему по базам данных разберём?"

def off_topic_answer():
    return ("Извини! 😊 Я DataBot — учебный помощник по теме компонентов связи с БД, "
            "визуализации и управления данными. Могу объяснить теорию, свойства компонентов "
            "и привести практические примеры. Давай вернёмся к этой теме!")

def answer_topic(text, history, client):
    if client is None:
        return offline_answer(text)
    try:
        conversation = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
        conversation.append({"role":"user", "content":text})
        instructions = """Ты DataBot, учебный помощник по теме «Компоненты связи с БД.
Компоненты визуализации и управления данными». Отвечай только в рамках темы.
Объясняй простым русским языком, давай примеры и код при необходимости.
Если вопрос неоднозначен, задай уточнение. Не выдумывай источники.
Используй web search для поиска актуальных сведений и указывай реальные ссылки,
если инструмент вернул источники. Не раскрывай и не запрашивай секретные ключи."""
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=instructions,
            tools=[{"type":"web_search_preview"}],
            input=conversation
        )
        return response.output_text
    except Exception as e:
        return ("Не удалось получить ответ GPT. Проверь OPENAI_API_KEY, доступ к API и интернет.\n\n"
                f"Техническая информация: {e}")

def offline_answer(text):
    t = text.lower()
    if "odbc" in t:
        return ("**ODBC** — программный интерфейс доступа к СУБД через драйвер. "
                "Приложение использует общий API, а драйвер конкретной СУБД преобразует вызовы "
                "в подходящий формат.")
    if "jdbc" in t:
        return "**JDBC** — Java API для подключения к базам данных и выполнения SQL-запросов с помощью драйверов."
    if "dataset" in t:
        return ("**DataSet** в ADO.NET — набор данных в памяти: таблицы, связи и ограничения. "
                "Он может использоваться независимо от постоянно открытого соединения.")
    if "datareader" in t:
        return "**DataReader** — объект для последовательного чтения результата запроса, обычно только вперёд и без редактирования."
    if "datagrid" in t or "таблиц" in t:
        return ("**DataGridView** отображает данные в виде строк и столбцов. Частые свойства: "
                "`DataSource`, `ReadOnly`, `AllowUserToAddRows`, `SelectionMode`, `AutoSizeColumnsMode`.")
    if "статичес" in t or "динамичес" in t or "путь" in t or "перенос" in t:
        return ("**Статическое подключение:** путь/строка подключения фиксированы в коде или конфигурации. "
                "**Динамическое:** приложение получает путь или параметры из интерфейса/настроек во время работы. "
                "При переносе SQLite-файла укажи новый путь и проверь подключение.")
    return ("В локальном режиме могу дать базовую справку по ODBC, JDBC, DataSet, DataReader, "
            "SQLite, статическому/динамическому подключению и компонентам интерфейса. "
            "Для развёрнутых ответов и интернет-поиска добавь OpenAI API key в `.env`.")
