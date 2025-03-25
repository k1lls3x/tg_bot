import mysql.connector
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SqlConnection:
    DB_CONFIG = {                   
        "host": "localhost",
        "user": "root",
        "password": "7R8M$JG%=~v~%Z&",
        "database": "keup"  
    }
 #   (AEvoWl(TC#gJk}|

    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(**self.DB_CONFIG)
            self.cursor = self.conn.cursor()
            logging.info("✅ Подключение к MySQL успешно!")
            return self.conn, self.cursor
        except mysql.connector.Error as err:
            logging.error(f"❌ Ошибка подключения: {err}")
            # Можно выбросить исключение, чтобы внешний код знал об ошибке.
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logging.info("🔌 Соединение с MySQL закрыто.")

# Пример использования
if __name__ == '__main__':
    try:
        with SqlConnection() as (conn, cursor):
            # Ваш код работы с БД
            cursor.execute("SELECT * FROM your_table")
            results = cursor.fetchall()
            for row in results:
                print(row)
    except mysql.connector.Error as e:
        logging.error(f"Ошибка во время работы с БД: {e}")
