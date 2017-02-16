from sqlalchemy import Column,Integer,String, Date, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, func
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
#secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

# class Inventory(Base):
#     __tablename__ = 'inventory'
#     id = Column(Integer, primary_key=True)
#     product_id = Column(Integer, ForeignKey('product.id'))
#     quantity = Column(Integer)
#     last_filled = Column(DateTime, default=func.now())
#     product = relationship("Product", back_populates="inventory")


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    country = Column(String(255))
    email = Column(String(255), unique=True)
    photo = Column(String(255), unique=True)
    password_hash = Column(String(255))
    gender=Column(String)
    dob=Column(Date)
    admin=Column(Boolean)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def set_photo(self, photo):
        self.photo = photo

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class Championship(Base):
    __tablename__='championship'
    id=Column(Integer, primary_key=True)
    name=Column(String(255))
    date=Column(Date)
    place=Column(String)

class Player(Base):
    __tablename__='player'
    id=Column(Integer, primary_key=True)
    name=Column(String(255))
    dob=Column(Date)
    gender=Column(String)
    country=Column(String)
    club=Column(String)
    awards=Column(Integer)
    narrative=Column(String)

class PlayerAssoc(Base):
    __tablename__='player_championship'
    id=Column(Integer, primary_key=True)
    player_id=Column(Integer, ForeignKey('player.id'))
    championship_id=Column(Integer, ForeignKey('championship.id'))

class News(Base):
    __tablename__='news'
    id=Column(Integer, primary_key=True)
    user=relationship('User')
    user_id=Column(Integer, ForeignKey('user.id'))
    subject=Column(String)
    content=Column(String)
    comments=relationship('Comment', uselist=True)

class Comment(Base):
    __tablename__='comment'
    id=Column(Integer, primary_key=True)
    article=relationship('News')
    user=relationship('User')
    user_id=Column(Integer, ForeignKey('user.id'))
    news_id=Column(Integer, ForeignKey('news.id'))
    content=Column(String)

class Gallery(Base):
    __tablename__="gallery"
    id=Column(Integer, primary_key=True)
    news_id=Column(Integer, ForeignKey('news.id'))
    nae=Column(String)

engine = create_engine('sqlite:///Project.db')


Base.metadata.create_all(engine)
