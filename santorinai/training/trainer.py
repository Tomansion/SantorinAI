"""Episode collection and optional per-seat learning on the current engine."""

from collections.abc import Sequence
from random import Random
from time import perf_counter

from santorinai.agents import Agent
from santorinai.core import GameState
from santorinai.training.agents import TrainableAgent
from santorinai.training.callbacks import TrainingCallback
from santorinai.training.records import (
    BoardState,
    EpisodeMetrics,
    EpisodeResult,
    TrainingConfig,
    TrainingResult,
    Transition,
    UpdateResult,
)


class Trainer:
    """Run any two Agent implementations, including future human adapters.

    learning_seats independently enables updates for each seat. Disabling learn
    overrides both flags. Action selection always receives a private state copy.
    """

    def __init__(
        self,
        player1: Agent,
        player2: Agent,
        config: TrainingConfig | None = None,
        callbacks: Sequence[TrainingCallback] = (),
    ):
        for player in (player1, player2):
            if not callable(getattr(player, "select_action", None)):
                raise TypeError("Both agents must implement select_action(state)")
        self.players = (player1, player2)
        self.config = config if config is not None else TrainingConfig()
        self.callbacks = tuple(callbacks)
        self.rng = Random(self.config.seed)
        if (
            player1 is player2
            and self.config.learn
            and all(self.config.learning_seats)
            and isinstance(player1, TrainableAgent)
        ):
            raise ValueError("A shared learner must not be updated independently twice")

    def run(self) -> TrainingResult:
        started = perf_counter()
        wins = [0, 0]
        total_steps = draws = truncated_episodes = completed = 0
        stopped_early = False
        for callback in self.callbacks:
            callback.on_training_start(self.config)

        for index in range(1, self.config.episodes + 1):
            for callback in self.callbacks:
                callback.on_episode_start(index)
            episode = self.run_episode(index)
            metrics = episode.metrics
            completed += 1
            total_steps += metrics.steps
            if metrics.winner is not None:
                wins[metrics.winner] += 1
            elif metrics.truncated:
                truncated_episodes += 1
            else:
                draws += 1

            self.update_agents(episode)
            for callback in self.callbacks:
                if callback.on_episode_end(episode) is False:
                    stopped_early = True
            if stopped_early:
                break

        result = TrainingResult(
            completed,
            total_steps,
            (wins[0], wins[1]),
            draws,
            truncated_episodes,
            stopped_early,
            perf_counter() - started,
        )
        for callback in self.callbacks:
            callback.on_training_end(result)
        return result

    def update_agents(self, episode: EpisodeResult) -> None:
        """Apply enabled seat updates and emit update callbacks."""
        if self.config.learn:
            for seat, player in enumerate(self.players):
                if self.config.learning_seats[seat] and isinstance(
                    player, TrainableAgent
                ):
                    update = UpdateResult(
                        episode.metrics.episode,
                        seat,
                        dict(player.update(episode, seat)),
                    )
                    for callback in self.callbacks:
                        callback.on_update(update)

    def run_episode(self, index: int = 1) -> EpisodeResult:
        """Collect one episode and emit step hooks, without updating any agent.

        Trainer.run() and the league manager own the other lifecycle hooks.
        """
        started = perf_counter()
        state = GameState.new_game(self.config.start, self.rng)
        transitions: list[Transition] = []
        for step in range(1, self.config.max_steps + 1):
            seat = state.to_play
            before = BoardState.from_state(state)
            phase = "placement" if state.in_placement else "move"
            observation = state.clone()
            # GameState.clone() shares its cached legal-action list. Keep a
            # player's accidental list mutation from changing the live state.
            observation._legal = state.legal_actions().copy()
            action = self.players[seat].select_action(observation)
            valid = type(action) is int and action in state.legal_actions()
            if valid:
                climbed = state.is_winning_action(action)
                state.step(action, validate=False)
                reason = (
                    ("climbed" if climbed else "opponent_stuck")
                    if state.is_terminal
                    else "action_played"
                )
            else:
                state.winner = 1 - seat
                state._legal = []
                reason = f"invalid_action_by_player_{seat}"

            terminated = state.is_terminal
            truncated = not terminated and step == self.config.max_steps
            if truncated:
                reason = "max_steps"
            rewards = (state.reward(0), state.reward(1))
            transition = Transition(
                index,
                step,
                seat,
                phase,
                before,
                action,
                BoardState.from_state(state),
                rewards,
                terminated,
                truncated,
                valid,
                reason,
            )
            transitions.append(transition)
            for callback in self.callbacks:
                callback.on_step(transition)
            if terminated or truncated:
                break

        return EpisodeResult(
            EpisodeMetrics(
                index,
                len(transitions),
                state.winner,
                rewards,
                terminated,
                truncated,
                reason,
                perf_counter() - started,
            ),
            tuple(transitions),
        )
