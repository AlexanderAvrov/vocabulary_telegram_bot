import os
import logging

import requests
import chardet
from dotenv import load_dotenv
from selenium import webdriver
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

load_dotenv()
token = os.getenv('TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

URL_CAT = 'https://api.thecatapi.com/v1/images/search'
URL_DOG = 'https://api.thedogapi.com/v1/images/search'


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


def translate(text, source_lang, target_lang):
    """Перевод текста"""
    url = "https://libretranslate.com/"
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
    text = update.message.text
    lang = chardet.detect(text.encode('cp1251'))
    if lang['language'] == 'Russian':
        source_lang, target_lang = 'ru', 'en'
    else:
        source_lang, target_lang = 'en', 'ru'
    print(lang)
    translate_text = translate(text, source_lang, target_lang)
    chat = update.effective_chat
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
