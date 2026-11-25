# -*- coding: utf-8 -*-
"""DataBot: учебный помощник и локальный конструктор БД."""
import os
import uuid
from pathlib import Path
import streamlit as st
from databot.core import (
    classify_message, answer_topic, neutral_answer, off_topic_answer,
    get_openai_client, load_env
)
from databot.database import (
    create_demo_database, inspect_sqlite, read_table, validate_sqlite_path
)
from databot.quiz import QUESTIONS, grade_answers, save_result, load_results
from databot.lessons import LESSONS, COMPONENTS

load_env()
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = DATA_DIR / "demo.sqlite"
if not DEFAULT_DB.exists():
    create_demo_database(str(DEFAULT_DB))

st.set_page_config(page_title="DataBot", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

if "chat" not in st.session_state:
    st.session_state.chat = []
if "db_path" not in st.session_state:
    st.session_state.db_path = str(DEFAULT_DB)
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

client = get_openai_client()

with st.sidebar:
    st.title("🤖 DataBot")
    st.caption("Компоненты связи с БД, визуализации и управления данными")
    page = st.radio(
        "Навигация",
        ["💬 Чат", "📚 Обучение", "🔌 Конструктор подключения", "📊 Визуализация",
         "🧩 Компоненты и свойства", "🌿 Ветвления", "📝 Итоговый тест", "📈 Результаты"]
    )
    st.divider()
    if client:
        st.success("OpenAI API: подключён")
    else:
        st.warning("Режим без ИИ: для свободных ответов и интернет-поиска нужен API-ключ")
    st.caption("Подключение SQLite и демонстрационные данные доступны без API.")
    if st.button("Очистить историю чата", use_container_width=True):
        st.session_state.chat = []
        st.rerun()

if page == "💬 Чат":
    st.title("DataBot")
    st.caption("Задавай вопросы по теме. На приветствия и благодарности бот отвечает обычно; посторонние темы вежливо перенаправляет.")
    for item in st.session_state.chat:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    prompt = st.chat_input("Напиши вопрос о базах данных или компонентах...")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        category = classify_message(prompt, st.session_state.chat[:-1], client)
        if category == "neutral":
            reply = neutral_answer(prompt)
        elif category == "other":
            reply = off_topic_answer()
        else:
            reply = answer_topic(prompt, st.session_state.chat[:-1], client)
        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.rerun()
    st.markdown("**Примеры вопросов**")
    cols = st.columns(3)
    examples = ["Что такое ODBC и JDBC?", "Чем статическое подключение отличается от динамического?",
                "Какие свойства есть у DataGridView?"]
    for col, question in zip(cols, examples):
        if col.button(question, use_container_width=True):
            st.session_state.chat.append({"role": "user", "content": question})
            category = classify_message(question, st.session_state.chat[:-1], client)
            reply = answer_topic(question, st.session_state.chat[:-1], client) if category == "topic" else neutral_answer(question)
            st.session_state.chat.append({"role": "assistant", "content": reply})
            st.rerun()

elif page == "📚 Обучение":
    st.title("Учебные разделы")
    st.write("Выбирай раздел. После изучения можно перейти к проверке знаний.")
    for title, body in LESSONS.items():
        with st.expander(title):
            st.markdown(body)
    st.info("Совет: попроси DataBot привести пример на Python, C# или SQL — в зависимости от вопроса.")

elif page == "🔌 Конструктор подключения":
    st.title("Конструктор подключения к БД")
    st.markdown("""
    Здесь можно **самостоятельно изменить путь** к файлу SQLite и проверить соединение.
    Это демонстрирует динамическую настройку: приложение получает новый путь из поля ввода,
    а не требует переписывания исходного кода.
    """)
    c1, c2 = st.columns([2, 1])
    with c1:
        path = st.text_input("Путь к файлу SQLite", value=st.session_state.db_path,
                             help="Например: D:/Databases/university.db")
        st.session_state.db_path = path
    with c2:
        st.write("")
        st.write("")
        if st.button("Создать демонстрационную БД", type="primary", use_container_width=True):
            create_demo_database(str(DEFAULT_DB))
            st.session_state.db_path = str(DEFAULT_DB)
            st.success("Демонстрационная база создана.")
            st.rerun()
    uploaded = st.file_uploader("Или перенеси БД в приложение: загрузи файл .db / .sqlite", type=["db", "sqlite", "sqlite3"])
    if uploaded:
        upload_dir = DATA_DIR / "imported" / str(st.session_state.setdefault("session_id", uuid.uuid4().hex))
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(uploaded.name).name
        target = str(upload_dir / safe_name)
        with open(target, "wb") as f:
            f.write(uploaded.getbuffer())
        st.session_state.db_path = target
        st.success(f"Файл загружен. Новый путь: {target}")
    a, b = st.columns(2)
    with a:
        if st.button("Проверить подключение", use_container_width=True):
            ok, message = validate_sqlite_path(st.session_state.db_path)
            (st.success if ok else st.error)(message)
    with b:
        if st.button("Вернуть путь демонстрационной БД", use_container_width=True):
            st.session_state.db_path = str(DEFAULT_DB)
            st.rerun()
    st.subheader("Статическая и динамическая связь")
    st.markdown("""
    - **Статическая:** путь зафиксирован в исходном коде/конфигурации. При переносе файла приходится менять конфигурацию или код.
    - **Динамическая:** путь хранится в настройке интерфейса и может быть изменён пользователем во время работы.
    - **Переносимая:** файл БД можно скопировать в другую папку/на другой компьютер, затем указать новый путь и проверить подключение.

    В этом учебном модуле реализована динамическая смена пути к SQLite-файлу. Для MySQL/PostgreSQL нужны серверные адреса,
    учётные данные и соответствующие драйверы; реальные пароли не вводи в демонстрационную работу.
    """)
    try:
        tables = inspect_sqlite(st.session_state.db_path)
        if tables:
            st.write("Таблицы в выбранной базе:", ", ".join(tables))
    except Exception:
        pass

elif page == "📊 Визуализация":
    st.title("Визуализация данных")
    try:
        tables = inspect_sqlite(st.session_state.db_path)
        if not tables:
            st.warning("В базе нет таблиц. Создай демонстрационную БД в конструкторе подключения.")
        else:
            table = st.selectbox("Выбери таблицу", tables)
            df = read_table(st.session_state.db_path, table)
            st.subheader(f"Таблица: {table}")
            st.dataframe(df, use_container_width=True, hide_index=True)
            numeric = list(df.select_dtypes(include="number").columns)
            if numeric and len(df.columns) >= 2:
                import plotly.express as px
                x_col = st.selectbox("Поле категорий (X)", list(df.columns))
                y_col = st.selectbox("Числовое поле (Y)", numeric)
                kind = st.selectbox("Вид графика", ["Столбчатая диаграмма", "Линейный график", "Круговая диаграмма"])
                if kind == "Столбчатая диаграмма":
                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} по {x_col}")
                elif kind == "Линейный график":
                    fig = px.line(df, x=x_col, y=y_col, markers=True, title=f"{y_col} по {x_col}")
                else:
                    fig = px.pie(df, names=x_col, values=y_col, title=f"Распределение {y_col}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Для графика нужна числовая колонка и поле категорий.")
    except Exception as e:
        st.error(f"Не удалось прочитать базу: {e}")
        st.caption("Проверь путь и формат SQLite-файла в разделе «Конструктор подключения».")

