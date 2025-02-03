import logging
import os

class Logs:
    def __init__(self):
        # Удаляем все существующие обработчики логирования
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        log_dir = "logs"
        log_file = os.path.join(log_dir, "bot_errors.log")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Создаём обработчик для записи в файл с поддержкой UTF-8
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Создаём кастомный логгер
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.ERROR)

        # Удаляем **все** обработчики, включая StreamHandler (консольный вывод)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Добавляем только FileHandler, который пишет в файл
        self.logger.addHandler(file_handler)

    def error(self, message):
        """Логирование ошибок"""
        self.logger.error(message)

    def warning(self, message):
        """Логирование предупреждений"""
        self.logger.warning(message)

    def info(self, message):
        """Логирование информационных сообщений"""
        self.logger.info(message)
