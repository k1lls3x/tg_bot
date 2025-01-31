import os
import logging
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

folder_path = r"A:\\test"
path_dict = {}

def get_unique_id(path):
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
        self.main_menu = main_menu  # Теперь FileManagerBot ссылается на TelegramBot
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

    def send_folder_contents(self, chat_id, message_id=None, current_path=None):
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

            parent_folder = os.path.dirname(current_path)
            if parent_folder != current_path:
                parent_id = get_unique_id(parent_folder)
                if parent_id:
                    markup.add(InlineKeyboardButton("⬅ Назад", callback_data=f"folder::{parent_id}"))

            markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
            
            text_message = f"Содержимое папки: {current_path}"
            
            if message_id:
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
        ext = os.path.splitext(path)[1].lower()
        return {
            '.exe': '👾',
            '.zip': '🗂️', '.rar': '🗂️', '.7z': '🗂️',
            '.docx': '📓',
            '.jpg': '🖼', '.png': '🖼', '.jpeg': '🖼'
        }.get(ext, '📄')

    def handle_folder(self, call):
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
        try:
            uid = call.data.split("::")[1]
            path = path_dict.get(uid)

            if not path or not os.path.isfile(path):
                self.bot.answer_callback_query(call.id, "Файл недоступен")
                return

            file_size = os.path.getsize(path)

            if file_size > 2000 * 1024 * 1024:
                self.bot.send_message(call.message.chat.id, "Файл слишком большой для Telegram (макс. 2 ГБ)")
                return

            url = f"https://api.telegram.org/bot{self.bot.token}/sendDocument"
            with open(path, "rb") as file:
                response = requests.post(
                url,
                data={"chat_id": call.message.chat.id},  # <-- Добавляем chat_id
                files={"document": file}
                )

            if response.status_code == 200:
                file_id = response.json().get("result", {}).get("document", {}).get("file_id")
                if file_id:
                    self.bot.send_document(call.message.chat.id, file_id, caption=f"Файл: {os.path.basename(path)}")
                else:
                    self.bot.send_message(call.message.chat.id, "Ошибка получения File ID")
            else:
                logging.error(f"Ошибка загрузки файла в Telegram API: {response.text}")
                self.bot.send_message(call.message.chat.id, "Ошибка загрузки файла")

        except Exception as e:
            logging.error(f"Ошибка отправки файла: {e}")
            self.bot.send_message(call.message.chat.id, "Ошибка при отправке файла")
