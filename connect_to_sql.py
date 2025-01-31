import mysql.connector

class SqlConnection:
    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "(AEvoWl(TC#gJk}|",
        "database": "keup"   # Имя базы данных (без .sql!)
    }

    @staticmethod
    def get_connection():
        """
        Подключение к MySQL и выбор базы данных.
        """
        try:
            conn = mysql.connector.connect(**SqlConnection.DB_CONFIG)
            cursor = conn.cursor()
            print("✅ Подключение к MySQL успешно!")
            return conn, cursor
        except mysql.connector.Error as err:
            print(f"❌ Ошибка подключения: {err}")
            return None, None

    @staticmethod
    def close_connection(conn, cursor):
        """
        Закрывает соединение с MySQL.
        """
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("🔌 Соединение с MySQL закрыто.")
