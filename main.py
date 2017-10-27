from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from models import *
from pony.orm import db_session, desc, commit
import os, random

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
@db_session
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
    ts = TrainingSessions(name='Test', chamber_count=5, swap_delay=200,
                     swap_start=2, swap_end=5)
    for i in range(ts.chamber_count):
        ts.chambers.create(step=i+1, dummy=Dummies[1], reaction_to_guess=random.randint(1,6))
    return 'Done'


@app.route('/test')
@db_session
def test():
    return render_template('test.html', reactions=ReactionTypes.select(lambda r: r.id > 0))


@app.route('/first_data')
@db_session
def first_data():
    cur_session = TrainingSessions.select().order_by(desc(TrainingSessions.id)).first()
    if 'user' in session:
        usr = Users.get(name=session['user'])
        prev_tries = usr.sandboxes.select(lambda s: s.session == cur_session)
        if prev_tries is not None:
            prev_tries.delete(bulk=True)
        first_chamber = Chambers.get(session=cur_session, step=1)
        img1 = first_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == 0).get().get_path()
        img2 = first_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == first_chamber.reaction_to_guess.id).get().get_path()
        return jsonify(steps=cur_session.chamber_count,
                       delay=cur_session.swap_delay,
                       img1=img1,
                       img2=img2,
                       start_time=cur_session.swap_start,
                       end_time=cur_session.swap_end)
    return 'Session not found', 404


@app.route('/next_data')
@db_session
def next_data():
    cur_session = TrainingSessions.select().order_by(desc(TrainingSessions.id)).first()
    if 'user' in session:
        usr = Users.get(name=session['user'])
        cur_chamber = Chambers.get(session=cur_session, step=int(request.args['cur_step']))
        usr.sandboxes.create(chamber=cur_chamber, guessed_reaction=ReactionTypes[int(request.args['guessed_react'])], session=cur_session)
        if int(request.args['cur_step']) < cur_session.chamber_count:
            next_chamber = Chambers.get(session=cur_session, step=int(request.args['cur_step']) + 1)
            img1 = next_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == 0).get().get_path()
            img2 = next_chamber.dummy.reactions.select(lambda r: r.reaction_type.id == next_chamber.reaction_to_guess.id).get().get_path()
            return jsonify(img1=img1,
                           img2=img2)
        elif int(request.args['cur_step']) > cur_session.chamber_count:
            return 'Bad Request', 400
    return 'Session not found', 404
    

@app.route('/admin', methods=['GET', 'POST'])
@db_session
def admin():
    if request.method == "POST":
        TrainingSessions(name=request.form['sess_name'],
                         chamber_count=request.form['sess_chamber_count'],
                         swap_delay=request.form['sess_swap_delay'],
                         swap_start=request.form['sess_swap_start'],
                         swap_end=request.form['sess_swap_end'])
    return render_template('admin.html', 
                           sessions=TrainingSessions.select().order_by(desc(TrainingSessions.id)))


@app.route('/session/<id>')
@db_session
def get_stats(id):
    cur_session = TrainingSessions[id]
    return render_template('stats.html', data=cur_session)


@app.route('/finish')
@db_session
def finish():
    if 'user' in session:
        user = Users.get(name=session['user'])
        cur_session = TrainingSessions.select().order_by(desc(TrainingSessions.id)).first()
        score = calculate_score(user, cur_session)
        return str(score) + '/' + str(cur_session.chamber_count)
    return 'Session not found', 404


def calculate_score(user, cur_session):
    score_table = ScoreTable.get(user=user, session=cur_session)
    if score_table is None:
        score_table = ScoreTable(user=user, session=cur_session)
    score_table.score = 0
    for line in user.sandboxes.select():
        if line.guessed_reaction.id == line.chamber.reaction_to_guess.id:
            score_table.score += 1
    return score_table.score

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
    app.run(host="0.0.0.0", debug=True)
    
