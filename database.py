import sqlite3

# Создаем базу данных
conn = sqlite3.connect('messenger.db')
cursor = conn.cursor()

# Создаем таблицу
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        text TEXT
    )
''')

conn.commit()
conn.close()
print("База данных успешно создана!")