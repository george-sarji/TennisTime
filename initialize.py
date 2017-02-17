from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from database_setup import *
from datetime import datetime

engine = create_engine('sqlite:///Project.db')
Base.metadata.create_all(engine)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#You can add some starter data for your database here.
user=User(name="Admin", country="Palestine", email="george17@meet.mit.edu", admin=True, photo="profile.jpg")
user.hash_password("Administrator")
date = datetime(day=11, month=12, year=2013)
champ=Championship(name="Nada's championship", date=date, place="Nazareth")
news=News(user=user, user_id=1, subject="test", content="Test, this is a test.")
session.add(user)
session.add(champ)
session.add(news)
session.commit()	

