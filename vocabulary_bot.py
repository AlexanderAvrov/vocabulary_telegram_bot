import os
import logging

import requests
from dotenv import load_dotenv
from selenium import webdriver
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from database import session, User, Translate, Learning

load_dotenv()
token = os.getenv('TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

URL_CAT = 'https://api.thecatapi.com/v1/images/search'
URL_DOG = 'https://api.thedogapi.com/v1/images/search'
ALPHABET_EN = (["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"])


def get_new_image_cat():
    """Получение адреса картинки с котиком"""
    try:
        response = requests.get(URL_CAT)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        response = requests.get(URL_DOG)

    response = response.json()
    random_cat = response[0].get('url')
    return random_cat


def get_new_image_dog():
    """Получение адреса картинки с собачкой"""
    try:
        response = requests.get(URL_DOG)
    except Exception as error:
        print(error)
        response = requests.get(URL_CAT)

    response = response.json()
    random_dog = response[0].get('url')
    return random_dog


def translating_word(text, source_lang, target_lang):
    """Перевод текста"""
    url = f'https://libretranslate.com/?source={source_lang}&target={target_lang}&q={text}'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    js = f"""
    const res = await fetch("https://libretranslate.com/translate", {{
    	method: "POST",
    	body: JSON.stringify({{
    		q: "{text}",
    		source: "{source_lang}",
    		target: "{target_lang}",
    		format: "text",
    		api_key: ""
    	}}),
    	headers: {{ "Content-Type": "application/json" }}
    }});

    return await res.json();
    """
    result = driver.execute_script(js)
    return result['translatedText']


def translate_me(update, context):
    """Запуск функции перевода и отправка сообщения с переводом"""
    chat = update.effective_chat
    user = session.query(User).filter(User.id_user == chat.id).first()
    if not user:
        user = User(id_user=chat.id)
        session.add(user)
    text = update.message.text.lower()
    if text[0].lower() in ALPHABET_EN:
        source_lang, target_lang = 'en', 'ru'
        translate = session.query(Translate).filter(Translate.english_expression == text).first()
        if translate:
            translate_text = translate.russian_expression
    else:
        source_lang, target_lang = 'ru', 'en'
        translate = session.query(Translate).filter(Translate.russian_expression == text).first()
        if translate:
            translate_text = translate.english_expression
    if not translate:
        translate_text = translating_word(text, source_lang, target_lang)
        translate = Translate(english_expression=text, russian_expression=translate_text)
        session.add(translate)
    session.add(Learning(user=user.id, word=translate.id, is_learned=False))
    session.commit()
    context.bot.send_message(
        chat_id=chat.id,
        text=f'{text} - {translate_text}',
    )
    print(f'Сделал перевод: {text} - {translate_text}. Для {update.message.from_user.username}')


def say_hi(update, context):    # TODO: сделать определение сообщения "привет" и отправки приветствия
    """Функция приветствия"""
    name = update.message.from_user.username
    chat = update.effective_chat
    print(name)

    context.bot.send_message(
        chat_id=chat.id,
        text=f'Привет, {name}, я Вальдемар_Bot!',
    )


def new_cat(update, context):
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image_cat())


def new_dog(update, context):
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image_dog())


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = ReplyKeyboardMarkup([
                                  ['/foto_cat', '/foto_dog'],
                                  ['Определи мой ip', '/random_digit'],    # TODO: настроить кнопки, убрать лишние
                                 ], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text='Привет, {}. Посмотри, какого котика я тебе нашёл'.format(name),
        reply_markup=button
    )

    context.bot.send_photo(chat.id, get_new_image_cat())


def main():
    updater = Updater(token=token)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('foto_cat', new_cat))
    updater.dispatcher.add_handler(CommandHandler('foto_dog', new_dog))

    updater.dispatcher.add_handler(MessageHandler(Filters.text, translate_me))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
