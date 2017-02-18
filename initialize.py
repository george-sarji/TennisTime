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
session.add(user)
session.commit()	

