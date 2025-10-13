import random


class Player:
    def __init__(self, score):
        self.score = score

    def update_score(self, result):
        self.score += result


class TitForTat(Player):
    def __init__(self, score):
        self.score = score
        self.init_move = 1

    def next_move(self, opp_move):
        if opp_move == 0:
            return 0
        elif opp_move == 1:
            return 1


class Random(Player):
    def __init__(self, score):
        self.score = score
        self.init_move = random.choice([0, 1])

    def next_move(self):
        return random.choice([0, 1])
