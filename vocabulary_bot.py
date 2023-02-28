import os
import logging
import random

import requests
from dotenv import load_dotenv
from sqlalchemy import and_
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler

from animals import get_new_image_cat, new_cat, new_dog
from database import session, User, Translate, Learning

load_dotenv()
token = os.getenv('TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

ALPHABET_EN = (["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"])
ALPHABET_RU = (['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н',
                'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'э', 'ю', 'я'])


def translating_word(text, sl, tl):
    """Перевод текста"""
    url = f'https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl={sl}&tl={tl}&q={text}'
    response = requests.get(url)
    result = response.json()
    return result[0][0][0]


def translate_me(update, context):
    """Запуск функции перевода и отправка сообщения с переводом"""
    chat = update.effective_chat
    user = session.query(User).filter(User.id_user == chat.id).first()
    if not user:
        user = User(id_user=chat.id)
        session.add(user)
    input_text = update.message.text.lower()
    if input_text[0].lower() in ALPHABET_EN:
        source_lang, target_lang = 'en', 'ru'
        translate = session.query(Translate).filter(Translate.english_expression == input_text).first()
        if translate:
            translate_text = translate.russian_expression
    elif input_text[0].lower() in ALPHABET_RU:
        source_lang, target_lang = 'ru', 'en'
        translate = session.query(Translate).filter(Translate.russian_expression == input_text).first()
        if translate:
            translate_text = translate.english_expression
    else:
        context.bot.send_message(
            chat_id=chat.id,
            text=f'Такого языка я не знаю! Но зато у меня есть картинка с котиком',
        )
        context.bot.send_photo(chat.id, get_new_image_cat())
        return
    if not translate:
        translate_text = translating_word(input_text, source_lang, target_lang)
        if source_lang == 'en':
            translate = Translate(english_expression=input_text, russian_expression=translate_text)
            session.add(translate)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)
            translate = session.query(Translate).filter(Translate.english_expression == input_text).first()
        else:
            translate = Translate(english_expression=translate_text, russian_expression=input_text)
            session.add(translate)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)
            translate = session.query(Translate).filter(Translate.russian_expression == input_text).first()
    try:
        is_learning = session.query(Learning).filter(
            and_(Learning.user == user.id, Learning.word == translate.id)).first()
    except Exception as e:
        session.rollback()
        print(e)
        return
    if not is_learning:
        session.add(Learning(user=user.id, word=translate.id, is_learned=False))
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(e)

    context.bot.send_message(
        chat_id=chat.id,
        text=f'{input_text} - {translate_text}',
    )
    print(f'Сделал перевод: {input_text} - {translate_text}. Для {update.message.from_user.username}')


def get_random_exclude(exclude, max_digit):
    """Нахождение рандомного числа с исключениями"""
    rand_integer = random.randint(0, max_digit)
    return get_random_exclude(exclude, max_digit) if rand_integer in exclude else rand_integer


def testing_words(update, context):
    """Проверка слов в режиме викторины"""
    user = session.query(User).filter(User.id_user == update.effective_chat.id).first()
    translates = user.translates
    count_words = len(translates)
    if count_words < 3:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=('У вас мало слов для повторения. Добавьте хотя бы три штуки. '
                  'Что бы добавить слово, просто напишите мне его на английском или русском.')
        )
        return
    first = get_random_exclude([None], (count_words - 1))
    second = get_random_exclude([first], (count_words - 1))
    third = get_random_exclude([first, second], (count_words - 1))
    target_word = translates[first].russian_expression
    first_answer = get_random_exclude([None], 2)
    second_answer = get_random_exclude([first_answer], 2)
    third_answer = get_random_exclude([first_answer, second_answer], 2)
    answers = [translates[first], translates[second], translates[third]]
    keyboard = [[InlineKeyboardButton(f'1️⃣ {answers[first_answer].russian_expression}', callback_data=(
        'correct' if answers[first_answer].russian_expression == target_word else 'wrong'))],
                [InlineKeyboardButton(f'2️⃣ {answers[second_answer].russian_expression}', callback_data=(
                    'correct' if answers[second_answer].russian_expression == target_word else 'wrong'))],
                [InlineKeyboardButton(f'3️⃣ {answers[third_answer].russian_expression}', callback_data=(
                    'correct' if answers[third_answer].russian_expression == target_word else 'wrong'))],
                [InlineKeyboardButton('Удалить слово ❌', callback_data=f'delete-{translates[first].id}-test')],
                [InlineKeyboardButton('Закончить повторение слов ⛔', callback_data='stop')]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с клавиатурой
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'🇦🇺 {translates[first].english_expression} - это ...',
        reply_markup=reply_markup
    )


def repeat_words(update, context, count=0):
    """Повторение слов"""
    user = session.query(User).filter(User.id_user == update.effective_chat.id).first()
    translates = user.translates
    if count >= len(translates):
        count = 0
    if len(translates) < 1:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='У вас нет слов для повторения 🙁 Добавьте хотя бы одно! Просто напишите мне незнакомое слово.')
        return
    translate = translates[count]
    keyboard = [[InlineKeyboardButton('Следующее слово ➡️', callback_data=f'next-{count}')],
                [InlineKeyboardButton('Удалить слово ❌', callback_data=f'delete-{translate.id}-repeat-{count}')],
                [InlineKeyboardButton('Закончить повторение слов ⛔', callback_data='stop')]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'🇦🇺 {translate.english_expression} - {translate.russian_expression} 🇷🇺',
            reply_markup=reply_markup
        )


def check_answer(update, context):
    """Проверка ответа (callback_query)"""
    query = update.callback_query
    if query.data == 'correct':
        context.bot.send_message(chat_id=update.effective_chat.id, text='Правильно! ✅')
    elif query.data == 'wrong':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'⛔ Неправильно! ‼️')
    elif 'next' in query.data:
        data = query.data.split('-')
        count = int(data[1])
        count += 1
        return repeat_words(update, context, count)
    elif 'delete' in query.data:
        data = query.data.split('-')
        count = int(data[1])
        count += 1
        translate_id = data[1]
        user = session.query(User).filter(User.id_user == update.effective_chat.id).first()
        session.query(Learning).filter(and_(Learning.user == user.id, Learning.word == translate_id)).delete()
        session.commit()
        if data[2] == 'repeat':
            return repeat_words(update, context, count)
        else:
            return testing_words(update, context)
    elif query.data == 'stop':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f' Повторение слов окончено 🤗'
        )
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Следующий вопрос: ... ⬇️')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'...')
    testing_words(update, context)




def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([
                                  ['/repeat'],
                                  ['/test'],
                                 ], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text=f'Привет, {update.message.from_user.first_name}. Посмотри, какого котика я тебе нашёл',
        reply_markup=button
    )

    context.bot.send_photo(chat.id, get_new_image_cat())
    context.bot.send_message(
        chat_id=chat.id,
        text=('Если нужно перевести слово с английского, просто напиши мне его в чат.'
              ' Так же можно перевести в обратную сторону.'),
        reply_markup=button
    )


def main():
    updater = Updater(token=token)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('foto_cat', new_cat))
    updater.dispatcher.add_handler(CommandHandler('foto_dog', new_dog))
    updater.dispatcher.add_handler(CommandHandler('test', testing_words))
    updater.dispatcher.add_handler(CommandHandler('repeat', repeat_words))
    updater.dispatcher.add_handler(CallbackQueryHandler(check_answer))

    updater.dispatcher.add_handler(MessageHandler(Filters.text, translate_me))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
