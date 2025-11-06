from abc import abstractmethod, ABC
import random


class Player(ABC):
    def __init__(self):
        self.init_move = 0
        self.last_move = self.init_move
        self.score = 0
        self.current_move = self.last_move

    def update_score(self, result):
        self.score += result

    @abstractmethod
    def gen_move(self, opp_last_move: int) -> int:
        pass


class TitForTat(Player):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.last_move

    def gen_move(self, opp_last_move: int) -> int:
        if opp_last_move == 0:
            self.current_move = 0
            return 0
        elif opp_last_move == 1:
            self.current_move = 1
            return 1
        else:
            raise ValueError(f"input error next_move({opp_last_move})")


class Random(Player):
    def __init__(self):
        super().__init__()
        self.init_move = random.choice([0, 1])
        self.last_move = self.init_move
        self.current_move = self.last_move
        self.score = 0

    def gen_move(self, opp_last_move: int) -> int:
        self.current_move = random.choice([0, 1])
        return self.current_move


class Unconditional_Coopearator(Player):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.init_move

    def gen_move(self, opp_last_move: int) -> int:
        self.current_move = 1
        return self.current_move


class Unconditional_Defector(Player):
    def __init__(self):
        super().__init__()
        self.init_move = 0
        self.last_move = self.init_move
        self.current_move = self.init_move
        self.score = 0

    def gen_move(self, opp_last_move: int) -> int:
        self.current_move = 0
        return self.current_move


class Grim_Trigger(Player):
    def __init__(self):
        super().__init__()
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.init_move
        self.triggered = False

    def gen_move(self, opp_last_move: int) -> int:
        if self.triggered:
            return 0
        else:
            if opp_last_move == 0:
                self.triggered = True
                return 0
            else:
                return 1
