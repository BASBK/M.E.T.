from flask import Flask, render_template, session, request, redirect, url_for
from models import *
from pony.orm import db_session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        session.pop('user', None)
        session['user'] = request.form['username']
        if not Users.exists(name=session['user']):
            Users(name=session['user'])
        return redirect(url_for('test'))
    return render_template('login.html')


@app.route('/test')
def test():
    return render_template('test.html')


@db_session
def check_new_dummies():
    dummies = os.scandir(os.getcwd() + '\static\dummies')
    for d in dummies:
        if not Dummies.exists(name=d.name):
            dummy = Dummies(name=d.name, assets_path=d.path)
            reactions = os.scandir(d.path)
            for r in reactions:
                dummy.reactions.create(file_name=r.name, reaction_type=ReactionTypes[1])

if __name__ == '__main__':
    app.run(debug=True)
    
