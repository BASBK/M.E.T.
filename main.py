from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from models import *
from pony.orm import db_session, desc, commit, count
import os, random
from PIL import Image

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


@db_session
def init():
    ReactionTypes(id=0, type_name='Нейтральный')
    ReactionTypes(type_name='Удивление')
    ReactionTypes(type_name='Страх')
    ReactionTypes(type_name='Гнев')
    ReactionTypes(type_name='Отвращение')
    ReactionTypes(type_name='Радость')
    ReactionTypes(type_name='Печаль')
    load_new_dummies()
    return 'Done'


@app.route('/test')
@db_session
def test():
    if 'user' in session:
        if TrainingSessions.select()[:] != []:
            return render_template('test.html', reactions=ReactionTypes.select(lambda r: r.id > 0))
        return 'Create training session first!', 404
    return redirect(url_for('main'))


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
    max_count = count(Dummies.select()) * 6
    if request.method == "POST":
        chamber_count = int(request.form['sess_chamber_count'])
        if chamber_count > max_count:
            chamber_count = max_count
        ts = TrainingSessions(name=request.form['sess_name'],
                         chamber_count=chamber_count,
                         swap_delay=request.form['sess_swap_delay'],
                         swap_start=request.form['sess_swap_start'],
                         swap_end=request.form['sess_swap_end'])
        gen_chambers(ts)
    return render_template('admin.html', 
                           sessions=TrainingSessions.select().order_by(desc(TrainingSessions.id)), max_chambers=max_count)


def gen_chambers(ts):
    t = 0
    while t < (ts.chamber_count):
        chamber = Chambers(step=t+1, 
                           dummy=Dummies.select_random(1)[0],
                           reaction_to_guess=random.randint(1,6)) 
        if not ts.chambers.select(lambda c: c.dummy == chamber.dummy and c.reaction_to_guess == chamber.reaction_to_guess).exists():
            ts.chambers.add(chamber)
            t+=1
        else:
            chamber.delete()


@app.route('/session/<id>')
@db_session
def get_stats(id):
    cur_session = TrainingSessions[id]
    sandboxes = {}
    for row in cur_session.score_table:
        sandboxes[row.user.name] = []
        for s in row.user.sandboxes.select().order_by(lambda snd: snd.chamber.step):
            sandboxes[row.user.name].append(s)   
    return render_template('stats.html', data=cur_session, sandboxes=sandboxes)


@app.route('/finish')
@db_session
def finish():
    if 'user' in session:
        user = Users.get(name=session['user'])
        cur_session = TrainingSessions.select().order_by(desc(TrainingSessions.id)).first()
        score = calculate_score(user, cur_session)
        return render_template('finish.html')
    return redirect(url_for('main'))


def calculate_score(user, cur_session):
    score_table = ScoreTable.get(user=user, session=cur_session)
    if score_table is None:
        score_table = ScoreTable(user=user, session=cur_session)
    score_table.score = 0
    for line in user.sandboxes.select():
        if line.guessed_reaction.id == line.chamber.reaction_to_guess.id:
            score_table.score += 1
    return score_table.score


@app.route('/admin/load_imgs')
@db_session
def load_new_dummies():
    size = 900, 600
    img_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
    dummies = os.scandir(os.getcwd() + '\static\dummies')
    for d in dummies:
        if not Dummies.exists(name=d.name):
            dummy = Dummies(name=d.name, assets_path=d.path)
            print('New face added: ' + d.name)
            reactions = os.scandir(d.path)
            for r in reactions:
                if r.name.lower().split('.')[-1] in img_formats:
                    react = dummy.reactions.create(file_name=r.name, reaction_type=ReactionTypes[int(r.name[0])])
                    img = Image.open(react.dummy.assets_path + '\\' + react.file_name)
                    img.thumbnail(size)
                    img.save(react.dummy.assets_path + '\\' + react.file_name)
                    img.close()
                    print('\tReaction image ' + react.file_name + ' was compressed and added.')
                else:
                    print('\t' + r.name + ' is not an image. Ignored.')
    max_count = count(Dummies.select()) * 6
    return str(max_count);


if __name__ == '__main__':
    try:
        init()
        print('Initiation complete!\nFace loading complete!')
    except:
        print('Initiated already!')
        load_new_dummies()
        print('Face loading complete!')
    app.run(host="0.0.0.0", debug=False)
    
