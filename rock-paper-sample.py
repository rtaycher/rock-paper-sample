import enum
import random

import flask
import requests

app = flask.Flask(__name__)

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
paper.beats(spock)
scissors.beats(paper)
scissors.beats(lizard)
lizard.beats(spock)
lizard.beats(paper)
spock.beats(scissors)
spock.beats(lizard)


@app.route("/")
def hello():
    return "Hello World!"


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


@app.route("/play", methods=["POST"])
def play():
    data = flask.request.form
    if data.get('player', None) not in [str(c['id']) for c in CHOICES]:
        return "invalid data", 422
    player_choice_id = int(data['player'])
    r = requests.get(flask.request.host_url + "choice")
    r.raise_for_status()
    computer_choice_id = r.json()["id"]
    return flask.jsonify(results=_hand_shapes_by_id[player_choice_id].vs(_hand_shapes_by_id[computer_choice_id]))


if __name__ == "__main__":
    app.run()
