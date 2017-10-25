from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from models import *
from pony.orm import db_session, desc, commit
import os, random

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



@app.route('/init')
@db_session
def init():
    ReactionTypes(id=0, type_name='Нейтральный')
    ReactionTypes(type_name='Удивление')
    ReactionTypes(type_name='Страх')
    ReactionTypes(type_name='Гнев')
    ReactionTypes(type_name='Отвращение')
    ReactionTypes(type_name='Радость')
    ReactionTypes(type_name='Печаль')
    check_new_dummies()
    ts = TrainingSessions(chamber_count=5, swap_delay=200,
                     swap_start=2, swap_end=5)
    for i in range(ts.chamber_count):
        ts.chambers.create(step=i+1, dummy=Dummies[1], reaction_to_guess=random.randint(1,6))
    return 'Done'


@app.route('/test')
@db_session
def test():
    return render_template('test.html', reactions=ReactionTypes.select())


@app.route('/first_data')
@db_session
def first_data():
    cur_session = TrainingSessions.select().order_by(desc(TrainingSessions.id)).first()
    first_chamber = Chambers.get(session=cur_session, step=1)
    img1 = first_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == 0).get().get_path()
    img2 = first_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == first_chamber.reaction_to_guess.id).get().get_path()
    return jsonify(steps=cur_session.chamber_count,
                   delay=cur_session.swap_delay,
                   img1=img1,
                   img2=img2,
                   start_time=cur_session.swap_start,
                   end_time=cur_session.swap_end)


@app.route('/next_data')
@db_session
def next_data():
    cur_session = TrainingSessions.select().order_by(desc(TrainingSessions.id)).first()
    next_chamber = Chambers.get(session=cur_session, step=int(request.args['cur_step']) + 1)
    print(next_chamber.id)
    img1 = next_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == 0).get().get_path()
    img2 = next_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == next_chamber.reaction_to_guess.id).get().get_path()
    print(img2)
    return jsonify(img1=img1,
                   img2=img2)


@db_session
def check_new_dummies():
    dummies = os.scandir(os.getcwd() + '\static\dummies')
    for d in dummies:
        if not Dummies.exists(name=d.name):
            dummy = Dummies(name=d.name, assets_path=d.path)
            reactions = os.scandir(d.path)
            for r in reactions:
                dummy.reactions.create(file_name=r.name, reaction_type=ReactionTypes[int(r.name[0])])

if __name__ == '__main__':
    app.run(debug=True)
    
