import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .file_manager import FileManagerBot

# Храним ID последнего сообщения меню для каждого пользователя
last_menu_message = {}

class TelegramBot:
    def __init__(self, bot):
        self.bot = bot
        self.file_manager = FileManagerBot(bot, self)
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.callback_query_handler(func=lambda call: call.data == "files")
        def handle_show_directories(call):
            """Обработчик кнопки 'Методички 📄'"""
            self.file_manager.send_folder_contents(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
            )

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            """Обработчик всех остальных кнопок"""
            responses = {
                "cabinet": "Soon... 🆔",
                "faq": "Soon... ❗",
                "guarantee": "Soon... ✅",
                "reviews": "Soon... 📢",
                "support": "Soon...👨‍💻",
                "topup": "Soon... "
            }
            response = responses.get(call.data, "Неизвестная команда")
            self.bot.send_message(call.message.chat.id, response)

    def send_menu(self, chat_id):
    # Удаляем предыдущее меню, если оно есть
        # if chat_id in last_menu_message:
        #     try:
        #         self.bot.delete_message(chat_id, last_menu_message[chat_id])
        #     except telebot.apihelper.ApiException as e:
        #         print(f"Ошибка удаления предыдущего меню: {e}")
        #     finally:
        #         del last_menu_message[chat_id]

        # Создаём разметку клавиатуры
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Методички 📄", callback_data="files"),
            InlineKeyboardButton("Soon... 🆔", callback_data="cabinet"),
            InlineKeyboardButton("Soon... ❗", callback_data="faq"),
            InlineKeyboardButton("Soon... ✅", callback_data="guarantee"),
            InlineKeyboardButton("Soon... 📢", callback_data="reviews"),
            InlineKeyboardButton("Soon... 👨‍💻", callback_data="support"),
        )
        markup.add(InlineKeyboardButton("Soon...", callback_data="topup"))

        # Отправляем новое меню
        try:
            with open("photos\\menu.jpg", "rb") as photo:
                sent_message = self.bot.send_photo(
                    chat_id,
                    photo,
                    caption="Главное меню.",
                    reply_markup=markup
                )
                # Сохраняем ID нового меню
                last_menu_message[chat_id] = sent_message.message_id
                return sent_message  # <--- Добавляем return
        except FileNotFoundError:
            self.bot.send_message(chat_id, "Ошибка: Файл menu.jpg не найден.")
            sent_message = self.bot.send_message(chat_id, "📌 Главное меню", reply_markup=markup)
            last_menu_message[chat_id] = sent_message.message_id
            return sent_message


