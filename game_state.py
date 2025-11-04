from player import (
    Player,
    TitForTat,
    Random,
    Unconditional_Defector,
    Unconditional_Coopearator,
)


class Game:
    def __init__(self, player_1: Player, player_2: Player, total_rounds: int):
        self.player_1 = player_1
        self.player_2 = player_2
        self.total_rounds = total_rounds
        self.current_round = 1

    def print_status(self):
        print(
            f"\nROUND {self.current_round}/{self.total_rounds}\nPlayer_1 move: {self.player_1.current_move}\nPlayer_2 move: {self.player_2.current_move}\n\nPlayer_1 score: {self.player_1.score}\nPlayer_2 score {self.player_2.score}\n"
        )

    def check_winner(self):
        if self.current_round == self.total_rounds:
            if self.player_1.score < self.player_2.score:
                print("player 1 wins")
                return True

            elif self.player_1.score > self.player_2.score:
                print("player 2 wins")
                return True

            elif self.player_1.score == self.player_2.score:
                print("tie game")
                return True
        else:
            return False

    def play_round(self) -> bool:
        if self.current_round == 1:
            self.player_1.current_move = self.player_1.init_move
            self.player_2.current_move = self.player_2.init_move

            scores = self.calculate_matrix_payoff(
                self.player_1.current_move, self.player_2.current_move
            )

            self.player_1.score, self.player_2.score = scores

            self.print_status()

            self.current_round += 1
            return False
        else:
            self.player_1.last_move = self.player_1.current_move
            self.player_2.last_move = self.player_2.current_move

            self.player_1.current_move = self.player_1.gen_move(self.player_2.last_move)
            self.player_2.current_move = self.player_2.gen_move(self.player_1.last_move)

            player_1_score, player_2_score = self.calculate_matrix_payoff(
                self.player_1.current_move, self.player_2.current_move
            )

            self.player_1.score += player_1_score
            self.player_2.score += player_2_score

            self.print_status()

            self.current_round += 1

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
