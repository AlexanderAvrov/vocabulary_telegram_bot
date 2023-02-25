import json

import requests
from sqlalchemy import delete

from database import session, Learning, engine, metadata, Translate, User

# for word in learning_words:
#     print('номер юзера: ', word.user, ', номер слова: ', word.word)

session.query(Learning).delete()
session.query(Translate).delete()
session.query(User).delete()
# session.query(Translate).filter(Translate.english_expression == 'i').delete()
session.commit()

learning_words = session.query(Translate)
for word in learning_words:
    print('номер юзера: ', word.english_expression, ', номер слова: ', word.russian_expression)

# url = 'https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=en&tl=ru&q=hello world'
#
# response = requests.get(url)
# # resp_text = response.text
# # translate_text = translate_text[0]
# # translate_text = [[['hello']]]
# # response = [[["Привет, мир", "hello world", null, null, 10]], null,"en", null, null, null, null,[]]
# data = response.json()
# print(data[0][0][0])
