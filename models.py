from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import check_password_hash
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }


class Consumer(User):
    __tablename__ = 'consumers'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Consumer'
    }


class Company(User):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    profile_photo = db.Column(db.String(120), nullable=True)
    introduction = db.Column(db.Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Company'
    }


class Mediator(User):
    __tablename__ = 'mediators'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    profile_photo = db.Column(db.String(120), nullable=True)
    biography = db.Column(db.Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Mediator'
    }


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Submitted')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumers.id'), nullable=False)
    consumer = db.relationship('Consumer', backref=db.backref('cases', lazy=True))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    company = db.relationship('Company', backref=db.backref('cases', lazy=True))
    comments = db.relationship('Comment', backref='case', lazy=True, cascade='all, delete-orphan')
    supports = db.relationship('Support', backref='case', lazy=True)
    consumer_message = db.Column(db.Text, nullable=True)
    message_color = db.Column(db.String(10), nullable=True)




class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    case = db.relationship('Case', backref=db.backref('evidence', lazy=True))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)

    def is_owner(self, user_id):
        return self.user_id == user_id


class Support(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('supports', lazy=True))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
