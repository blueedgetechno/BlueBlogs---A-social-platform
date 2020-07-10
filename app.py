from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
import hashlib
import os
import random

images = []
propics = []

for root, directories, files in os.walk("static/img/post"):
    for filename in files:
        images.append(filename)

for root, directories, files in os.walk("static/img/profile"):
    for filename in files:
        propics.append(filename)


def giveme():
    random.shuffle(images)
    return random.choice(images)


def giveprof():
    random.shuffle(propics)
    return random.choice(propics)


with open("templates/config.json", "r") as c:
    para = json.load(c)["para"]

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = 'ThisIsAwildGameOfSurvival'
db = SQLAlchemy(app)

from model import*


def hashit(s):
    z = s.encode('ascii')
    return hashlib.sha256(z).hexdigest()


def isalready(s):
    return s in images or s in propics


def toolong(title, content):
    tl = len(title) > 80
    contlis = content.split("\n")
    cl = len(contlis) > 7
    clt = len(content) > 600
    return tl or cl or clt


def longabout(about):
    return len(about) > 100


def invalid(email):
    if email.count("@") != 1 or email.count(".") != 1:
        return True
    if " " in email:
        return True
    if ".com" not in email:
        return True
    em = email.split("@")
    if len(em[0]) == 0:
        return True
    for x in em[0]:
        a = ord(x)
        if 47 < a < 58 or 64 < a < 91 or 96 < a < 123:
            continue
        else:
            return True

    ep = em[1].split(".")
    if len(ep) != 2:
        return True
    if ep[1] != "com":
        return True
    if ep[0] not in ["outlook", "gmail"]:
        return True

    return False


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("error"))


@app.route('/')
def index():
    posts = Posts.query.order_by(Posts.date.desc()).all()
    tp = para['nofpost']
    last = len(posts) // tp + (len(posts) % tp != 0)
    if last == 1:
        return render_template('index.html', posts=posts, prev="#", next="#")

    page = request.args.get('page')
    try:
        page = int(page)
    except(Exception):
        page = 0

    posts = posts[page * tp:min((page + 1) * tp, len(posts))]

    prev = "?page=" + str(page - 1) if page > 0 else "#"
    next = "?page=" + str(page + 1) if page < last - 1 else "#"

    return render_template('index.html', posts=posts, prev=prev, next=next)


@app.route('/profile/<string:name>')
def profile(name):
    edit = 0
    posts = Posts.query.filter_by(
        author=name).order_by(Posts.date.desc()).all()
    if "user" in session:
        if name == session["user"]:
            edit = 1

    user = Users.query.get_or_404(name)
    return render_template("profile.html", user=user, edit=edit, posts=posts)


