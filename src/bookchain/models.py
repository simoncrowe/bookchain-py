import configparser
import os


from sqlalchemy import Column, create_engine, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

MODULE_PARENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(MODULE_PARENT_DIRECTORY, 'settings.ini'))

DATABASE_ENGINE = create_engine(
    'postgresql://{username}:{password}@{database_host}/{database_name}'.format(
        username=config['DATABASE']['user'],
        password=config['DATABASE']['pass'],
        database_host=config['DATABASE']['host'],
        database_name=config['DATABASE']['name'],
    )
)


class Block(Base):

    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True)
    hash = Column(String(64))
    timestamp = Column(String(255))
    text = Column(String())


Base.metadata.create_all(DATABASE_ENGINE)
