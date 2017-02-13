from flask import Flask, url_for, flash, render_template, redirect, request, g, send_from_directory
from flask import session as login_session
# from model import *
from werkzeug.utils import secure_filename
import locale, os
app = Flask(__name__)
app.secret_key="this is my project"
# SQLAlchemy stuff
### Add your tables here!
# For example:
# from database_setup import Base, Potato, Monkey
from database_setup import *	

from datetime import datetime

from sqlalchemy import create_engine, desc, asc

from sqlalchemy.orm import sessionmaker
# from model import *
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
engine = create_engine('sqlite:///Project.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
dbsession = DBSession()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#YOUR WEB APP CODE GOES HERE
@app.route('/')
def main():
	return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method=="GET":
		return render_template('login.html')
	else:
		email=request.form['email']
		password=request.form['password']
		user=dbsession.query(User).filter_by(email=email).first()
		if (verify_login(email, password)):
			login_session['name']=user.name
			login_session['email']=user.email
			login_session['id']=user.id
			g.id=user.id
			flash("Login successful! Welcome back, "+user.name)
			return redirect(url_for('main'))
		else:
			flash("Incorrect login credentials")
			return redirect(url_for('login'))

def verify_login(email, password):
	user=dbsession.query(User).filter_by(email=email).first()
	if (user is None):
		return False
	elif (user.verify_password(password)):
		return True
	return False



@app.route('/signup',methods=['POST','GET'])
def signup():
	if request.method=='GET':
		return render_template("signup.html")
	name=request.form['name']
	email=request.form['email']
	password=request.form['password']
	confpass=request.form['confpass']
	date=request.form['dob']
	gender=request.form['gender']
	country=request.form['country']
	dates=date.split('-')
	file = request.files['file']
	if 'file' not in request.files:
		flash('No file part')
		return redirect(request.url)
	file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
	if file.filename == '':
		flash('No selected file')
	dob=datetime(year=(int)(dates[0]), month=(int)(dates[1]), day=(int)(dates[2]))
	if (dbsession.query(User).filter_by(email=email).first() is not None):
		flash("Email already in use")
		return redirect(request.url)
	if (password==confpass):
		user=User(name = name, email = email, dob = dob, gender = gender, country=country, admin=False)
		user.hash_password(password)
		dbsession.add(user)
		dbsession.commit()
		filename = str(user.id) + "_user" 
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		user.set_photo(filename)
		dbsession.commit()
		return redirect(url_for('login'))
	else:
		flash("Passwords do not match.")
		return redirect(url_for('signup'))

@app.route('/championships')
def championships():
	championships=dbsession.query(Championship).all()
	return render_template('championship.html', championships=championships)

@app.route('/players')
def players():
	playerslist=dbsession.query(Player).all()
	return render_template('players.html', playerslist=playerslist)

@app.route('/news')
def news():
	newslist=dbsession.query(News).all()
	return render_template('news.html', newslist=newslist)

@app.route('/acp')
def admincp():
	if login_session is None:
		flash("You are not logged in.")
		return redirect('login')
	elif login_session is not None:
		email=login_session['email']
		user=dbsession.query(User).filter_by(email="test").first()
		if (user is not None and user.admin):
			return render_template('acp.html')
		flash ("Access not authorized.")
		return redirect(url_for('main'))

@app.route('/article/<int:id>', methods=['POST', 'GET'])
def article(id):
	if (request.method)=='GET':
		article=dbsession.query(News).filter_by(id=id).first()
		if (article is None):
			flash("Invalid article. Page could not be found.")
			return redirect(url_for('news'))
		else:
			author=dbsession.query(User).filter_by(id=article.user).first()
			return render_template('article.html', article=article, author=author)
	else:
		return redirect(url_for('main'))

@app.route('/profile')
def profile():
	return render_template('index.html')

@app.route('/logout')
def logout():
	del login_session['email']
	del login_session['id']
	del login_session['name']
	flash("Good bye!")
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.run(debug=True)