elif page == "🧩 Компоненты и свойства":
    st.title("Компоненты визуализации и управления данными")
    st.caption("Справочник описывает распространённые компоненты Windows Forms (.NET), их назначение, свойства и события.")
    for name, data in COMPONENTS.items():
        with st.expander(name):
            st.markdown(data)

elif page == "🌿 Ветвления":
    st.title("Ветвления учебного сценария")
    st.write("Выбери вариант — сценарий перейдёт по соответствующей ветке.")
    if "branch" not in st.session_state:
        st.session_state.branch = "start"
    branch = st.session_state.branch
    if branch == "start":
        st.info("Привет! Что хочешь изучить?")
        c1, c2, c3 = st.columns(3)
        if c1.button("Подключение к БД"):
            st.session_state.branch = "connection"
            st.rerun()
        if c2.button("Визуализация"):
            st.session_state.branch = "visual"
            st.rerun()
        if c3.button("Компоненты"):
            st.session_state.branch = "components"
            st.rerun()
    elif branch == "connection":
        st.subheader("Подключение к БД")
        st.markdown("Путь к SQLite-файлу можно изменить в конструкторе. Какой тип связи позволяет менять параметр без редактирования исходного кода?")
        choice = st.radio("Выбери ответ", ["Статическая", "Динамическая", "Нет связи"], key="branch_conn")
        if st.button("Проверить ответ"):
            if choice == "Динамическая":
                st.success("Верно! Пользователь меняет путь через интерфейс.")
                st.session_state.branch = "start"
            else:
                st.error("Попробуй ещё раз. Подсказка: параметр задаётся во время работы приложения.")
            st.rerun()
    elif branch == "visual":
        st.subheader("Визуализация")
        st.markdown("Какой компонент показывает записи в виде строк и столбцов?")
        choice = st.radio("Выбери ответ", ["DataGridView", "TextBox", "MenuStrip"], key="branch_visual")
        if st.button("Проверить ответ"):
            if choice == "DataGridView":
                st.success("Правильно! DataGridView отображает табличные данные.")
                st.session_state.branch = "start"
            else:
                st.error("Неверно. Подумай, какой компонент предназначен для таблиц.")
            st.rerun()
    else:
        st.subheader("Компоненты")
        st.markdown("Какой компонент обычно запускает действие при нажатии?")
        choice = st.radio("Выбери ответ", ["Label", "Button", "Panel"], key="branch_components")
        if st.button("Проверить ответ"):
            if choice == "Button":
                st.success("Верно! Событие Click обрабатывает нажатие.")
                st.session_state.branch = "start"
            else:
                st.error("Попробуй ещё раз. Это элемент управления с событием Click.")
            st.rerun()
    if st.button("Вернуться в начало сценария"):
        st.session_state.branch = "start"
        st.rerun()

