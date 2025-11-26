from player import (
    Player,
    TitForTat,
    Random,
    Unconditional_Defector,
    Unconditional_Coopearator,
)

import numpy as np


class Game:
    def __init__(self, player_1: Player, player_2: Player, total_rounds: int):
        self.player_1 = player_1
        self.player_2 = player_2
        self.total_rounds = total_rounds
        self.current_round = 1

        self.p1_total_scores = np.zeros(total_rounds)
        self.p2_total_scores = np.zeros(total_rounds)

        self.p1_scores = np.zeros(total_rounds)
        self.p2_scores = np.zeros(total_rounds)

        self.p1_moves = np.zeros(total_rounds)
        self.p2_moves = np.zeros(total_rounds)


    def init_log(self):
        self.player_1.log_player()
        self.player_2.log_player()

    def print_status(self):
        print(
            f"\nROUND {self.current_round}/{self.total_rounds}\nPlayer_1 move: {self.player_1.current_move}\nPlayer_2 move: {self.player_2.current_move}\n\nPlayer_1 score: {self.player_1.score}\nPlayer_2 score {self.player_2.score}\n"
        )

    def log_endgame_data(self):
        print("*")
        print("round score")
        print(self.p1_scores)
        print(self.p2_scores)
        print("round move")
        print(self.p1_moves)
        print(self.p2_moves)
        print("current total score")
        print(self.p1_total_scores)
        print(self.p2_total_scores)
        print("*")


    def check_winner(self):
        if self.current_round > self.total_rounds:
            if self.player_1.score < self.player_2.score:
                print("player 1 wins")
                self.log_endgame_data()
                return True

            elif self.player_1.score > self.player_2.score:
                print("player 2 wins")
                self.log_endgame_data()
                return True

            elif self.player_1.score == self.player_2.score:
                print("tie game")
                self.log_endgame_data()
                return True
        else:
            return False

    # self.add_to_arrays(scores, self.player_1.current_move, self.player_2.current_move, self.player_1.score, self.player_2.score)
    def add_to_arrays(self, round_scores):

        self.p1_moves[self.current_round -1] = self.player_1.current_move
        self.p2_moves[self.current_round -1] = self.player_2.current_move

        self.p1_total_scores[self.current_round -1] = self.player_1.score
        self.p2_total_scores[self.current_round -1] = self.player_2.score

        (
            self.p1_scores[self.current_round - 1],
            self.p2_scores[self.current_round - 1],
        ) = round_scores


    # refactor so logging is in its own function
    def play_round(self) -> bool:

        if self.current_round == 1:
            self.player_1.current_move = self.player_1.init_move
            self.player_2.current_move = self.player_2.init_move

            round_scores = self.calculate_matrix_payoff(
                self.player_1.current_move, self.player_2.current_move
            )

            self.player_1.score, self.player_2.score = round_scores
            self.add_to_arrays(round_scores)

            self.print_status()
            self.current_round += 1

            return False
        else:

            self.player_1.last_move = self.player_1.current_move
            self.player_2.last_move = self.player_2.current_move

            self.player_1.current_move = self.player_1.gen_move(self.player_2.last_move)
            self.player_2.current_move = self.player_2.gen_move(self.player_1.last_move)


            round_scores = self.calculate_matrix_payoff(
                self.player_1.current_move, self.player_2.current_move
            )

            self.player_1.score += round_scores[0]
            self.player_2.score += round_scores[1]

            self.add_to_arrays(round_scores)

            self.print_status()
            self.current_round += 1

            # changes this to check if current_round == max_rounds
            if self.check_winner():
                return True
            else:
                return False

    def calculate_matrix_payoff(self, move_1, move_2):
        if move_1 == 1 and move_2 == 1:
            return (1, 1)
        elif move_1 == 1 and move_2 == 0:
            return (10, 0)
        elif move_1 == 0 and move_2 == 1:
            return (0, 10)
        elif move_1 == 0 and move_2 == 0:
            return (5, 5)
        else:
            raise ValueError(f"invalid inputs {move_1}, and {move_2}")

    def return_player_scores(self):
        scores = ()
        scores = self.player_1.score, self.player_2.score
        return scores


