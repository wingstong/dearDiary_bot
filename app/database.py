import pyodbc
from app.config import DB_SERVER, DB_DATABASE


def get_db_connection():
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(connection_string)
    return conn

def get_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id_user FROM Users WHERE Username = ? AND Password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def check_user_exists(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id_user FROM Users WHERE Username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(username, password, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (Username, Password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id_task, taskText, deadLine, isComplete FROM TODO WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def add_task(task_description, task_deadline, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO TODO (taskText, deadLine, isComplete, user_id) VALUES (?, ?, 0, ?)",
                   (task_description, task_deadline, user_id))
    conn.commit()
    conn.close()

def toggle_task(task_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE TODO SET isComplete = ? WHERE Id_task = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def get_task_status(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT isComplete FROM TODO WHERE Id_task = ?", (task_id,))
    is_complete = cursor.fetchone()[0]
    conn.close()
    return is_complete

def get_diary_entries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, entry_date, content FROM diary")
    entries = cursor.fetchall()
    conn.close()
    return entries