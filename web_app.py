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
	players=dbsession.query(Player).order_by(Player.id).limit(3)
	articles=dbsession.query(News).order_by(News.id).limit(3)
	championships=dbsession.query(Championship).order_by(Championship.id).limit(5)
	return render_template('index.html', players=players, articles=articles, championships=championships)


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
	return render_template('players.html', players=playerslist)

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
			lastuser=dbsession.query(User).order_by(User.id).first()
			lastarticle=dbsession.query(News).order_by(News.id).first()
			lastchampionship=dbsession.query(Championship).order_by(Championship.id).first()
			lastplayer=dbsession.query(Player).order_by(Player.id).first()
			return render_template('acp.html', user=lastuser, article=lastarticle, championship=lastchampionship, player=lastplayer)
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
			author=dbsession.query(User).filter_by(id=article.user.id).first()
			users=[]
			comments=dbsession.query(Comment).filter_by(news_id=id).all()
			pictures=dbsession.query(Gallery).filter_by(news_id=id).first()
			for comment in comments:
				users.append(dbsession.query(User).filter_by(id=comment.user_id).first())
			return render_template('article.html', article=article, author=author, comments=comments, users=users, pictures=pictures)
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
	del login_session['admin']
	flash("Good bye!")
	return redirect(url_for('login'))

@app.route('/acp/articles')
def ManageArticles():
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
	articles = dbsession.query(News).all()
	return render_template('ManageArticles.html', articles=articles)

@app.route('/acp/article/<int:id>', methods=['POST', 'GET'])
def ManageArticle(id):
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
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

@app.route('/acp/comment/<int:id>', methods=['POST'])
def DeleteComment(id):
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
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
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
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

@app.route('/acp/article/delete/<int:id>')
def DeleteArticle(id):
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
	article=dbsession.query(News).filter_by(id=id).first()
	if (article is None):
		flash("Invalid article.")
		return redirect(url_for('ManageArticles'))
	else:
		comments=dbsession.query(Comment).filter_by(news_id=article.id).all()
		for comment in comments:
			dbsession.delete(comment)
		dbsession.delete(article)
		dbsession.commit()
		flash("Article successfully deleted.")
		return redirect(url_for('ManageArticles'))


@app.route('/acp/add', methods=['GET', 'POST'])
def AddArticle():
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
	if request.method =='GET':
		return render_template('AddArticle.html')
	else:
		subject=request.form['subject']
		content=request.form['content']
		content=content.replace('\r', '\n')
		file=request.files['file']
		article=News(subject=subject, content=content, user=user, user_id=user.id)
		dbsession.add(article)
		dbsession.commit()
		photo=Gallery(news_id=article.id)
		dbsession.add(photo)
		dbsession.commit()
		filename = str(photo.id)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		photo.name=filename
		dbsession.commit()
		flash("Article added successfully.")
		return redirect(url_for('ManageArticles'))

@app.route('/acp/championships')
def ManageChampionships():
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
		return redirect(url_for('main'))
	championships=dbsession.query(Championship).all()
	return render_template('ManageChampionships.html', championships=championships)

@app.route('/acp/addchamp', methods=['GET', 'POST'])
def AddChampionship():
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
	if request.method=='GET':
		return render_template('AddChampionship.html')
	else:
		name=request.form['name']
		place=request.form['place']
		date=request.form['date']
		date=date.split('-')
		championship=Championship(name=name, place=place, date=datetime(year=(int)(date[0]), month=(int)(date[1]), day=(int)(date[2])))
		dbsession.add(championship)
		dbsession.commit()
		flash("Championship added succesfully.")
		return redirect(url_for('ManageChampionships'))

@app.route('/acp/managechamp/<int:id>', methods=['POST', 'GET'])
def ManageChampionship(id):
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
	championship=dbsession.query(Championship).filter_by(id=id).first()
	if championship is None:
		flash("Championship was not found.")
		return redirect(url_for('ManageChampionships'))
	if request.method=='GET':
		return render_template('ManageChampionship.html', championship=championship)
	else:
		name=request.form['name']
		place=request.form['place']
		date=request.form['date']
		date=date.split('-')
		championship.name=name
		championship.place=place
		championship.date=datetime(year=(int)(date[0]), month=(int)(date[1]), day=(int)(date[2]))
		dbsession.commit()
		flash("Championship edited successfully.")
		return redirect(url_for('ManageChampionships'))

@app.route('/acp/deletechamp/<int:id>')
def DeleteChampionship(id):
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
	championship=dbsession.query(Championship).filter_by(id=id).first()
	if championship is None:
		flash("Championship was not found.")
		return redirect(url_for('ManageChampionships'))
	else:
		dbsession.delete(championship)
		dbsession.commit()
		flash("Championship deleted successfully.")
		return redirect(url_for('ManageChampionships'))


@app.route('/acp/manageplayers')
def ManagePlayers():
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
	players=dbsession.query(Player).all()
	return render_template("ManagePlayers.html", players=players)

@app.route('/acp/manageplayer/<int:id>', methods=['POST', 'GET'])
def ManagePlayer(id):
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
	player=dbsession.query(Player).filter_by(id=id).first()
	if player is None:
		flash("Invalid player.")
		return redirect(url_for('ManagePlayers'))
	if request.method=='GET':
		return render_template("ManagePlayer.html", player=player)
	else:
		name=request.form['name']
		bday=request.form['date'].split('-')
		country=request.form['country']
		club=request.form['club']
		awards=request.form['awards']
		narrative=request.form['narrative'].replace('\r', '<br>')
		player.name=name
		player.birthday=datetime(year=(int)(bday[0]), month=(int)(bday[1]), day=(int)(bday[2]))
		player.country=country
		player.club=club
		player.awards=awards
		player.narrative=narrative
		dbsession.commit()
		flash("Player edited successfully.")
		return redirect(url_for('ManagePlayers'))

@app.route('/acp/addplayer', methods=['POST', 'GET'])
def AddPlayer():
	if login_session is None:
		flash("You must be logged in to do this.")
		return redirect(url_for('login'))
	user=dbsession.query(User).filter_by(id=login_session['id']).first()
	if (not user.admin):
		flash("You are not authorized to do this.")
	if request.method=='GET':
		return render_template('AddPlayer.html')
	else:
		name=request.form['name']
		birthday=request.form['birthday'].split('-')
		country=request.form['country']
		gender=request.form['gender']
		club=request.form['club']
		awards=(int)(request.form['awards'])
		narrative=request.form['narrative'].replace('\r', '\n')
		file=request.files['file']
		player=Player(name=name, dob=datetime(year=(int)(birthday[0]), month=(int)(birthday[1]), day=(int)(birthday[2])), country=country, gender=gender,
			club=club, narrative=narrative, awards=awards)
		dbsession.add(player)
		dbsession.commit()
		filename = str(player.id) + "_player" 
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		player.set_photo(filename)
		dbsession.commit()
		flash("Player added successfully.")
		return redirect(url_for('ManagePlayers'))

@app.route('/about')
def AboutMe():
	return render_template('about.html')

@app.route('/gallery')
def gallery():
	gallery=dbsession.query(Gallery).all()
	return render_template('gallery.html', gallery=gallery)

@app.route('/contact')
def contact():
	return render_template('contact.html')

if __name__ == '__main__':
	app.run(debug=True)
