from pony.orm import PrimaryKey, Required, Set, Optional, Database
from datetime import datetime

db = Database()

class TrainingSessions(db.Entity):
    date = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    chamber_count = Required(int)
    swap_delay = Required(int)

    chambers = Set('Chambers')
    sandboxes = Set('UserSandboxes')
    score_table = Set('ScoreTable')


class Chambers(db.Entity):
    dummy = Required('Dummies')
    reaction_to_guess = Required('ReactionTypes')

    session = Required(TrainingSessions)


class Dummies(db.Entity):
    name = Required(str)
    assets_path = Required(str)
    
    reactions = Set('Reactions')
    sandboxes = Set('UserSandboxes')

class ReactionTypes(db.Entity):
    type = Required(str)

    reactions = Set('Reactions')
    sandboxes = Set('UserSandboxes')


class Reactions(db.Entity):
    dummy = Required(Dummies)
    file_name = Required(str)
    reaction_type = Required(ReactionTypes)


class Users(db.Entity):
    name = Required(str)
    
    sandboxes = Set('UserSandboxes')
    score_table = Optional('ScoreTable')


class UserSandboxes(db.Entity):
    user = Required(Users)
    dummy = Required(Dummies)
    guessed_reaction = Required(ReactionTypes)
    session = Required(TrainingSessions)


class ScoreTable(db.Entity):
    user = Required(Users)
    score = Required(int, default=0)
    session = Required(TrainingSessions)


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)