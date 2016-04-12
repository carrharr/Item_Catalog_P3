#!/usr/bin/python

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import url_for
from flask import flash
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_model import Base, Drivers, Trips, User
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2
import json
import requests

# Endpoints, functions and routing for car sharing webapp for Tenerife (Canary Islands, Spain)
# Requires installation of flask, sqlalchemy and oauth2client libraries
# This is a project for Udacity FSND and is under development, DO NOT DEPLOY!
# Using SQLite for quick concept testing, will move onto a RNDB (probably Postgres) in the future
# No form of caching will be implemented for now

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


################### Connect to database and create session ####################

engine = create_engine('sqlite:///draivcan.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
dbs = DBSession()
########################## Database Helper Functions ##########################

# Tinkered ALL

def list_categories():
    """Returns an alphabetized list of all category names."""
    trips = dbs.query(Trips)
    category_list = []
    for trip in trips:
        if trip not in category_list:
            category_list.append(trip.category)
    category_list = sorted(list(set(category_list)))
    return category_list


def list_drivers():
    """Returns an alphabetized list of all the current booths."""
    return dbs.query(Drivers).order_by(asc(Drivers.name))


def last_ten_items():
    """Returns last ten items added to the items database."""
    return dbs.query(Trips).order_by(Trips.id.desc()).limit(10)


def all_items():
    """Returns all items in the items database."""
    return dbs.query(Trips).order_by(asc(Trips.name))


def category_trips(category):
    """Returns all items in given category."""
    return (dbs.query(Trips)
            .filter_by(category=category)
            .order_by(asc(Trips.name)))


############################## Login Functions ################################


@app.route('/login')
def login():
    """Creates a state token, add it to the session, and render login page."""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Based on: https://gist.github.com/adarsh0806/ef392dbb0906160e4263 'Google+ Connect'
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Manages the authentication process for login."""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already '
                                            'connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'
    # Check to see if owner is in owner database
    user_id = getUserId(data['email'])
    if not user_id:
        user_id = addUser(login_session)
    login_session['user_id'] = user_id

    # Create the success screeen
    output = []
    output.append('<h1>Welcome, ')
    output.append(login_session['username'])
    output.append('!</h1><img src="')
    output.append(login_session['picture'])
    output.append(' " style = "width: 300px; height: 300px;')
    output.append('border-radius: 150px;-webkit-border-radius: 150px;')
    output.append('-moz-border-radius: 150px;"> ')
    flash("You are now logged in as %s" % login_session['username'])
    return ''.join(output)

################################### Logout ####################################


@app.route('/logout')
def logout():
    """
        Deletes session and returns the user to the main page if they are
        logged in.
    """
    try:
        access_token = login_session.get('access_token')

        if access_token is None:
            response = make_response(json.dumps('Current user not connected.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            flash('You are not logged in!')
            return redirect('/')
            return response

        url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
                % access_token )
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        if result['status'] == '200':
            del login_session['access_token']
            del login_session['gplus_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            flash('You have successfully logged out!')
            return redirect('/')
        else:
            response = make_response(json.dumps('Failed to revoke token for '
                                                'given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            return response
    except KeyError:
        flash('You are not logged in!')
        return redirect('/')


########################### User Helper Functions #############################


# Add new owner to database
def addUser(login_session):
    """Adds user to user database and returns their user id."""
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    dbs.add(newUser)
    dbs.commit()
    user = dbs.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Get owner info
def getUserInfo(user_id):
    """Returns user info for user with user_id."""
    user = dbs.query(User).filter_by(id=user_id).one()
    return user


# Get owner id
def getUserId(email):
    """Returns user id for user based on email address if user exists."""
    try:
        user = dbs.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# - - - - - - - - - - - - - - - - - Routing - - - - - - - - - - - - - - - - - -

# Homepage.
@app.route('/')
def index():
    """Return index from login state."""
    drivers = list_drivers()
    trips = last_ten_items()
    categories = list_categories()

    if 'username' not in login_session:
        return render_template('public_index.html', drivers=drivers,
                               trips=trips, categories=categories)
    else:
        return render_template('index.html', drivers=drivers,
                               trips=trips, categories=categories)


# List of all trips
@app.route('/trips/')
def allTrips():
    """Returns the template for all trips."""
    trips = all_items()
    return render_template('trips.html', items=trips)


# List of all trips in category
@app.route('/trips/<category>')
def categoryTrips(category=None):
    """Returns template for given category."""
    trips = category_trips(category)
    return render_template('category_trips.html',
                           trips=trips, category=category)


# Contact page
@app.route('/about/')
def about():
    """Returns the about page template."""
    return render_template('about.html')


# - - - - - - - - - - - - - Driver Functions Routing - - - -- - - - - - - - - -


# Add a driver
@app.route('/drivers/add/', methods=['GET', 'POST'])
def addDriver():
    """Returns template to add driver. Adds driver if the form is submitted and
        user has permission."""
    if 'username' not in login_session:
        return redirect('/login')
        flash('You are not logged in, please login to perform this operation')
    if request.method == 'POST':
        newDriver = Drivers(name=request.form['name'],
                          email=request.form['email'],
                          phone=request.form['phone'],
                          image=request.form['image'],
                          user_id=login_session['user_id'])
        dbs.add(newDriver)
        dbs.commit()
        flash('New driver for %s successfully added!' % newDriver.name)
        return redirect(url_for('index'))
    else:
        return render_template('addDriver.html')


# Edit driver
@app.route('/drivers/<int:driver_id>/edit/', methods=['GET', 'POST'])
def editDriver(driver_id=None):
    """Returns template to edit driver. Driver is updated if form submitted
        and validated."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if driver.user_id != login_session['user_id']:
        result = []
        result.append('<script>')
        result.append('function invalidUser(){')
        result.append('alert("You are not authorized to edit this driver.");}')
        result.append('</script><body onload="invalidUser()">')
        return ''.join(result)

    if request.method == 'POST':
        if request.form['name']:
            driver.name = request.form['name']
        if request.form['email']:
            driver.email = request.form['email']
        if request.form['phone']:
            driver.phone = request.form['phone']
        if request.form['image']:
            driver.image = request.form['image']
        dbs.add(driver)
        dbs.commit()
        flash('Driver information for %s successfully edited' % driver.name)
        return redirect(url_for('index'))
    else:
        return render_template('editDriver.html', driver=driver)


# Delete driver
@app.route('/drivers/<int:driver_id>/delete/', methods=['GET', 'POST'])
def deleteDriver(driver_id=None):
    """Returns template to delete driver."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if driver.user_id != login_session['user_id']:
        result = []
        result.append('<script>')
        result.append('function invalidUser(){')
        result.append('alert("You are not authorized to delete this driver.");}')
        result.append('</script><body onload="invalidUser()">')
        return ''.join(result)

    if request.method == 'POST':
        dbs.delete(driver)
        dbs.commit()
        flash('%s successfully deleted!' % driver.name)
        return redirect(url_for('index'))
    else:
        return render_template('deleteDriver.html', driver=driver)


# Show Driver Trips and info
@app.route('/drivers/<int:driver_id>/')
def driver(driver_id=None):
    """Returns template for given driver id."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()
    trips = dbs.query(Trips).filter_by(driver_id=driver.id)
    owner = getUserInfo(driver.user_id)
    if 'username' not in login_session or owner.id != login_session['user_id']:
        return render_template('public_driver.html', driver=driver, trips=trips)
    else:
        return render_template('driver.html', driver=driver, trips=trips)


# - - - - - - - - - - - - - Trip Functions Routing - - - -- - - - - - - - - - -

# View a single trip
@app.route('/drivers/<int:driver_id>/<int:trip_id>/')
def trip(driver_id=None, trip_id=None):
    """Return the trip template for a given trip id."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()
    trip = dbs.query(Trips).filter_by(id=trip_id).one()
    return render_template('trip.html', driver=driver, trip=trip)


# Add trip
@app.route('/drivers/<int:driver_id>/new/', methods=['GET', 'POST'])
def addTrip(driver_id=None):
    """Return template to add trip. Add on form submission"""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if driver.user_id != login_session['user_id']:
        result = []
        result.append('<script>')
        result.append('function invalidUser(){')
        result.append('alert("You are not authorized to add trips for this')
        result.append(' driver.");}')
        result.append('</script><body onload="invalidUser()">')
        return ''.join(result)

    if request.method == 'POST':
        trip = Trips(name=request.form['name'],
                     description=request.form['description'],
                     origin=request.form['origin'],
                     destination=request.form['destination'],
                     departs=request.form['departs'],
                     price=request.form['price'],
                     category=request.form['category'],
                     driver_id=driver.id,
                     user_id=driver.user_id)
        dbs.add(trip)
        dbs.commit()
        flash('Trip successfully added to %s!' % driver.name)
        return redirect(url_for('driver', driver_id=driver.id))
    else:
        return render_template('addTrip.html', driver=driver)


# Edit trip
@app.route('/drivers/<int:driver_id>/<int:trip_id>/edit/',
           methods=['GET', 'POST'])
def editTrip(driver_id=None, trip_id=None):
    """Return template to edit trip. Edit trip on form submission."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()
    trip = dbs.query(Trips).filter_by(id=trip_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if driver.user_id != login_session['user_id']:
        result = []
        result.append('<script>')
        result.append('function invalidUser(){')
        result.append('alert("You are not authorized to edit trips for this')
        result.append(' driver.");}')
        result.append('</script><body onload="invalidUser()">')
        return ''.join(result)

    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['origin']:
            item.origin = request.form['origin']
        if request.form['destination']:
            item.destination = request.form['destination']
        if request.form['departs']:
            item.departs = request.form['departs']
        if request.form['price']:
            item.price = request.form['price']
        if request.form['category']:
            item.category = request.form['category']
        dbs.add(trip)
        dbs.commit()
        flash('%s successfully updated!' % trip.name)
        return redirect(url_for('driver', driver_id=driver.id))
    else:
        return render_template('editTrip.html', trip=trip, driver=driver)


# Delete trip
@app.route('/drivers/<int:driver_id>/<int:trip_id>/delete/',
           methods=['GET', 'POST'])
def deleteTrip(driver_id=None, trip_id=None):
    """Return template to delete trip. Delete trip on form submission."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()
    trip = dbs.query(Trips).filter_by(id=trip_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if driver.user_id != login_session['user_id']:
        result = []
        result.append('<script>')
        result.append('function invalidUser(){')
        result.append('alert("You are not authorized to delete trips from')
        result.append(' this driver.");}')
        result.append('</script><body onload="invalidUser()">')
        return ''.join(result)

    if request.method == 'POST':
        dbs.delete(trip)
        dbs.commit()
        flash('%s successfully deleted!' % trip.name)
        return redirect(url_for('driver', driver_id=driver.id))
    else:
        return render_template('deleteTrip.html', driver=driver, trip=trip)


################################## JSON API ###################################

# All Trips Info
@app.route('/trips/json')
def allTripsJSON(driver_id=None):
    """Returns JSON for all items in the database."""
    trips = dbs.query(Trips).order_by(asc(Trips.name)).all()
    return jsonify(trips=[t.serialize for t in trips])


# Driver Info
@app.route('/driver/<int:driver_id>/json')
def driverJSON(driver_id=None):
    """Returns JSON for a given booth id."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()
    trips= dbs.query(Trips).filter_by(driver_id=driver_id)
    return jsonify(trips=[t.serialize for t in trips])


# Trip Info
@app.route('/driver/<int:driver_id>/<int:trip_id>/json')
def tripJSON(driver_id=None, trip_id=None):
    """Returns JSON for a given booth and item id."""
    driver = dbs.query(Drivers).filter_by(id=driver_id).one()
    trip = dbs.query(Trips).filter_by(id=trip_id).one()
    return jsonify(trip=trip.serialize)

###############################################################################

if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.run(debug='True', host='0.0.0.0', port=8000)
