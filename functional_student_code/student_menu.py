import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from .file_manager import FileManagerBot

class TelegramBot:
    def __init__(self, bot):
        self.bot = bot
        self.file_manager = FileManagerBot(bot,self)
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
        """Функция отправки главного меню"""
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

        try:
            with open("photos\\menu.jpg", "rb") as photo:
                self.bot.send_photo(
                    chat_id,
                    photo,
                    caption="Главное меню.",
                    reply_markup=markup
                )
        except FileNotFoundError:
            self.bot.send_message(chat_id, "Ошибка: Файл menu.jpg не найден.")
