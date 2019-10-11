import enum
import random

import flask
import requests

from shared_ctx import app, DB
import scoreboard

CHOICES = [dict(id=1, name="rock"), dict(id=2, name="paper"), dict(id=3, name="scissors"),
           dict(id=4, name="lizard"), dict(id=5, name="spock")]
_hand_shapes_by_id = dict()
_beat_dictionary = dict()


class GameResult(str, enum.Enum):
    Win = "win"
    Loss = "loss"
    Tie = "tie"


class HandShape:
    def __init__(self, _id):
        self.id = _id
        _hand_shapes_by_id[self.id] = self

    def __repr__(self):
        return [c['name'] for c in CHOICES if c['id'] == self.id][0]

    def beats(self, loser):
        _beat_dictionary[self.id] = _beat_dictionary.get(self.id, [])
        _beat_dictionary[self.id].append(loser.id)

    def vs(self, other):
        if self.id == other.id:
            return GameResult.Tie
        elif other.id in _beat_dictionary[self.id]:
            return GameResult.Win
        elif self.id in _beat_dictionary[other.id]:
            return GameResult.Loss
        else:
            raise Exception(f"found unregistered result for {self} vs {other}")


rock, paper, scissors, lizard, spock = HandShape(1), HandShape(2), HandShape(3), HandShape(4), HandShape(5)
rock.beats(scissors)
rock.beats(lizard)
paper.beats(rock)
paper.beats(spock)
scissors.beats(paper)
scissors.beats(lizard)
lizard.beats(spock)
lizard.beats(paper)
spock.beats(scissors)
spock.beats(rock)


@app.route("/")
def hello():
    return f'<a href="/winners">winners</a>'


@app.route("/choices")
def choices():
    return flask.jsonify(CHOICES)


@app.route("/choice")
def choice():
    r = requests.get(flask.request.host_url + "random")
    r.raise_for_status()
    random_index = r.json()["random_number"] % len(CHOICES)
    return flask.jsonify(CHOICES[random_index])


@app.route("/random")
def random_():
    return flask.jsonify(random_number=random.randrange(start=1, stop=100 + 1))


@app.route("/winners", methods=["GET", "DELETE"])
def winners():
    """get last x winners(defaults to 10)"""
    if flask.request.method == "GET":
        limit = flask.request.args.get('limit', 10)
        return flask.jsonify(scoreboard.get_winners(limit))
    elif flask.request.method == "DELETE":
        DB.DateTime.query.delete()


@app.route("/play", methods=["POST"])
def play():
    data = flask.request.form
    if 'player' not in data:
        return f"invalid data, missing choice#", 422
    if data.get('player', None) not in [str(c['id']) for c in CHOICES]:
        return f"invalid data, player gave invalid choice# {data['player']}", 422
    player_choice_id = int(data['player'])
    r = requests.get(flask.request.host_url + "choice")
    r.raise_for_status()
    computer_choice_id = r.json()["id"]
    result = _hand_shapes_by_id[player_choice_id].vs(_hand_shapes_by_id[computer_choice_id])
    if result == GameResult.Win:
        scoreboard.add_win(DB, "Player1")
    elif result == GameResult.Loss:
        scoreboard.add_win(DB, "Computer")
    return flask.jsonify(results=result, player=player_choice_id, computer=computer_choice_id)


@app.route("/two_player_play/<int:session_id>", methods=["POST"])
def two_player_play(session_id):
    """consume the link by having the second player send their data"""
    data = flask.request.form
    if data.get('player2_choice_id', None) not in [str(c['id']) for c in CHOICES]:
        return "invalid data", 422
    if "player2_name" not in data:
        return "invalid data, missing player name", 422
    player1_name, player1_choice_id = scoreboard.consume_invitation(DB, session_id)

    player2_choice_id = int(data['player2_choice_id'])
    player2_name = data['player2_name']

    result = _hand_shapes_by_id[player1_choice_id].vs(_hand_shapes_by_id[player2_choice_id])
    winner_name = None
    if result == GameResult.Win:
        scoreboard.add_win(DB, player1_name)
        winner_name = player1_name
    elif result == GameResult.Loss:
        scoreboard.add_win(DB, player2_name)
        winner_name = player2_name

    return flask.jsonify(winner=winner_name, player1_choice_id=player1_choice_id,
                         player2_choice_id=player2_choice_id)


@app.route("/make_game_session", methods=["POST"])
def make_game_session():
    """Create a link a person can send to another person to play a round"""
    data = flask.request.form
    if not data.get('player_name', None):
        return "invalid data", 422
    if not data.get('player_choice_id', None):
        return "invalid data", 422
    session_id = scoreboard.create_invitation(DB,
                                              data['player_name'],
                                              int(data['player_choice_id'])).id
    return flask.jsonify(url=f'{flask.request.url_root}two_player_play/{session_id}')


if __name__ == "__main__":
    scoreboard.init_database(DB)
    app.run()
