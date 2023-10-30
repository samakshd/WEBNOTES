from flask import Flask, render_template, request, url_for, redirect, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from os import listdir
import hashlib


app = Flask(__name__)
app.secret_key = "SECRETKEY"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Notepad.db'
app.config['CLIENT_NOTES'] = './Clients'

db = SQLAlchemy(app)


class Data(db.Model):
    '''
    Sno, subject, content, date
    '''
    Sno = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    user = db.Column(db.Integer, nullable=False)


class Data_Guest(db.Model):
    '''
    Sno, subject, content, date
    '''
    Sno = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class User(db.Model):
    '''
    UID, username, email, password
    '''
    UID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12), nullable=True)



@app.route('/')
@app.route('/home')
def home():
    session['user'] = ""
    return render_template("home.html")


@app.route('/download/<id>', methods=['GET', 'POST'])
def downloader(id):
    if request.method == "POST":
        note = Data.query.filter_by(Sno=int(id)).first()
        with open('./Clients/WebNote.txt', 'w') as f:
            f.write(note.subject)
            f.write("\n\n")
            f.write(note.content)
        f.close()
        return send_from_directory(app.config['CLIENT_NOTES'], filename="WebNote.txt", as_attachment=True)

    return "ERROR IN DOWNLOADING FILE"


@app.route('/download-guest/<id>', methods=['GET', 'POST'])
def download_guest(id):
    note = Data_Guest.query.filter_by(Sno=id).first()
    with open('./Clients/WebNote.txt', 'w') as f:
        f.write(note.subject)
        f.write("\n\n")
        f.write(note.content)
    f.close()
    return send_from_directory(app.config['CLIENT_NOTES'], filename="WebNote.txt", as_attachment=True)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if(request.method == "POST"):
        username = request.form.get('new_username')
        email = request.form.get('email')
        password = request.form.get('new_password')
        ep = hashlib.md5(password.encode())

        username_check = User.query.filter_by(username=username).first()
        if not username:
            error = 'Username is Required'
        elif not password:
            error = 'Password is Required'
        elif not email:
            error = 'Email is required'
        else:
            if username_check is None:
                entry = User(username=username, email=email,
                             password=ep.hexdigest(), date=datetime.now())

                db.session.add(entry)
                db.session.commit()
                return redirect(url_for("login"))
            else:
                error = 'Username Already Exists'

    return render_template("signup.html", error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():

    if('user' in session and (User.query.filter_by(username=session['user']).first() is not None)):
        return redirect(url_for("dashboard", user=session['user']))

    error = None
    if(request.method == "POST"):

        username = request.form.get('username')
        password = request.form.get('password')
        ep = hashlib.md5(password.encode())
        user_check = User.query.filter_by(username=username, password=ep.hexdigest()).first()

        if user_check is None:
            error = 'Invalid Credentials'
        else:
            session['user'] = username
            return redirect(url_for("dashboard", user=username))

    return render_template("login.html", error=error)


@app.route('/<user>/dashboard', methods=['GET', 'POST'])
def dashboard(user):

    if('user' in session and session['user'] == user):
        posts = Data.query.filter_by(user=user).all()
        return render_template("dashboard.html", posts=posts, user=user)
    else:
        error = "UNAUTHORIZED ACCESS"
        return redirect(url_for("login"))

@app.route('/<user>/notepad/<id>', methods=['GET', 'POST'])
def notepad(user, id):
    if('user' in session and session['user'] == user):
        update = Data.query.filter_by(Sno=id).first()
        error = None
        if(request.method == "POST"):
            if(id == "0"):
                subject = request.form.get('subject')
                content = request.form.get('content')

                if not subject:
                    error = "Title is Required"
                elif not content:
                    error = "Content is Required"
                else:

                    entry = Data(subject=subject, content=content, date=datetime.now(), user=user)

                    db.session.add(entry)
                    db.session.commit()
                    return redirect(url_for("dashboard", user=user))

                return render_template('notepad.html', update=update, id=id, user=user, error=error)

            else:

                subject = request.form.get('subject')
                content = request.form.get('content')

                if not subject:
                    error = "Title is Required"
                elif not content:
                    error = "Content is Required"
                else:

                    updated = Data.query.filter_by(Sno=int(id)).update({Data.subject: subject, Data.content: content, Data.date: datetime.now()})

                    db.session.commit()
                    return redirect(url_for("dashboard", user=user))

                return render_template('notepad.html', update=update, id=id, user=user, error=error)

        return render_template('notepad.html', update=update, id=id, user=user, error=error)

    else:
        error = "UNAUTHORIZED ACCESS"
        return redirect(url_for("login"))


@app.route('/<user>/delete/<id>', methods=['GET', 'POST'])
def delete(user, id):
    if request.method == "POST":
        note = Data.query.filter_by(Sno=int(id)).first()
        db.session.delete(note)
        db.session.commit()
        return redirect(url_for('dashboard', user=user))
    return "ERROR IN DELETING FILE"




@app.route('/guest/notepad', methods=['GET', 'POST'])
def guest_notepad():
    error = None
    if(request.method == "POST"):

        subject = request.form.get('subject')
        content = request.form.get('content')

        if not subject:
            error = "Title is Required"
        elif not content:
            error = "Content is Required"
        else:
            entry = Data_Guest(subject=subject, content=content, date=datetime.now())

            db.session.add(entry)
            db.session.commit()

            data = Data_Guest.query.filter_by().all()
            return redirect(url_for("download_guest", id=data[-1].Sno))

        return render_template('guest_notepad.html', error=error)

    return render_template('guest_notepad.html', error=error)



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
