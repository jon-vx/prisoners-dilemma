from abc import abstractmethod, ABC
import random
import numpy as np


class Player(ABC):
    def __init__(self, rounds):
        self.rounds = rounds
        self.init_move = 0
        self.last_move = self.init_move
        self.score = 0
        self.current_move = self.last_move
        self.current_round = 1
        scores = np.zeros(rounds)

    def update_score(self, result):
        self.score += result

    @abstractmethod
    def gen_move(self, opp_last_move: int) -> int:
        pass

    @abstractmethod
    def log_player(self):
        pass


class TitForTat(Player):
    def __init__(self, rounds):
        super().__init__(rounds)
        self.score = 0
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.last_move
        scores = np.zeros(rounds)

    def gen_move(self, opp_last_move: int) -> int:
        if opp_last_move == 0:
            self.current_move = 0
            return 0
        elif opp_last_move == 1:
            self.current_move = 1
            return 1
        else:
            raise ValueError(f"input error next_move({opp_last_move})")

    def log_player(self):
        print("tit for tat")


class Random(Player):
    def __init__(self, rounds):
        super().__init__(rounds)
        self.init_move = random.choice([0, 1])
        self.last_move = self.init_move
        self.current_move = self.last_move
        self.score = 0
        scores = np.zeros(rounds)

    def gen_move(self, opp_last_move: int) -> int:
        self.current_move = random.choice([0, 1])
        return self.current_move

    def log_player(self):
        print("random")


class Unconditional_Coopearator(Player):
    def __init__(self, rounds):
        super().__init__(rounds)
        self.score = 0
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.init_move
        scores = np.zeros(rounds)

    def gen_move(self, opp_last_move: int) -> int:
        self.current_move = 1
        return self.current_move

    def log_player(self):
        print("unconditional cooperator")


class Unconditional_Defector(Player):
    def __init__(self, rounds):
        super().__init__(rounds)
        self.init_move = 0
        self.last_move = self.init_move
        self.current_move = self.init_move
        self.score = 0
        scores = np.zeros(rounds)

    def gen_move(self, opp_last_move: int) -> int:
        self.current_move = 0
        return self.current_move

    def log_player(self):
        print("unconditional defector")


class Grim_Trigger(Player):
    def __init__(self, rounds):
        super().__init__(rounds)
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.init_move
        self.triggered = False
        scores = np.zeros(rounds)

    def gen_move(self, opp_last_move: int) -> int:
        if self.triggered:
            return 0
        else:
            if opp_last_move == 0:
                self.triggered = True
                return 0
            else:
                return 1

    def log_player(self):
        print("grim trigger")


class Pavlov(Player):
    def __init__(self, rounds):
        super().__init__(rounds)
        self.init_move = 1
        self.last_move = self.init_move
        self.current_move = self.init_move

    def gen_move(self, opp_last_move: int) -> int:
        if opp_last_move == self.last_move:
            return 1
        else:
            return 0

    def log_player(self):
        print("Pavlov")
