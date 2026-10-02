export interface Strategy {
  key: string;
  name: string;
  description: string;
}

export interface TournamentConfig {
  strategies: string[];
  rounds: number;
  matches_per_pair: number;
  seed: number;
  include_self_play: boolean;
  payoffs: {
    temptation: number;
    reward: number;
    punishment: number;
    sucker: number;
  };
}

export interface MatchSummary {
  id: string;
  strategy_a: string;
  strategy_b: string;
  score_a: number;
  score_b: number;
  rounds: number;
  cooperation_rate_a: number;
  cooperation_rate_b: number;
  winner: "a" | "b" | "tie";
}

export interface MatchDetail extends MatchSummary {
  history: {
    round_number: number;
    move_a: "cooperate" | "defect";
    move_b: "cooperate" | "defect";
    cumulative_score_a: number;
    cumulative_score_b: number;
  }[];
}

export interface Tournament {
  id: string;
  configuration: TournamentConfig;
  created_at: string;
  matches: MatchSummary[];
  leaderboard: {
    rank: number;
    strategy_key: string;
    total_score: number;
    wins: number;
    losses: number;
    ties: number;
    cooperation_rate: number;
  }[];
}
