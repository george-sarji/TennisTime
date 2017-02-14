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

UPLOAD_FOLDER = 'static'
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
			login_session['admin']=user.admin
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
		id=login_session['id']
		user=dbsession.query(User).filter_by(id=id).first()
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
			users=[]
			comments=dbsession.query(Comment).filter_by(news_id=id).all()
			for comment in comments:
				users.append(dbsession.query(User).filter_by(id=comment.user_id).first())
			return render_template('article.html', article=article, author=author, comments=comments, users=users)
	else:
		comment=request.form['comment']
		newcomment=Comment(user_id=login_session['id'], news_id=id, content=comment)
		dbsession.add(newcomment)
		dbsession.commit()
		return redirect(url_for('article', id=id))

@app.route('/profile')
def profile():
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	return render_template('Profile.html', user=user)

@app.route('/logout')
def logout():
	del login_session['email']
	del login_session['id']
	del login_session['name']
	flash("Good bye!")
	return redirect(url_for('login'))

@app.route('/acp/articles')
def ManageArticles():
	articles = dbsession.query(News).all()
	return render_template('ManageArticles.html', articles=articles)

@app.route('/acp/article/<int:id>', methods=['POST', 'GET'])
def ManageArticle(id):
	article=dbsession.query(News).filter_by(id=id).first()
	if request.method=='GET':
		if (article is None):
			flash("Invalid article.")
			return redirect(url_for('ManageArticles'))
		else:
			comments=dbsession.query(Comment).filter_by(news_id=article.id).all()
			return render_template('ManageArticle.html', article=article, comments=comments)
	else:
		subject=request.form['subject']
		content=request.form['content']
		if (subject!=article.subject):
			article.subject=subject
		if (content != article.content):
			article.content=content
		dbsession.commit()
		return redirect(url_for('ManageArticle', id=id))

@app.route('/acp/comment/<int:id>')
def DeleteComment(id):
	comment=dbsession.query(Comment).filter_by(id=id).first()
	dbsession.delete(comment)
	dbsession.commit()
	flash("Comment has been deleted successfully.")
	return redirect(url_for('ManageArticles'))

@app.route('/acp/members')
def ManageUsers():
	users=dbsession.query(User).all()
	return render_template('ManageUsers.html', users=users)

@app.route('/acp/member/<int:id>', methods=['POST', 'GET'])
def ManageUser(id):
	user=dbsession.query(User).filter_by(id=id).first()
	if (request.method=='GET'):
		if user is None:
			flash("Invalid user.")
			return redirect(url_for('ManageUsers'))
		else:
			return render_template('ManageUser.html', user=user)
	else:
		if (user.admin):
			flash("You cant delete the admin account.")
			return redirect(url_for("ManageUser", id = user.id))
		comments=dbsession.query(Comment).filter_by(user=user).all()
		for comment in comments:
			dbsession.delete(comment)
		#dbsession.delete(comments)
		dbsession.delete(user)
		dbsession.commit()
		flash("User deleted successfully.")
		return redirect(url_for('ManageUsers'))

@app.route('/acp/article/delete/<int:id>', methods=['POST'])
def DeleteArticle(id):
	article=dbsession.query(News).filter_by(id=id).first()
	if (article is None):
		flash("Invalid article.")
		return redirect(url_for('ManageArticles'))
	else:
		dbsession.delete(article)
		dbsession.commit()
		flash("Article successfully deleted.")
		return redirect(url_for('ManageArticles'))

if __name__ == '__main__':
	app.run(debug=True)
