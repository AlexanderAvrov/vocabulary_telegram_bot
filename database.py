import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
password = os.getenv('POSTGRES_PASSWORD')
url_object = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password=password,
    host="127.0.0.1",
    database="vocabulary",
)

engine = create_engine(url_object)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    id_user = Column(Integer)


class Translate(Base):
    __tablename__ = 'Translate'

    id = Column(Integer, primary_key=True)
    text = Column(String(256))
    translate = Column(String(512))


class Learning(Base):
    __tablename__ = 'Learning'

    id = Column(Integer, primary_key=True)
    user = Column(ForeignKey("User.id"))
    word = Column(ForeignKey("Translate.id"))
    is_learned = Column(Boolean)


Base.metadata.create_all(engine)
