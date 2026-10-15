"""Opponent sampling, rotating learner seats, checkpoints and league evaluation."""

from collections.abc import Sequence
from dataclasses import replace
from functools import partial
from random import Random
from time import perf_counter

from santorinai.agents import Agent
from santorinai.training.agents import CheckpointableAgent
from santorinai.training.callbacks import TrainingCallback
from santorinai.training.checkpoints import CheckpointManager
from santorinai.training.opponents import Opponent, OpponentPool
from santorinai.training.records import (
    LeagueConfig,
    LeagueResult,
    Matchup,
    TrainingConfig,
    TrainingResult,
)
from santorinai.training.tournament import run_tournament
from santorinai.training.trainer import Trainer


class LeagueTrainer:
    """Train one learner against a changing mixture of independent opponents.

    Initial, periodic and final snapshots enter the opponent pool. Only recent
    automatically added snapshots are retained in that pool; all saved artifacts
    remain on disk. Tournaments reload the current learner checkpoint and never
    call the live learner, so evaluation cannot change its RNG or model state.
    """

    def __init__(
        self,
        learner: CheckpointableAgent,
        opponents: OpponentPool,
        checkpoints: CheckpointManager,
        config: LeagueConfig | None = None,
        callbacks: Sequence[TrainingCallback] = (),
        learner_name: str = "learner",
    ):
        if not isinstance(learner, CheckpointableAgent):
            raise TypeError("The league learner must implement CheckpointableAgent")
        if not learner_name or any(e.name == learner_name for e in opponents.entries):
            raise ValueError("The learner needs a unique nonempty name")
        self.learner = learner
        self.opponents = opponents
        self.checkpoints = checkpoints
        self.config = config if config is not None else LeagueConfig()
        self.callbacks = tuple(callbacks)
        self.learner_name = learner_name

    def _create_opponent(self, entry: Opponent, seed: int) -> Agent:
        agent = entry.create(seed)
        if agent is self.learner:
            raise ValueError("Opponent factories must not return the live learner")
        return agent

    def run(self) -> LeagueResult:
        started = perf_counter()
        config = self.config
        training_config = TrainingConfig(
            episodes=config.episodes,
            max_steps=config.max_steps,
            learning_seats=(True, False),
            start=config.start,
            seed=config.seed,
        )
        for callback in self.callbacks:
            callback.on_training_start(training_config)
        for callback in self.callbacks:
            callback.on_league_start(config)

        # Evaluation has its own random stream and agent instances. Changing the
        # tournament schedule must not change training matchups or trajectories.
        rng, evaluation_rng = Random(config.seed), Random(config.seed)
        prefix = f"{self.learner_name}@"
        historical = [
            entry.name
            for entry in self.opponents.entries
            if entry.checkpoint is not None and entry.name.startswith(prefix)
        ]
        saved = []
        tournaments = []

        def save_snapshot(episode, add_to_pool=True):
            info = self.checkpoints.save(
                self.learner,
                episode,
                purpose="training" if add_to_pool else "evaluation",
            )
            saved.append(info)
            if add_to_pool:
                name = prefix + info.name
                self.opponents.add_checkpoint(
                    self.checkpoints, info, type(self.learner), name=name
                )
                historical.append(name)
                while len(historical) > config.max_historical_opponents:
                    self.opponents.remove(historical.pop(0))
            for callback in self.callbacks:
                callback.on_checkpoint_saved(info)
            return info

        save_snapshot(0)
        wins = [0, 0]
        learner_wins = opponent_wins = draws = truncations = total_steps = completed = 0
        stopped = False
        for index in range(1, config.episodes + 1):
            entry = self.opponents.sample(rng)
            opponent_seed, start_seed = (rng.randrange(2**32) for _ in range(2))
            opponent = self._create_opponent(entry, opponent_seed)
            learner_seat = (index - 1) % 2
            agents = (
                (self.learner, opponent)
                if learner_seat == 0
                else (opponent, self.learner)
            )
            flags = (learner_seat == 0, learner_seat == 1)
            matchup = Matchup(
                index, self.learner_name, entry.name, learner_seat, flags, opponent_seed
            )
            for callback in self.callbacks:
                callback.on_matchup(matchup)
            for callback in self.callbacks:
                callback.on_episode_start(index)
            runner = Trainer(
                *agents,
                replace(
                    training_config, episodes=1, learning_seats=flags, seed=start_seed
                ),
                callbacks=self.callbacks,
            )
            episode = runner.run_episode(index)
            metrics = episode.metrics
            completed += 1
            total_steps += metrics.steps
            if metrics.winner is not None:
                wins[metrics.winner] += 1
                if metrics.winner == learner_seat:
                    learner_wins += 1
                else:
                    opponent_wins += 1
            elif metrics.truncated:
                truncations += 1
            else:
                draws += 1
            runner.update_agents(episode)
            for callback in self.callbacks:
                if callback.on_episode_end(episode) is False:
                    stopped = True

            final = index == config.episodes or stopped
            evaluate = (
                not stopped
                and config.tournament_every is not None
                and (index % config.tournament_every == 0 or final)
            )
            latest = None
            if index % config.checkpoint_every == 0 or final:
                latest = save_snapshot(index)
            if evaluate:
                if latest is None:
                    latest = save_snapshot(index, add_to_pool=False)
                participants = {
                    self.learner_name: partial(
                        self.checkpoints.load, latest.name, type(self.learner)
                    ),
                    **{
                        entry.name: partial(self._create_opponent, entry)
                        for entry in self.opponents.entries
                    },
                }
                tournaments.append(
                    run_tournament(
                        participants,
                        games_per_pair=config.tournament_games_per_pair,
                        max_steps=config.max_steps,
                        seed=evaluation_rng.randrange(2**32),
                        start=config.start,
                        training_episode=index,
                        callbacks=self.callbacks,
                    )
                )
            if stopped:
                break

        training = TrainingResult(
            completed,
            total_steps,
            (wins[0], wins[1]),
            draws,
            truncations,
            stopped,
            perf_counter() - started,
        )
        result = LeagueResult(
            training, learner_wins, opponent_wins, tuple(saved), tuple(tournaments)
        )
        for callback in self.callbacks:
            callback.on_training_end(training)
        for callback in self.callbacks:
            callback.on_league_end(result)
        return result
