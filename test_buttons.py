import logging
import os
import random

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from database import session, User

load_dotenv()
token = os.getenv('TOKEN')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def get_random_exclude(exclude, max_digit):
    rand_integer = random.randint(0, max_digit)
    return get_random_exclude(exclude, max_digit) if rand_integer in exclude else rand_integer


# Функция, которая будет вызываться при получении команды /start
def testing_words(update, context):
    # Создаем клавиатуру с кнопкой
    user = session.query(User).filter(User.id_user == update.effective_chat.id).first()
    translates = user.translates
    count_words = len(translates)
    first = get_random_exclude([None], (count_words - 1))
    second = get_random_exclude([first], (count_words - 1))
    third = get_random_exclude([first, second], (count_words - 1))
    target_word = translates[first].russian_expression
    first_answer = get_random_exclude([None], 2)
    second_answer = get_random_exclude([first_answer], 2)
    third_answer = get_random_exclude([first_answer, second_answer], 2)
    answers = [translates[first], translates[second], translates[third]]
    keyboard = [[InlineKeyboardButton(answers[first_answer].russian_expression, callback_data=(
        'correct' if answers[first_answer].russian_expression == target_word else 'wrong'))],
                [InlineKeyboardButton(answers[second_answer].russian_expression, callback_data=(
                    'correct' if answers[second_answer].russian_expression == target_word else 'wrong'))],
                [InlineKeyboardButton(answers[third_answer].russian_expression, callback_data=(
                    'correct' if answers[third_answer].russian_expression == target_word else 'wrong'))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с клавиатурой
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'🇦🇺 {translates[first].english_expression} - это ...',
        reply_markup=reply_markup
    )


# Функция, которая будет вызываться при нажатии на кнопку
def check_answer(update, context):
    query = update.callback_query
    if query.data == 'correct':
        context.bot.send_message(chat_id=update.effective_chat.id, text='Правильно! ✅')
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Неправильно! ❌')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Следующий вопрос: ... ⬇️')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'...')
    testing_words(update, context)


def main():
    # Создаем объект Updater и передаем ему токен нашего бота
    updater = Updater('5585806024:AAFCaaDyMavc1V_kOP6H1NH95p9DQSmApUk', use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Регистрируем обработчик команды /start
    dp.add_handler(CommandHandler("start", testing_words))
    dp.add_handler(CallbackQueryHandler(check_answer))
    # Регистрируем обработчик нажатия на кнопку
    # dp.add_handler(CallbackQueryHandler(testing_words))

    # Запускаем бота
    updater.start_polling()

    # Ждем, пока бот не остановится
    updater.idle()


if __name__ == '__main__':
    main()
