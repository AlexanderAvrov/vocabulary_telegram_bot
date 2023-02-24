from sqlalchemy import delete

from database import session, Learning, engine, metadata

# for word in learning_words:
#     print('номер юзера: ', word.user, ', номер слова: ', word.word)

# session.query(Learning).delete()
# session.commit()

learning_words = session.query(Learning)
for word in learning_words:
    print('номер юзера: ', word.user, ', номер слова: ', word.word)
