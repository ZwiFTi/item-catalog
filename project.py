from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify)

# login_required
from functools import wraps

# LOGIN
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# CRUD OPERATIONS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import (Base,
                            Catalog,
                            CatalogItem,
                            User)

app = Flask(__name__)

# CREATE SESSION AND CONNECTO TO DB
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# ------------------------------------
# LOGIN THINGS
# ------------------------------------
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Web client 1"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
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
        return response

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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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

    # see if user exists, if not create new user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;' \
              'height: 300px;' \
              'border-radius: 150px;' \
              '-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '

    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONECT
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user is not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # print 'In gdisconnect access token is %s' % login_session['access_token']
    # print 'User name is: '
    # print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'  \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # print 'Result is '
    # print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['state']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You have been logged out")
        return redirect(url_for('Index'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# LOGIN REQUIRED
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' in login_session:
            return f(*args, **kwargs)
        else:
            flash('You are not allowed to access there', 'danger')
            return redirect(url_for('showLogin'))

    return decorated_function


# ------------------------------------
# JSON ENDPOINTS
# ------------------------------------
@app.route('/catalog/<catalog_name>/<catalogitem_name>/JSON')
def CatalogItemJSON(catalog_name, catalogitem_name):
    selectedCatalog = session.query(Catalog).filter_by(name=catalog_name).one()
    item = session.query(CatalogItem).filter_by(catalog_id=selectedCatalog.id,
                                                name=catalogitem_name).one()
    return jsonify(Item=item.serialize)


@app.route('/JSON')
def CatalogJSON():
    catalogs = session.query(CatalogItem).all()
    j = jsonify(CatalogItems=[e.serialize for e in catalogs])
    return j


# ------------------------------------
# VIEW / READ
# ------------------------------------
# TASK 1 - Displaying the front page
@app.route('/')
@login_required
def Index():
    ''' URI for displaying the frontpage,
        and the five latest '''
    if 'username' in login_session:
        isLogin = True
    else:
        isLogin = False
    catalogs = session.query(Catalog).all()
    items = session.query(CatalogItem).all()

    # A filter that gives the five latest category items by user
    if isLogin:
        itemsByUser = filter(
            lambda x: x.user.name == login_session['username'], items)
        itemsByUser = list(reversed(itemsByUser))
        itemsByUser = itemsByUser[:5]
    else:
        itemsByUser = []

    return render_template('catalog.html', catalogs=catalogs,
                           items=itemsByUser,
                           islogin=isLogin)


# TASK 2
@app.route('/catalog/<catalog_name>/items/')
def ListItems(catalog_name):
    ''' URI for displaying all items within a selected category '''
    if 'username' in login_session:
        isLogin = True
    else:
        isLogin = False
    catalogs = session.query(Catalog).all()
    selectedCatalog = session.query(Catalog).filter_by(name=catalog_name).one()

    items = session.query(CatalogItem).filter_by(catalog_id=selectedCatalog.id)

    if isLogin:
        itemsByUser = filter(
                    lambda x: x.user.name == login_session['username'], items)
    else:
        itemsByUser = []

    return render_template('selectedCatalog.html', catalogs=catalogs,
                           catalog=selectedCatalog,
                           items=itemsByUser,
                           islogin=isLogin)


# TASK 3 - Display an item
@app.route('/catalog/<catalog_name>/<catalogitem_name>/')
def Details(catalog_name, catalogitem_name):
    ''' URI for displaying the details of a selected item within
        a selected category '''
    if 'username' in login_session:
        isLogin = True
    else:
        isLogin = False
    selectedCatalog = session.query(Catalog).filter_by(name=catalog_name).one()
    item = session.query(CatalogItem).filter_by(catalog_id=selectedCatalog.id,
                                                name=catalogitem_name).one()

    return render_template('item.html', catalog=selectedCatalog,
                           item=item,
                           islogin=isLogin)


# ------------------------------------
# Create, update and delete operations
# ------------------------------------
@app.route('/catalog/<catalog_name>/new', methods=['GET', 'POST'])
@login_required
def newCatalogItem(catalog_name):
    ''' Create a new catalog item '''
    if 'username' in login_session:
        isLogin = True
    else:
        isLogin = False

    if request.method == 'POST':
        selectedCatalog = session.query(Catalog).filter_by(
            name=catalog_name).one()

        allItems = session.query(CatalogItem).all()
        names = []

        for item in allItems:
            names.append(item.name)

        newItem = CatalogItem(
            name=request.form['name'],
            description=request.form['description'],
            catalog=selectedCatalog,
            user_id=login_session['user_id'])

        # Checking if the item exists
        if newItem.name not in names:
            print(newItem)
            session.add(newItem)
            session.commit()
            flash('Item named ' + request.form['name'] + ' created')
            print("item created")

            check = session.query(CatalogItem).filter_by(
                name=request.form['name'])
            print(check)

            return redirect(url_for('ListItems', catalog_name=catalog_name,
                                    islogin=isLogin))
        flash('Item already exists')
        return redirect(url_for('Index'))
    else:
        return render_template('newCatalogItem.html',
                               catalog_name=catalog_name,
                               islogin=isLogin)


@app.route('/catalog/<catalogitem_name>/edit', methods=['GET', 'POST'])
@login_required
def EditCatalogItem(catalogitem_name):
    ''' Edit a catalog item '''
    selectedCatalogItem = session.query(CatalogItem).filter_by(
                                name=catalogitem_name).one()

    # Authorization test
    if selectedCatalogItem.user_id != login_session['user_id']:
        flash('You are not authorized to edit this item')
        return redirect(url_for('Index'))

    # Editing item if authorized
    if request.method == 'POST':
        if request.form['description'] != selectedCatalogItem.description:
            flash('Set items description from ' +
                  selectedCatalogItem.description + ' to ' +
                  request.form['description'] + '.')
            selectedCatalogItem.description = request.form['description']
        selectedCatalogItem.name = request.form['name']
        session.add(selectedCatalogItem)
        session.commit()

        if request.form['name'] != catalogitem_name:
            flash('Set items name from ' +
                  catalogitem_name + ' to ' + request.form['name'] + '.')

        return redirect(url_for('Details',
                                catalog_name=selectedCatalogItem.catalog.name,
                                catalogitem_name=selectedCatalogItem.name,
                                isLogin=True))
    else:
        return render_template('editCatalogItem.html',
                               catalogitem_name=catalogitem_name,
                               islogin=True)


@app.route('/catalog/<catalogitem_name>/delete', methods=['GET', 'POST'])
@login_required
def DeleteCatalogItem(catalogitem_name):
    ''' Delete a catalog item '''
    if 'username' in login_session:
        isLogin = True
    else:
        isLogin = False
        return redirect(url_for('showLogin'))

    itemToDelete = session.query(CatalogItem).filter_by(
        name=catalogitem_name).first()

    # Authorization test
    if itemToDelete.user_id != login_session['user_id']:
        flash('You are not authorized to delete this item')
        return redirect(url_for('Index'))

    # Deleting item if authorized
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('deleted item ' + catalogitem_name + '.')
        return redirect(url_for('Index'))
    else:
        return render_template('deleteCatalogItem.html',
                               catalogitem_name=catalogitem_name,
                               islogin=isLogin)


# Helper functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
