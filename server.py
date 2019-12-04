from flask import Flask, render_template, g ,request, flash, redirect, url_for, session, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = '/545rter]qwesd#2_=1'
db_location = 'database/database.db'

#Database initialization

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = sqlite3.connect(db_location)
        g.db  = db
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('database/schema.sql', mode='r') as f:
             db.cursor().executescript(f.read())
        db.commit()

#Basic route handling
   
@app.route('/about')
def about():
    return render_template('about.html'), 200

@app.route('/contact')
def contact():
    return render_template('contact.html'), 200

@app.route('/login_success')
def login_success():
    return render_template('login_success.html'), 200

#Using WTForms to create the register form for some simple validation

class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=20)])
    name = StringField('Name', [validators.Length(min=1, max=20)])
    email= StringField('Email', [validators.Length(min=6, max=30)])
    password = PasswordField('Password', [validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password')

#Handling user registration

@app.route('/Register', methods=['GET', 'POST'])
def register(): 
    form = RegisterForm(request.form)

    #If validaitons met, add data to database and send user to login page

    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt((str(form.password.data)))

        #Open database and make sure the username doesnt already exist

        db = get_db()
        cursor = db.cursor()
        insert_user = 'SELECT * FROM users WHERE username = ?'
        cursor.execute(insert_user, [username])
        result = cursor.fetchall()
        
        #Username already exists
        if result:
            flash("That username is already taken")
            return render_template('register.html', form=form)

        #Data is considered valid, add to dB
        else:
            db.cursor().execute('INSERT INTO users(name,email,username,password)values(?,?,?,?)',(name,email,username,password))
            db.commit()
            db.close()
        
        flash('You have been registered, and can now log in!')

        return redirect(url_for('login'))
    return render_template('register.html', form=form), 200

#Handling user login

@app.route('/Login', methods=['GET','POST'])
def login():

    #Handle post method from html button
    if request.method == 'POST':
        usernameInput = request.form['username']
        passwordInput = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        result = cursor.execute('SELECT * FROM users WHERE username = ?', [usernameInput])
        user_exists = result.fetchone()
        
        #Check user exists in dB
        if user_exists:
            c = cursor.execute('SELECT password FROM users WHERE username = ?', [usernameInput])
            password_to_be_checked = c.fetchone()
            passw = password_to_be_checked[0]

            #Check that passwords match 
            if sha256_crypt.verify(passwordInput, passw):
                
                #Passwords match
                session['logged_in'] = True
                session['username'] = usernameInput
                flash("You were succesfully logged in")
                return redirect(url_for('login_success'))
            else:
                
               #Passwords not identical to that stored in dB
               app.logger.info('PASSWORD NOT MATCHED')
               flash("Incorrect username or password")
            db.close()
        else:
            #User not found in dB
            flash("Invalid username ")

        return render_template('login.html'), 200
    return render_template('login.html'), 200
 
@app.route('/send_message', methods=['GET','POST'])
def send_message():

    if request.method == 'POST':

        #On post method, take data from client side html textbox and store in dB
        message_to_send = request.form['new_message']
        send_to = request.form['send_to']
        
        #Open dB and insert data if username is valid
        if session: 
            from_user = session['username']
            db = get_db()
            cursor = db.cursor()
            result = cursor.execute('SELECT username FROM users WHERE username = ?', [send_to])
            user_exists = result.fetchone()

            if user_exists:
                cursor.execute('INSERT INTO messages (from_user, to_user, message_content) values (?,?,?)',(from_user,send_to,message_to_send))
                db.commit()
                flash('Message sent succesfully')
            else:
                flash('ERROR - username does not exist.')
                return render_template('send_message.html'), 200
        else:
            flash('You must be logged in to send messages!')
            return redirect(url_for('login'))
    return render_template('send_message.html'), 200

@app.route('/inbox', methods=['GET','POST'])
def inbox():
                
    if request.method == 'POST':

        #Open dB and insert data if username is valid

        if session:
            messages_for = session['username']
            db = get_db()
            cursor = db.cursor()
            result = cursor.execute('SELECT * FROM messages WHERE to_user = ?',[messages_for])
            result = cursor.fetchone()

            if result:  
                flash('You have a new message!')
                cursor.execute('SELECT from_user, MAX(ID) FROM messages WHERE to_user = ?',[messages_for])
                message_from = cursor.fetchone()
                message_from = message_from[0]

                cursor.execute('SELECT message_content, MAX(ID) FROM messages WHERE to_user = ?',[messages_for])
                message_content = cursor.fetchone()
                message_content = message_content[0]

                return render_template('inbox.html', message_from=message_from, message_content=message_content)
                db.close()
            else:
                flash('ERROR - You have no new messages.')
        else:
            flash('You must be logged in to view messages!')
            return redirect(url_for('login'))

        return render_template('inbox.html'), 200
    return render_template('inbox.html'), 200

#Check users credentials

def logged(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You must be logged in to view this page!')
            return redirect(url_for('login'))
    return decorated


@app.route('/forums', methods=['GET','POST'])
def forums():
    
    #Handle post method

    if request.method == 'POST':

        form_post = request.form['new_message']
        
        #If user is logged in make save forum post in dB

        if session:
            from_user = session['username']
            db = get_db()
            cursor = db.cursor()
            result = cursor.execute('INSERT INTO posts (posted_by, post_content) values (?,?)',(from_user,form_post))
            db.commit()
                
            flash('Your post is now featured on the homepage!')
            return redirect(url_for('home'))

        else: 
            flash('You must be logged in to create posts!')
            return redirect(url_for('login'))

        return render_template('forum.html'), 200
    return render_template('forum.html'), 200


#Handling routing for homepage, serve forum data if it exists

@app.route('/', methods=['GET','POST'])
def home():

    if session:
        db = get_db()
        cursor = db.cursor()
        result = cursor.execute('SELECT posted_by, MAX(ID) FROM posts')
        result = cursor.fetchone()
        
        #There is forum data to serve

        if result:  
            posted_by = result[0]
            
            postcontent = cursor.execute('SELECT post_content, MAX(ID) FROM posts')
            postcontent = cursor.fetchone()
            post_content = postcontent[0]

            return render_template('home.html', post_content=post_content,posted_by=posted_by)

        #No forum posts

        else:
            flash('No forum posts :(.') 
            return render_template('home.html'), 200
    return render_template('home.html'), 200

#Handling profile route, and delete profile post

@app.route('/Profile', methods=['GET','POST'])
def profile():

    if request.method == 'POST':
        if session:
            user = session['username']
            
            #Delete profile info in dB, leave other tables untouched
            db = get_db()
            cursor = db.cursor()
            cursor.execute('DELETE FROM users WHERE username = ?',[user])
            db.commit()
        
            return redirect(url_for('home'))
        else:
            flash('You must be logged in to delete your account!')
            return redirect(url_for('login'))
    return render_template('profile.html')

#Logout
@app.route('/Logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

#Run app

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
