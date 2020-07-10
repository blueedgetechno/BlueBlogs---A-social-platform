from manage import db
from datetime import datetime


class Users(db.Model):
    name = db.Column(db.String(50), unique=True,
                     nullable=False, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    about = db.Column(db.String(100), nullable=False,
                      default="If you’re going to tell people the truth, be funny or they’ll kill you.")
    prof = db.Column(db.String(20), nullable=False, default="profile.jpg")
    github = db.Column(db.String(100), nullable=False, default="")
    code = db.Column(db.String(100), nullable=False, default="")

    def __repr__(self):
        return '<user %r>' % self.id


class Posts(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(600), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    author = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(30))

    def __repr__(self):
        return '<post %r>' % self.id


class Games(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    nick = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    dis = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<game %r>' % self.id


class Videos(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    link = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<vid %r>' % self.id
