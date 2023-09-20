from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Configure the database
DATABASE = 'users.db'

def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      email TEXT NOT NULL,
                      password TEXT NOT NULL,
                      profile_picture TEXT)''')
    conn.commit()
    conn.close()
create_table()

def is_username_taken(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def is_email_taken(email):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

@app.route('/')
def index():
    return render_template('signup.html')

@app.route('/home/<username>', methods=['GET', 'POST'])
def home(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if request.method == 'POST':
        query = request.form['search_query']
        
        cursor.execute('SELECT username FROM users WHERE username LIKE ?', ('%' + query + '%',))
        search_results = [result[0] for result in cursor.fetchall()]
        conn.close()
        
        return render_template('home.html', username=username, profile_picture=user[4], search_results=search_results)
    
    conn.close()

    if user:
        return render_template('home.html', username=user[1], profile_picture=user[4])
    else:
        # Handle user not found
        error_message = "User not found"
        return render_template('error.html', error_message=error_message)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    profile_picture = request.files['profile_picture']
    if profile_picture:
        profile_picture_filename = secure_filename(profile_picture.filename)
        profile_picture_path = os.path.join('static/profile_pictures', profile_picture_filename)
        profile_picture.save(profile_picture_path)
    else:
        profile_picture_filename = None

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, email, password, profile_picture) VALUES (?, ?, ?, ?)',
                   (username, email, password, profile_picture_filename))
    conn.commit()
    conn.close()

    return redirect(url_for('home', username=username))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('home', username=username))
        else:
            error_message = "Invalid username or password"
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

@app.route('/account/<username>')
def account(username):  
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        # user[1] is the username, user[2] is the email, user[4] is the profile_picture
        return render_template('account.html', username=user[1], email=user[2], profile_picture=user[4])
    else:
        # Handle user not found
        error_message = "User not found"
        return render_template('error.html', error_message=error_message)
    
@app.route('/change_password/<username>')
def change_password_page(username):
    return render_template('change_password.html', username=username)

@app.route('/change_password/<username>', methods=['POST'])
def change_password(username):
    old_password = request.form['old_password']
    new_password = request.form['new_password']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, old_password))
    user = cursor.fetchone()

    if user:
        cursor.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
        conn.commit()
        conn.close()
        success_message = "Password changed successfully"
        return render_template('account.html', username=username, email=user[2], success_message=success_message)
    else:
        conn.close()
        error_message = "Incorrect old password"
        return render_template('account.html', username=username, email=user[2], error_message=error_message)
    
@app.route('/upload_profile_picture/<username>')
def upload_profile_picture_page(username):
    return render_template('upload_profile_picture.html', username=username)

@app.route('/upload_profile_picture/<username>', methods=['POST'])
def upload_profile_picture(username):
    profile_picture = request.files['profile_picture']
    if profile_picture:
        profile_picture_filename = secure_filename(profile_picture.filename)
        profile_picture_path = os.path.join('static/profile_pictures', profile_picture_filename)
        profile_picture.save(profile_picture_path)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET profile_picture = ? WHERE username = ?', (profile_picture_filename, username))
        conn.commit()
        conn.close()

    return redirect(url_for('account', username=username))

@app.route('/delete_account/<username>')
def delete_account(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

    # Redirect to a page indicating successful account deletion
    return redirect(url_for('account_deleted'))

@app.route('/account_deleted')
def account_deleted():
    return "Your account has been deleted successfully."

# @app.route('/create_tweet', methods=['POST'])
# def create_tweet():
    # Handle the form submission and tweet creation logic here
    # Extract tweet text and image from the form data
    # Save the tweet and image to your database or storage system
    # return redirect(url_for('home'))  # Redirect back to the home page after tweeting
    
if __name__ == '__main__':
    app.run(debug=True)