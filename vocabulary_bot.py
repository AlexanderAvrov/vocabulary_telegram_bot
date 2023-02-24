import os
import logging

import requests
from dotenv import load_dotenv
from selenium import webdriver
from sqlalchemy import and_
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
ALPHABET_RU = (['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н',
                'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'э', 'ю', 'я'])


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
            session.commit()
            translate = session.query(Translate).filter(Translate.english_expression == input_text).first()
        else:
            translate = Translate(english_expression=translate_text, russian_expression=input_text)
            session.add(translate)
            session.commit()
            translate = session.query(Translate).filter(Translate.russian_expression == input_text).first()
    is_learning = session.query(Learning).filter(and_(Learning.user == user.id, Learning.word == translate.id)).first()
    if not is_learning:
        session.add(Learning(user=user.id, word=translate.id, is_learned=False))
    try:
        session.commit()
    except Exception as e:
        print(e)

    context.bot.send_message(
        chat_id=chat.id,
        text=f'{input_text} - {translate_text}',
    )
    print(f'Сделал перевод: {input_text} - {translate_text}. Для {update.message.from_user.username}')


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
                                  ['/foto_cat', '/foto_dog'],    # TODO: настроить кнопки, убрать лишние
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

    updater.dispatcher.add_handler(MessageHandler(Filters.text, translate_me))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
