from flask import Flask
from models import *
from pony.orm import db_session
import os

app = Flask(__name__)

@app.route('/')
def main():
    check_new_dummies()
    return 'Hi'

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
    
