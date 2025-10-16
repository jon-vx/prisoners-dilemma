from re import error
from player import Player, TitForTat, Random


class Game:
    def __init__(self, player_1: Player, player_2: Player, total_rounds: int):
        self.player_1 = player_1
        self.player_2 = player_2
        self.total_rounds = total_rounds
        self.current_round = 1

        print(f"initialized players {player_1} and {player_2}")

    def check_winner(self):
        if self.current_round == self.total_rounds:
            if self.player_1.score < self.player_2.score:
                print("player 1 wins")

            elif self.player_1.score > self.player_2.score:
                print("player 2 wins")

            elif self.player_1.score == self.player_2.score:
                print("tie game")

    def play_round(self) -> bool:
        if self.current_round == 1:
            player_1_move: int = self.player_1.init_move
            player_2_move: int = self.player_2.init_move

            scores = self.calculate_matrix_payoff(player_1_move, player_2_move)
            player_1_score, player_2_score = scores

            self.player_1.score = player_1_score
            self.player_2.score = player_2_score

            print(
                f"\nPlayer_1 move: {player_1_move}\nPlayer_2 move: {player_2_move}\n\nPlayer_1 score: {self.player_1.score}\nPlayer_2 score {self.player_2.score}\n"
            )

            self.current_round += 1
            return False
        else:
            player_1_move: int = self.player_1.next_move(self.player_2.last_move)
            player_2_move: int = self.player_2.next_move(self.player_1.last_move)

            scores = self.calculate_matrix_payoff(player_1_move, player_2_move)
            player_1_score, player_2_score = scores

            self.player_1.score += player_1_score
            self.player_2.score += player_2_score
            print(
                f"\nPlayer_1 move: {player_1_move}\nPlayer_2 move: {player_2_move}\n\nPlayer_1 score: {self.player_1.score}\nPlayer_2 score {self.player_2.score}\n"
            )

            if self.check_winner() is True:
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
