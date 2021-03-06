import pony.orm.dbproviders.sqlite
from pony.orm import PrimaryKey, Required, Set, Optional, Database
from datetime import datetime

db = Database()

class TrainingSessions(db.Entity):
    name = Required(str)
    date = Required(datetime, sql_default='CURRENT_TIMESTAMP')
    chamber_count = Required(int)
    swap_delay = Required(int)
    swap_start = Required(int)
    swap_end = Required(int)

    chambers = Set('Chambers')
    sandboxes = Set('UserSandboxes')
    score_table = Set('ScoreTable')


class Chambers(db.Entity):
    step = Required(int)
    dummy = Required('Dummies')
    reaction_to_guess = Required('ReactionTypes')

    session = Optional(TrainingSessions)
    sandboxes = Set('UserSandboxes')


class Dummies(db.Entity):
    name = Required(str)
    assets_path = Required(str)
    
    reactions = Set('Reactions')
    chambers = Set(Chambers)

class ReactionTypes(db.Entity):
    type_name = Required(str, unique=True)

    reactions = Set('Reactions')
    sandboxes = Set('UserSandboxes')
    chambers = Set(Chambers)


class Reactions(db.Entity):
    dummy = Required(Dummies)
    file_name = Required(str)
    reaction_type = Required(ReactionTypes)

    def get_path(this):
        return '/static/dummies/' + this.dummy.name + '/' + this.file_name


class Users(db.Entity):
    name = Required(str)
    
    sandboxes = Set('UserSandboxes')
    score_table = Set('ScoreTable')


class UserSandboxes(db.Entity):
    user = Required(Users)
    chamber = Required(Chambers)
    guessed_reaction = Required(ReactionTypes)
    session = Required(TrainingSessions)


class ScoreTable(db.Entity):
    user = Required(Users)
    score = Required(int, default=0)
    session = Required(TrainingSessions)


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)