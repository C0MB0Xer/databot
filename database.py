# -*- coding: utf-8 -*-
import os
import sqlite3
from pathlib import Path
import pandas as pd

def create_demo_database(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, group_name TEXT, score INTEGER)")
    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO students(name, group_name, score) VALUES(?,?,?)", [
            ("Анна", "ИТ-41", 87), ("Иван", "ИТ-41", 74), ("Мария", "ИТ-42", 96),
            ("Олег", "ИТ-42", 68), ("Елена", "ИТ-41", 91)])
    cur.execute("CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY, title TEXT, hours INTEGER)")
    cur.execute("SELECT COUNT(*) FROM subjects")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO subjects(title, hours) VALUES(?,?)", [
            ("Базы данных", 72), ("Визуализация данных", 36), ("Программирование", 54)])
    con.commit()
    con.close()

def validate_sqlite_path(path):
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return False, f"Файл не найден: {p}"
        con = sqlite3.connect(str(p))
        con.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        con.close()
        return True, f"Подключение успешно: {p}"
    except Exception as e:
        return False, f"Ошибка подключения: {e}"

def inspect_sqlite(path):
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Файл не найден: {p}")
    con = sqlite3.connect(str(p))
    rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    con.close()
    return [r[0] for r in rows]

def read_table(path, table):
    # Идентификатор таблицы экранируется двойными кавычками.
    safe = table.replace('"', '""')
    con = sqlite3.connect(str(Path(path).expanduser()))
    try:
        return pd.read_sql_query(f'SELECT * FROM "{safe}"', con)
    finally:
        con.close()
