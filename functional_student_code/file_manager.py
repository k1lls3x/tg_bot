import os
import logging
import requests
import zipfile
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

folder_path = r"D:\\"  # Корневая папка по умолчанию
path_dict = {}

def get_unique_id(path):
    """
    Генерирует уникальный идентификатор для переданного пути
    и сохраняет его в глобальном словаре path_dict.
    """
    try:
        unique_id = str(len(path_dict))
        path_dict[unique_id] = path
        return unique_id
    except Exception as e:
        logging.error(f"Ошибка генерации ID для {path}: {e}")
        return None

class FileManagerBot:
    def __init__(self, bot, main_menu):
        self.bot = bot
        self.main_menu = main_menu  # ссылка на основной объект (меню) бота
        self.register_handlers()

    def register_handlers(self):
        @self.bot.callback_query_handler(func=lambda call: call.data == "main_menu")
        def _main_menu(call):
            try:
                self.bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception as e:
                logging.error(f"Ошибка удаления сообщения: {e}")
            self.main_menu.send_menu(call.message.chat.id)

        @self.bot.callback_query_handler(func=lambda call: call.data == "root_folder")
        def _root_folder(call):
            self.send_folder_contents(call.message.chat.id, call.message.message_id, folder_path)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("folder::"))
        def _folder(call):
            self.handle_folder(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("file::"))
        def _file(call):
            self.handle_file(call)

        # --- Обработчик создания архива ---
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("create_archive::"))
        def create_archive(call):
            """
            Создаёт ZIP-архив из текущей папки (извлекается из path_dict по UID),
            исключая сам создаваемый архив из набора файлов.
            """
            try:
                uid = call.data.split("::")[1]
                current_folder_path = path_dict.get(uid)
                if not current_folder_path:
                    # fallback на корень, если не нашли
                    current_folder_path = folder_path

                if not os.path.exists(current_folder_path):
                    self.bot.send_message(call.message.chat.id, "Папка для архивации не найдена.")
                    return

                if not os.path.isdir(current_folder_path):
                    self.bot.send_message(call.message.chat.id, "Указанный путь не является директорией.")
                    return

                # Получаем название папки (если архивируем корень диска, задаём стандартное имя)
                folder_name = os.path.basename(os.path.normpath(current_folder_path)) or "backup"
                archive_name = f"{folder_name}.zip"

                # Создаём архив в той же папке, но важно пропускать сам архив при архивировании
                archive_path = os.path.join(current_folder_path, archive_name)

                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
                    for root, _, files in os.walk(current_folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Пропускаем сам файл архива, чтобы не вкладывать его в самого себя
                            if file_path == archive_path:
                                continue

                            arcname = os.path.relpath(file_path, current_folder_path)
                            archive.write(file_path, arcname)

                # Проверяем, создался ли архив
                if not os.path.exists(archive_path):
                    self.bot.send_message(call.message.chat.id, "Ошибка: архив не был создан.")
                    return

                # Отправляем архив пользователю
                with open(archive_path, "rb") as file:
                    self.bot.send_document(call.message.chat.id, file)

                os.remove(archive_path)
               

            except Exception as e:
                logging.error(f"Ошибка при создании архива: {e}")
                self.bot.send_message(call.message.chat.id, f"Произошла ошибка: {e}")

    def send_folder_contents(self, chat_id, message_id=None, current_path=None):
        """
        Отправляет список файлов/папок в выбранном каталоге.
        """
        try:
            if current_path is None:
                current_path = folder_path
            
            if not os.path.exists(current_path):
                self.bot.send_message(chat_id, "Указанная папка не существует.")
                return
            
            if not os.path.isdir(current_path):
                self.bot.send_message(chat_id, "Указанный путь не является папкой.")
                return

            markup = InlineKeyboardMarkup()
            items = os.listdir(current_path)

            for item in items:
                full_path = os.path.join(current_path, item)
                unique_id = get_unique_id(full_path)
                if not unique_id:
                    continue

                if os.path.isdir(full_path):
                    markup.add(InlineKeyboardButton(f"📁 {item}", callback_data=f"folder::{unique_id}"))
                elif os.path.isfile(full_path):
                    icon = self.get_file_icon(full_path)
                    markup.add(InlineKeyboardButton(f"{icon} {item}", callback_data=f"file::{unique_id}"))

            # Кнопка "Назад", если есть родительская папка
            parent_folder = os.path.dirname(current_path)
            if parent_folder != current_path:
                parent_id = get_unique_id(parent_folder)
                if parent_id:
                    markup.add(InlineKeyboardButton("⬅ Назад", callback_data=f"folder::{parent_id}"))

            # Кнопка "Главное меню"
            markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))

            # Кнопка "Создать архив" - вшиваем текущую папку
            current_path_uid = get_unique_id(current_path)
            if current_path_uid:
                markup.add(
                    InlineKeyboardButton(
                        "📦 Создать архив",
                        callback_data=f"create_archive::{current_path_uid}"
                    )
                )

            text_message = f"Содержимое папки: {current_path}"
            
            if message_id:
                # Удаляем старое сообщение с клавиатурой, чтобы не плодить разные меню
                try:
                    self.bot.delete_message(chat_id, message_id)
                except Exception as e:
                    logging.error(f"Ошибка удаления сообщения: {e}")
                self.bot.send_message(chat_id, text_message, reply_markup=markup)
            else:
                self.bot.send_message(chat_id, text_message, reply_markup=markup)
        
        except Exception as e:
            logging.error(f"Ошибка отображения содержимого папки {current_path}: {e}")
            self.bot.send_message(chat_id, "Произошла ошибка при открытии папки.")

    def get_file_icon(self, path):
        """
        Возвращает подходящий значок в зависимости
        от расширения файла.
        """
        ext = os.path.splitext(path)[1].lower()
        return {
            '.exe': '👾',
            '.zip': '🗂️', '.rar': '🗂️', '.7z': '🗂️',
            '.docx': '📓',
            '.jpg': '🖼', '.png': '🖼', '.jpeg': '🖼'
        }.get(ext, '📄')

    def handle_folder(self, call):
        """
        Обрабатывает переход в выбранную папку.
        """
        try:
            uid = call.data.split("::")[1]
            path = path_dict.get(uid)
            if path and os.path.isdir(path):
                self.send_folder_contents(
                    call.message.chat.id,
                    call.message.message_id,
                    path
                )
            else:
                self.bot.answer_callback_query(call.id, "Папка не найдена!")
        except Exception as e:
            logging.error(f"Ошибка обработки папки: {e}")

    def handle_file(self, call):
        """
        Обрабатывает открытие/отправку файла.
        """
        try:
            uid = call.data.split("::")[1]
            path = path_dict.get(uid)

            if not path or not os.path.isfile(path):
                self.bot.answer_callback_query(call.id, "Файл недоступен")
                return

            file_size = os.path.getsize(path)
            # Telegram не даёт отправлять файлы > 2 ГБ
            if file_size > 2000 * 1024 * 1024:
                self.bot.send_message(call.message.chat.id, "Файл слишком большой для Telegram (макс. 2 ГБ)")
                return

            url = f"https://api.telegram.org/bot{self.bot.token}/sendDocument"
            with open(path, "rb") as file:
                response = requests.post(
                    url,
                    data={"chat_id": call.message.chat.id},
                    files={"document": file}
                )

            if response.status_code == 200:
                self.bot.answer_callback_query(call.id, "Файл отправлен!")
            else:
                logging.error(f"Ошибка загрузки файла: {response.text}")
                self.bot.send_message(call.message.chat.id, "Ошибка отправки файла")
        
        except Exception as e:
            logging.error(f"Ошибка отправки файла: {e}")
            self.bot.send_message(call.message.chat.id, "Ошибка при отправке файла")
