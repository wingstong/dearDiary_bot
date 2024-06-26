import aioodbc
import logging
from app.config import DB_SERVER, DB_DATABASE

async def get_db_connection():
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"Trusted_Connection=yes;"
    )
    try:
        conn = await aioodbc.connect(connection_string)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        return None

async def get_user(username: str, password: str):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT Id_user FROM Users WHERE Username = ? AND Password = ?",
                                     (username, password))
                user = await cursor.fetchone()
        return user
    except Exception as e:
        logging.error(f"Error fetching user: {e}")
        return None

async def check_user_exists(username: str):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT Id_user FROM Users WHERE Username = ?", (username,))
                user = await cursor.fetchone()
        return user
    except Exception as e:
        logging.error(f"Error checking user existence: {e}")
        return None

async def add_user(username: str, password: str, email: str):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("INSERT INTO Users (Username, Password, Email) VALUES (?, ?, ?)",
                                     (username, password, email))
                await conn.commit()
    except Exception as e:
        logging.error(f"Error adding user: {e}")

async def get_tasks(user_id: int):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT Id_task, taskText, deadLine, isComplete FROM TODO WHERE user_id = ?", (user_id,))
                tasks = await cursor.fetchall()
        return tasks
    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return []

async def add_task(task_description: str, task_deadline: str, user_id: int):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("INSERT INTO TODO (taskText, deadLine, isComplete, user_id) VALUES (?, ?, 0, ?)", (task_description, task_deadline, user_id))
                await conn.commit()
    except Exception as e:
        logging.error(f"Error adding task: {e}")

async def toggle_task(task_id: int, new_status: bool):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("UPDATE TODO SET isComplete = ? WHERE Id_task = ?", (new_status, task_id))
                await conn.commit()
    except Exception as e:
        logging.error(f"Error toggling task status: {e}")

async def get_task_status(task_id: int):
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT isComplete FROM TODO WHERE Id_task = ?", (task_id,))
                is_complete = await cursor.fetchone()
        return is_complete[0] if is_complete else None
    except Exception as e:
        logging.error(f"Error fetching task status: {e}")
        return None

async def get_diary_entries():
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT id, entry_date, content FROM diary")
                entries = await cursor.fetchall()
        return entries
    except Exception as e:
        logging
