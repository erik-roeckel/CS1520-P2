import os
from datetime import datetime
from flask import Flask, request, abort, url_for, redirect, session, render_template, flash, g, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash

from models import db, User, Event
app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'catering.db')
app.config.from_object(__name__)
app.config.from_envvar('CATERING_SETTINGS', silent = True)
app.secret_key = "development key"
DEBUG = True
owner = {'username': 'owner', 'password': 'pass'}

# by default, direct to login
db.init_app(app)

@app.cli.command('initdb')
def initdb_command():
	db.create_all()

def get_user_id(username):
	user = User.query.filter_by(username = username).first()
	if(user):
		return user.id
	else:
		return None

def get_event_id(date):
	event = Event.query.filter_by(date = date).first()
	if(event):
		return event.event_id
	else:
		return None

@app.before_request
def before_request():
	g.user = None
	if 'id' in session:
		g.user = User.query.filter_by(id = session['id']).first()

@app.route("/")
def default():
	return redirect(url_for("login_controller"))
	
@app.route("/login/", methods=["GET", "POST"])
def login_controller():
	# first check if the user is already logged in
	if g.user:
		if g.user.occupation == 'customer':
			return redirect(url_for("customer_profile", username = g.user.username))
		elif g.user.occupation == 'staff':
			return redirect(url_for("staff_profile", username = g.user.username))
	elif 'owner' in session:
			return redirect(url_for("owner_profile"))
	elif request.method == "POST":
		if owner['username'] == request.form['username'] and owner['password'] == request.form['password']:
			session['owner'] = True
			return redirect(url_for("owner_profile"))
		elif owner['username'] == request.form["username"] and owner['password'] is not request.form['password']:
				flash("You must enter a valid password")
		else:
			user = User.query.filter_by(username = request.form['username']).first()
			if user is None:
				flash('Invalid Username, try again')
				return redirect(url_for("login_controller"))
			elif not check_password_hash(user.hashedPass, request.form['password']):
				flash('Invalid Password, try again!')
			elif user:
				session['id'] = user.id
				if user.occupation == "customer": 
					return redirect(url_for("customer_profile", username = user.username))
				else: 
					return redirect(url_for("staff_profile", username = user.username))
	# if not, and the incoming request is via POST try to log them in
	# if all else fails, offer to log them in
	return render_template("login.html")

@app.route("/owner")
def owner_profile():
	all_events = Event.query.order_by(Event.date).all()
	return render_template("ownerProfile.html", events = all_events)
	
@app.route("/add-staff" , methods = ["GET", "POST"])
def add_staff():
	if request.method == "POST":
		if not request.form['user']:
			flash("You must enter a username to register a new staff member", 'error')
		elif get_user_id(request.form['user']) is not None:
			flash("You have already registed a staff member with this username, try another", 'error')
		elif not request.form['password']:
			flash("You must enter a password to register a new staff member", 'error')
		else:
			db.session.add(User("staff", request.form['user'], generate_password_hash(request.form['password'])))
			db.session.commit()
			flash("You have registered a new staff member!")
			return redirect(url_for("owner_profile"))
	return render_template("registerStaff.html")

@app.route("/staff/<username>")
def staff_profile(username):
	all_events= Event.query.order_by(Event.date).all()
	return render_template("staffProfile.html", username = g.user.username, events= all_events)

@app.route("/staff/<username>/<event>/<eventID>", methods = ["GET", "POST"])
def event_signup(username, event, eventID):
	if request.method == 'GET':
		return render_template("eventSignup.html", event = event)
	else:
		signup_event = Event.query.get(eventID)
		if not signup_event.staffOne:
			signup_event.staffOne = username
		elif not signup_event.staffTwo:
			signup_event.staffTwo = username
		else:
			signup_event.staffThree = username
		db.session.commit()
	return redirect(url_for('staff_profile', username = username))

@app.route("/profile/<username>", methods = ["GET", "POST"])
def customer_profile(username):
	customer_events = Event.query.filter_by(user_id = session['id']).all()
	if request.method == 'POST':
		if not request.form['description']:
			flash("You must enter an event description to register a new event")
		elif not request.form['date']:
			flash("You must enter an event date to register a new event")
		elif get_event_id(request.form['date']) is not None:
			flash("We have already scheduled an event for this date, please choose a different date")
		else:
			db.session.add(Event(get_user_id(username), request.form['description'], request.form['date']))
			db.session.commit()
			flash("You have registed a new event with Erik's Catering Co.")
			customer_events = Event.query.filter_by(user_id = session['id']).all()
			return render_template("customerProfile.html", username = g.user.username, events = customer_events)
	return render_template("customerProfile.html", username = g.user.username, events = customer_events)

@app.route("/remove_event/<event>/<eventId>", methods = ["GET", "POST"])
def delete_event(event, eventId):
	if request.method == 'GET':
		return render_template("deleteEvent.html", event = event)
	else:
		deleteEvent = Event.query.filter_by(event_id = eventId).first()
		db.session.delete(deleteEvent)
		db.session.commit()
		flash("You have successfully deleted this event from the catering schedule")
		return redirect(url_for('customer_profile', username = g.user.username))

@app.route("/register" , methods = ["GET", "POST"])
def register_controller():
	if request.method == "GET":
		return render_template("registerCustomer.html")
	elif request.method == "POST":
		if not request.form['user']:
			flash("You must enter a username to register", 'error')
		elif not request.form['password']:
			flash("You must enter a password to register", 'error')
		elif get_user_id(request.form['user']) is not None:
			flash("This username is already taken, try another", 'error')
		else:
			db.session.add(User("customer", request.form['user'], generate_password_hash(request.form['password'])))
			db.session.commit()
			flash("You have registered for an account, please sign in")
			return redirect(url_for("login_controller"))
	return render_template("registerCustomer.html")

@app.route("/logout")
def logout_controller():
	session.pop('id', None)
	if 'owner' in session:
		session.pop('owner', None)
	flash("You have been successfully logged out")
	return redirect(url_for("login_controller"))
		
			
if __name__ == "__main__":
	app.run()