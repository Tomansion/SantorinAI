"""Algorithm-independent training, league and tournament records.

All seat indices follow the current engine: player 0 moves first, then player 1.
"""

from dataclasses import dataclass
from typing import Literal, Self

from santorinai.core import GameState, StartMode


def positive_integer(name: str, value: int) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class TrainingConfig:
    episodes: int = 100
    max_steps: int = 512
    learn: bool = True
    learning_seats: tuple[bool, bool] = (True, True)
    start: StartMode = StartMode.placement
    seed: int | None = None

    def __post_init__(self):
        positive_integer("episodes", self.episodes)
        positive_integer("max_steps", self.max_steps)
        if len(self.learning_seats) != 2 or any(
            type(enabled) is not bool for enabled in self.learning_seats
        ):
            raise ValueError("learning_seats must contain two booleans")


@dataclass(frozen=True)
class BoardState:
    """Immutable engine snapshot; to_state() creates a private state for search."""

    heights: tuple[int, ...]
    workers: tuple[int, ...]
    to_play: int
    ply: int
    winner: int | None

    @classmethod
    def from_state(cls, state: GameState) -> Self:
        return cls(
            tuple(state.heights),
            tuple(state.workers),
            state.to_play,
            state.ply,
            state.winner,
        )

    def to_state(self) -> GameState:
        state = GameState(self.workers, self.heights, self.to_play)
        state.ply = self.ply
        state.winner = self.winner
        if self.winner is not None:
            state._legal = []
        return state


@dataclass(frozen=True)
class Transition:
    """One attempted action; rewards are indexed by seat, including opponent turns."""

    episode: int
    step: int
    player: int
    phase: Literal["placement", "move"]
    state: BoardState
    action: object
    next_state: BoardState
    rewards: tuple[float, float]
    terminated: bool
    truncated: bool
    valid: bool
    reason: str


@dataclass(frozen=True)
class EpisodeMetrics:
    episode: int
    steps: int
    winner: int | None
    rewards: tuple[float, float]
    terminated: bool
    truncated: bool
    reason: str
    duration_seconds: float


@dataclass(frozen=True)
class EpisodeResult:
    metrics: EpisodeMetrics
    transitions: tuple[Transition, ...]


@dataclass(frozen=True)
class UpdateResult:
    episode: int
    player: int
    metrics: dict[str, float]


@dataclass(frozen=True)
class TrainingResult:
    episodes_completed: int
    total_steps: int
    wins: tuple[int, int]
    draws: int
    truncated_episodes: int
    stopped_early: bool
    duration_seconds: float


@dataclass(frozen=True)
class LeagueConfig:
    episodes: int = 100
    max_steps: int = 512
    seed: int = 42
    checkpoint_every: int = 10
    max_historical_opponents: int = 5
    tournament_every: int | None = 25
    tournament_games_per_pair: int = 4
    start: StartMode = StartMode.placement

    def __post_init__(self):
        for name in (
            "episodes",
            "max_steps",
            "checkpoint_every",
            "max_historical_opponents",
        ):
            positive_integer(name, getattr(self, name))
        if self.tournament_every is not None:
            positive_integer("tournament_every", self.tournament_every)
        positive_integer("tournament_games_per_pair", self.tournament_games_per_pair)
        if self.tournament_games_per_pair % 2:
            raise ValueError("tournament_games_per_pair must be even to balance seats")


@dataclass(frozen=True)
class CheckpointInfo:
    name: str
    episode: int
    agent_type: str
    path: str
    purpose: Literal["training", "evaluation"] = "training"


@dataclass(frozen=True)
class Matchup:
    episode: int
    learner: str
    opponent: str
    learner_seat: int
    learning_seats: tuple[bool, bool]
    opponent_seed: int


@dataclass(frozen=True)
class TournamentConfig:
    participants: tuple[str, ...]
    games_per_pair: int = 4
    max_steps: int = 512
    seed: int = 42
    start: StartMode = StartMode.placement
    training_episode: int = 0

    def __post_init__(self):
        positive_integer("games_per_pair", self.games_per_pair)
        positive_integer("max_steps", self.max_steps)
        if self.games_per_pair % 2:
            raise ValueError("games_per_pair must be even to balance seats")
        if len(self.participants) < 2 or len(set(self.participants)) != len(
            self.participants
        ):
            raise ValueError("A tournament needs at least two distinct participants")


@dataclass(frozen=True)
class TournamentGame:
    training_episode: int
    participants: tuple[str, str]  # names in seat order
    game: int
    metrics: EpisodeMetrics


@dataclass(frozen=True)
class TournamentMatch:
    player_a: str
    player_b: str
    wins_a: int
    wins_b: int
    draws: int
    truncations: int
    total_steps: int

    @property
    def games(self) -> int:
        return self.wins_a + self.wins_b + self.draws + self.truncations

    @property
    def win_rate_a(self) -> float:
        return self.wins_a / self.games if self.games else 0.0


@dataclass(frozen=True)
class TournamentResult:
    training_episode: int
    matches: tuple[TournamentMatch, ...]

    @property
    def win_rates(self) -> dict[str, dict[str, float]]:
        rates: dict[str, dict[str, float]] = {}
        for match in self.matches:
            rates.setdefault(match.player_a, {})[match.player_b] = match.win_rate_a
            rates.setdefault(match.player_b, {})[match.player_a] = (
                match.wins_b / match.games if match.games else 0.0
            )
        return rates


@dataclass(frozen=True)
class LeagueResult:
    training: TrainingResult
    learner_wins: int
    opponent_wins: int
    checkpoints: tuple[CheckpointInfo, ...]
    tournaments: tuple[TournamentResult, ...]