elif page == "📝 Итоговый тест":
    st.title("Итоговый тест")
    st.write("Укажи имя и электронную почту, затем ответь на вопросы.")
    with st.form("final_quiz"):
        name = st.text_input("Имя участника")
        email = st.text_input("Электронная почта")
        answers = []
        for i, q in enumerate(QUESTIONS):
            answers.append(st.radio(f"{i+1}. {q['question']}", q["options"], key=f"final_{i}"))
        submitted = st.form_submit_button("Завершить тест")
    if submitted:
        score, total = grade_answers(answers)
        percent = round(score / total * 100)
        result = {"name": name.strip(), "email": email.strip(), "score": score,
                  "total": total, "percent": percent}
        save_result(result)
        st.session_state.quiz_result = result
        st.success(f"Тест завершён: {score}/{total} ({percent}%).")
        st.write("Результат:", "Отлично" if percent >= 90 else "Хорошо" if percent >= 70 else "Нужно повторить материал.")
        st.info("Локальная версия сохраняет результаты в CSV. Для настоящей отправки в Google Sheets нужна отдельная авторизация Google и настройка интеграции.")

elif page == "📈 Результаты":
    st.title("Результаты тестирования")
    df = load_results()
    if df.empty:
        st.info("Результатов пока нет. Пройди итоговый тест.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.metric("Участников", len(df))
        st.metric("Средний результат", f"{df['percent'].mean():.1f}%")
        st.download_button("Скачать CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="databot_results.csv", mime="text/csv")

st.divider()
st.caption("DataBot — учебный проект. Не вводи реальные пароли и секретные ключи в чат.")
