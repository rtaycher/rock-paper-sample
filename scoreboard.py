from shared_ctx import DB

import sqlalchemy
from flask_sqlalchemy import orm
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError


class Player(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<Player {self.name}>'


class GameInvitation(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    invitee_id = DB.Column(DB.Integer, DB.ForeignKey('player.id'), nullable=False)
    invitee = orm.relationship("Player")
    choice_id = DB.Column(DB.Integer)

    def __repr__(self):
        return f'<GameSession {self.id}>'


class GameResult(DB.Model):
    id = DB.Column(DB.Integer, primary_key=True)
    winner_id = DB.Column(DB.Integer, DB.ForeignKey('player.id'), nullable=True)
    winner = orm.relationship("Player")
    timestamp = DB.Column(DB.DateTime, server_default=sqlalchemy.sql.func.now(), index=True)

    def __repr__(self):
        return f'<GameResult {self.winner} {self.timestamp}>'


def find_or_create_player(db, name):
    player = Player.query.filter_by(name=name).first()
    if not player:
        player = Player(name=name)
        db.session.add(player)
        db.session.commit()
        player = Player.query.filter_by(name=name).first()
    return player


def init_database(db):
    db.create_all()
    find_or_create_player(db, name='Computer')
    find_or_create_player(db, name='Player1')


def add_win(db, winner_name):
    result = GameResult(winner=find_or_create_player(db, winner_name))
    db.session.add(result)
    db.session.commit()


def create_invitation(db, invitee_name, choice_id):
    invitation = GameInvitation(invitee=find_or_create_player(db, invitee_name), choice_id=choice_id)
    db.session.add(invitation)
    db.session.commit()
    return invitation


def consume_invitation(db, session_id):
    invitation = GameInvitation.query.get(session_id)
    player1_data = (invitation.invitee.name, invitation.choice_id)
    db.session.delete(invitation)
    db.session.commit()
    return player1_data


def get_winners(limit):
    results = GameResult.query.order_by(desc(GameResult.timestamp)).limit(limit).all()
    return [dict(winner=v.winner.name, timestamp=v.timestamp) for v in results]


def main(db):
    try:
        init_database(db)
    except SQLAlchemyError:
        db.session.rollback()
        db.session.close()


if __name__ == '__main__':
    main(DB)
