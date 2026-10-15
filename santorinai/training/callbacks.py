"""Composable tracking hooks for training, leagues, checkpoints and tournaments."""

import json
from dataclasses import asdict
from pathlib import Path

from santorinai.training.records import (
    CheckpointInfo,
    EpisodeMetrics,
    EpisodeResult,
    LeagueConfig,
    LeagueResult,
    Matchup,
    TournamentConfig,
    TournamentGame,
    TournamentMatch,
    TournamentResult,
    TrainingConfig,
    TrainingResult,
    Transition,
    UpdateResult,
)


class TrainingCallback:
    """Override only the hooks needed; errors propagate to the caller.

    Return False from on_episode_end to stop after that episode. End hooks run
    on normal completion and early stop, not after an exception. Tournament
    hooks are separate from training hooks and never trigger agent updates.
    """

    def on_training_start(self, config: TrainingConfig) -> None:
        pass

    def on_episode_start(self, episode: int) -> None:
        pass

    def on_step(self, transition: Transition) -> None:
        pass

    def on_update(self, update: UpdateResult) -> None:
        pass

    def on_episode_end(self, episode: EpisodeResult) -> bool | None:
        return None

    def on_training_end(self, result: TrainingResult) -> None:
        pass

    def on_league_start(self, config: LeagueConfig) -> None:
        pass

    def on_matchup(self, matchup: Matchup) -> None:
        pass

    def on_checkpoint_saved(self, checkpoint: CheckpointInfo) -> None:
        pass

    def on_tournament_start(self, config: TournamentConfig) -> None:
        pass

    def on_tournament_game(self, game: TournamentGame) -> None:
        pass

    def on_tournament_match(self, match: TournamentMatch) -> None:
        pass

    def on_tournament_end(self, result: TournamentResult) -> None:
        pass

    def on_league_end(self, result: LeagueResult) -> None:
        pass


class HistoryCallback(TrainingCallback):
    """Store summaries, never full trajectories or individual tournament games.

    Training start clears history. Use JSONLLogger alone for long experiments.
    """

    def __init__(self):
        self.episodes: list[EpisodeMetrics] = []
        self.updates: list[UpdateResult] = []
        self.matchups: list[Matchup] = []
        self.checkpoints: list[CheckpointInfo] = []
        self.tournaments: list[TournamentResult] = []
        self.result: TrainingResult | None = None
        self.league_result: LeagueResult | None = None

    def on_training_start(self, config: TrainingConfig) -> None:
        self.episodes.clear()
        self.updates.clear()
        self.matchups.clear()
        self.checkpoints.clear()
        self.tournaments.clear()
        self.result = None
        self.league_result = None

    def on_update(self, update: UpdateResult) -> None:
        self.updates.append(update)

    def on_episode_end(self, episode: EpisodeResult) -> None:
        self.episodes.append(episode.metrics)

    def on_matchup(self, matchup: Matchup) -> None:
        self.matchups.append(matchup)

    def on_checkpoint_saved(self, checkpoint: CheckpointInfo) -> None:
        self.checkpoints.append(checkpoint)

    def on_tournament_end(self, result: TournamentResult) -> None:
        self.tournaments.append(result)

    def on_training_end(self, result: TrainingResult) -> None:
        self.result = result

    def on_league_end(self, result: LeagueResult) -> None:
        self.league_result = result


class JSONLLogger(TrainingCallback):
    """Append event records immediately; start/end events delimit repeated runs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _write(self, event: str, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": event, **data}, allow_nan=False) + "\n")

    def on_training_start(self, config: TrainingConfig) -> None:
        self._write("training_start", asdict(config))

    def on_update(self, update: UpdateResult) -> None:
        self._write("update", asdict(update))

    def on_episode_end(self, episode: EpisodeResult) -> None:
        self._write("episode_end", asdict(episode.metrics))

    def on_training_end(self, result: TrainingResult) -> None:
        self._write("training_end", asdict(result))

    def on_league_start(self, config: LeagueConfig) -> None:
        self._write("league_start", asdict(config))

    def on_matchup(self, matchup: Matchup) -> None:
        self._write("matchup", asdict(matchup))

    def on_checkpoint_saved(self, checkpoint: CheckpointInfo) -> None:
        self._write("checkpoint_saved", asdict(checkpoint))

    def on_tournament_start(self, config: TournamentConfig) -> None:
        self._write("tournament_start", asdict(config))

    def on_tournament_game(self, game: TournamentGame) -> None:
        self._write("tournament_game", asdict(game))

    def on_tournament_match(self, match: TournamentMatch) -> None:
        self._write("tournament_match", asdict(match))

    def on_tournament_end(self, result: TournamentResult) -> None:
        self._write("tournament_end", asdict(result))

    def on_league_end(self, result: LeagueResult) -> None:
        # Other records already contain checkpoint and tournament details.
        self._write(
            "league_end",
            {
                "learner_wins": result.learner_wins,
                "opponent_wins": result.opponent_wins,
                "episodes_completed": result.training.episodes_completed,
                "checkpoints_saved": len(result.checkpoints),
                "tournaments_completed": len(result.tournaments),
            },
        )