@app.route('/editprofile', methods=["GET", "POST"])
def editprofile():
    if "user" not in session:
        flash("You are not logged in")
        return redirect("/login")

    user = Users.query.get_or_404(session["user"])
    if request.method == 'POST':
        about = request.form['about']
        github = request.form['github']
        code = request.form['code']
        about = about.strip(' ')
        about = about.strip('\n')
        if longabout(about) or "\n" in about:
            flash("The about is too long")
            return redirect("/editprofile")
        random_check = request.form.get('random')
        user.about = about
        user.github = github
        user.code = code
        if not random_check:
            try:
                image = request.files['profilepic']
                if isalready(image.filename):
                    flash('Sorry! The file name already exist')
                    return redirect('/editprofile')

                else:
                    image.save(os.path.join('static/img/profile/',
                                            secure_filename(image.filename)))

                user.prof = image.filename
            except Exception as e:
                print(e)

        else:
            user.prof = giveprof()

        try:
            db.session.commit()
            return redirect('/profile/' + user.name)
        except(Exception):
            return redirect('/error')
    else:
        return render_template("editprofile.html", user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "user" in session:
        flash("You are already logged in")
        return redirect("/")

    if request.method == 'POST':
        try:
            user = Users.query.get_or_404(request.form['username'])
        except Exception as e:
            print(e)
            flash("You are not signed in")
            return redirect("/createaccount")

        password = hashit(request.form['password'])

        if password == user.password:
            session["user"] = user.name
            flash("Logged In successfully")
            return redirect("/")
        else:
            flash("Wrong password")
            return redirect("/login")
    else:
        return render_template('login.html')


@app.route('/changepassword', methods=['GET', 'POST'])
def changepassword():
    if "user" not in session:
        flash("You are not logged in")
        return redirect("/")

    user = Users.query.get_or_404(session["user"])
    if request.method == 'POST':
        prevpass = hashit(request.form['oldpassword'])
        newpassword = hashit(request.form['newpassword'])

        if prevpass == user.password:
            user.password = newpassword
            try:
                db.session.commit()
                flash("Password updated! shh, Don't tell anyone")
                return redirect("/profile/"+user.name)
            except(Exception):
                return redirect("/error")
        else:
            flash("Wrong current password")
            return redirect("/changepassword")
    else:
        return render_template('changepassword.html')


@app.route('/deleteaccount', methods=['GET', 'POST'])
def deleteaccount():
    if "user" not in session:
        flash("You are not logged in")
        return redirect("/login")

    if request.method == 'POST':
        user = Users.query.get_or_404(session["user"])
        password = hashit(request.form['password'])

        if password == user.password:
            try:
                posts = Posts.query.filter_by(author=session["user"]).all()
                for post in posts:
                    db.session.delete(post)
                db.session.delete(user)
                db.session.commit()
                session.pop("user", None)
            except(Exception):
                return redirect("/error")
            flash("Account deleted")
            return redirect("/")
        else:
            flash("Wrong password")
            return redirect("/deleteaccount")
    else:
        return render_template('deleteaccount.html')


@app.route('/logout')
def logout():
    if "user" in session:
        session.pop("user", None)
        flash("Logged out successfully")
    else:
        flash("You are not logged in")
    return redirect("/")


@app.route('/createaccount',  methods=['GET', 'POST'])
def createaccount():
    if "user" in session:
        flash("You are already logged in")
        return redirect("/")

    if request.method == 'POST':
        try:
            username = request.form['username']
            user = Users.query.get_or_404(username)
            flash("Username already exist")
            return render_template('createaccount.html')
        except (Exception):
            email = request.form['email']
            user = Users.query.filter_by(email=email).all()
            if len(user):
                flash("Email address already exist")
                return render_template('createaccount.html')
            if invalid(email):
                flash("Email address doesn't exist")
                return render_template('createaccount.html')

            password = hashit(request.form['password'])
            newuser = Users(name=username, email=email, password=password)
            try:
                db.session.add(newuser)
                db.session.commit()
            except(Exception):
                return redirect("/error")
            session["user"] = username
            flash("You are now signed in")
            return redirect("/")

        if password == user.password:
            session["user"] = user.name
            flash("Logged In successfully")
            return redirect("/")
        else:
            flash("Wrong password")
            return redirect("/login")
    else:
        return render_template('createaccount.html')


@app.route('/editor')
def editor():
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    games = Games.query.all()
    return render_template('editor.html', games=games)


@app.route('/deletegame/<string:id>', methods=['GET', 'POST'])
def deletegame(id):
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    game = Games.query.get_or_404(id)
    if request.method == 'POST':
        try:
            try:
                os.remove(os.path.join(
                    'static/img/games/', game.nick + '.png'))
                os.remove(os.path.join(
                    'static/js/games/', game.nick + '.js'))
            except(Exception):
                return redirect('/error')

            db.session.delete(game)
            db.session.commit()
            return redirect('/editor')

        except(Exception):
            return redirect('/error')
    else:
        return render_template('deletegame.html', game=game)


@app.route('/editor/<string:id>', methods=['GET', 'POST'])
def editgame(id):
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    game = Games.query.get_or_404(id)

    if request.method == 'POST':
        try:
            os.remove(os.path.join(
                'static/img/games/', game.nick + '.png'))
            os.remove(os.path.join('static/js/games/', game.nick + '.js'))
        except(Exception):
            return redirect('/error')

        game.name = request.form['name']
        game.nick = request.form['nick']
        game.dis = request.form['discrip']

        image = request.files['imagefile']
        jsfile = request.files['jsfile']

        image.save(os.path.join('static/img/games/',
                                secure_filename(image.filename)))
        jsfile.save(os.path.join('static/js/games/',
                                 secure_filename(jsfile.filename)))

        try:
            db.session.commit()
            return redirect('/play')
        except(Exception):
            return redirect('/error')
    else:
        return render_template('editgame.html', game=game)


@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def editblog(id):
    if "user" not in session:
        flash("You are not logged in !")
        return redirect('/login')

    post = Posts.query.get_or_404(id)
    if post.author != session["user"]:
        flash("You can't edit someone else post")
        return redirect("/")

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        content = content.strip(' ')
        content = content.strip('\n')
        title = title.strip(' ')
        if toolong(title, content):
            flash("The title or post is too long")
            return redirect("/edit/" + str(id))

        post.title = title
        post.content = content
        try:
            db.session.commit()
            return redirect('/')
        except(Exception):
            return redirect('/error')
    return render_template('editblog.html', post=post)


@app.route('/delete/<string:id>', methods=['GET', 'POST'])
def delete(id):
    if "user" not in session:
        flash("You are not logged in !")
        return redirect('/login')

    post = Posts.query.get_or_404(id)
    if post.author != session["user"]:
        flash("You can't delete someone else post")
        return redirect("/")

    if request.method == 'POST':
        try:
            db.session.delete(post)
            db.session.commit()
            return redirect('/')
        except(Exception):
            return redirect('/error')

    return render_template('delete.html', post=post)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/add', methods=['GET', 'POST'])
def addvideo():
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    if request.method == 'POST':
        title = request.form['title']
        link = request.form['link']
        newvideo = Videos(
            title=title, link="https://www.youtube.com/embed/" + link)
        try:
            db.session.add(newvideo)
            db.session.commit()
            return redirect('/video')
        except(Exception):
            return redirect('/error')
    else:
        return render_template('addvideo.html')


@app.route('/video')
def video():
    videos = Videos.query.order_by(Videos.id.desc()).all()
    return render_template('video.html', videos=videos)


@app.route('/editvideo')
def editvideo():
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    videos = Videos.query.order_by(Videos.id.desc()).all()
    return render_template('editvideo.html', videos=videos)


@app.route('/deletevideo/<string:id>', methods=['GET', 'POST'])
def deletevideo(id):
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    video = Videos.query.get_or_404(id)

    if request.method == 'POST':
        try:
            db.session.delete(video)
            db.session.commit()
            return redirect('/editvideo')
        except(Exception):
            return redirect('/error')
    else:
        return render_template('deletevideo.html', video=video)


@app.route('/play')
def menu():
    games = Games.query.all()
    return render_template('play.html', games=games)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")

    if request.method == 'POST':
        name = request.form['name']
        nick = request.form['nick']
        dis = request.form['discrip']
        try:
            image = request.files['imagefile']
            jsfile = request.files['jsfile']
            image.save(os.path.join('static/img/games/',
                                    secure_filename(image.filename)))
            jsfile.save(os.path.join('static/js/games/',
                                     secure_filename(jsfile.filename)))
            newgame = Games(name=name, nick=nick, dis=dis)
            db.session.add(newgame)
            db.session.commit()
            return redirect('/play')
        except(Exception):
            return redirect('/error')
    else:
        return render_template('upload.html')


@app.route('/error')
def error():
    return render_template('404.html')


@app.route('/post', methods=['GET', 'POST'])
def post():
    if "user" not in session:
        flash("You are not logged in !")
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        content = content.strip(' ')
        content = content.strip('\n')
        title = title.strip(' ')
        if toolong(title, content):
            flash("The title or post is too long")
            return redirect("/post")
        random_check = request.form.get('random')
        if not random_check:
            try:
                image = request.files['postimage']
                if isalready(image.filename):
                    flash('Sorry! The file name already exist')
                    return redirect('/post')

                else:
                    image.save(os.path.join('static/img/post/',
                                            secure_filename(image.filename)))

            except(Exception):
                return redirect('/error')

            newpost = Posts(title=title, content=content,
                            image=image.filename, author=session["user"])
        else:
            newpost = Posts(title=title, content=content,
                            image=giveme(), author=session["user"])

        try:
            db.session.add(newpost)
            db.session.commit()
            return redirect('/')
        except(Exception):
            return redirect('/error')

    else:
        return render_template('/postblog.html')


@app.route('/admin/')
def admin():
    if "user" not in session or session["user"] != "blue":
        flash("You are not authorized visit this page")
        return redirect("/")
    else:
        return render_template('admin.html')


@app.route('/play/<int:id>')
def play(id):
    game = Games.query.get_or_404(id)
    return render_template('games/playgame.html', game=game)


@app.route('/play/full/<int:id>')
def playfull(id):
    game = Games.query.get_or_404(id)

    return render_template('games/fullsc.html', game=game)


@app.route("/js/<string:file>")
def index_js(file):
    with open("static/js/" + file, "r") as f:
        data = f.read()

    return data


if __name__ == '__main__':
    app.run(debug=True)
