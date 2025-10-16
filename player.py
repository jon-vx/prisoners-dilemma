from abc import abstractmethod, ABC
import random


class Player(ABC):
    def __init__(self, score):
        self.init_move = 0
        self.last_move = self.init_move
        self.score = score

    def update_score(self, result):
        self.score += result

    @abstractmethod
    def next_move(self, opp_move: int) -> int:
        pass


class TitForTat(Player):
    def __init__(self, score):
        super().__init__(score)
        self.init_move = 1
        self.last_move = self.init_move

    def next_move(self, opp_move: int) -> int:
        if opp_move == 0:
            return 0
        elif opp_move == 1:
            return 1
        else:
            raise ValueError(f"input error next_move({opp_move})")


class Random(Player):
    def __init__(self, score):
        super().__init__(score)
        self.init_move = random.choice([0, 1])
        self.last_move = self.init_move

    def next_move(self, opp_move: int) -> int:
        self.last_move = random.choice([0, 1])
        return self.last_move
