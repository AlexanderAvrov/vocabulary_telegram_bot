import logging

import requests

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


def new_cat(update, context):
    """Отправка сообщения с картинкой кошки"""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image_cat())


def new_dog(update, context):
    """Отправка сообщения с картинкой собаки"""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image_dog())
