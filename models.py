from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    occupation = db.Column(db.String(10), nullable = False)
    username = db.Column(db.String(24), nullable = False)
    hashedPass = db.Column(db.String(64), nullable = False)
    events = db.relationship('Event', backref='users' , lazy =True)

    def __init__(self, occupation, username, hashedPass):
        self.occupation = occupation
        self.username = username
        self.hashedPass = hashedPass
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable= False)
    description = db.Column(db.Text, nullable = False)
    date = db.Column(db.String(8), unique = True, nullable = False)
    staffOne = db.Column(db.String(24), nullable = True)
    staffTwo = db.Column(db.String(24), nullable = True)
    staffThree = db.Column(db.String(24), nullable = True)

    def __init__(self, user_id, description, date):
        self.user_id = user_id
        self.description = description
        self.date = date
    def __repr__(self):
        return 'Event Description: {}, Scheduled For: {}'.format(self.description, self.date)





    
    