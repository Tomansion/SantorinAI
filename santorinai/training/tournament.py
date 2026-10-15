"""Balanced round-robin evaluation with isolated agent instances and callbacks."""

from collections.abc import Mapping, Sequence
from itertools import combinations
from random import Random

from santorinai.core import StartMode
from santorinai.training.callbacks import TrainingCallback
from santorinai.training.opponents import AgentFactory
from santorinai.training.records import (
    TournamentConfig,
    TournamentGame,
    TournamentMatch,
    TournamentResult,
    TrainingConfig,
)
from santorinai.training.trainer import Trainer


def run_tournament(
    participants: Mapping[str, AgentFactory],
    *,
    games_per_pair: int = 4,
    max_steps: int = 512,
    seed: int = 42,
    start: StartMode = StartMode.placement,
    training_episode: int = 0,
    callbacks: Sequence[TrainingCallback] = (),
) -> TournamentResult:
    """No updates occur. Each seed is used for two games with reversed seats.

    Factories receive an action-selection seed and must return independent
    agents. Evaluation owns its RNG and never borrows a live learner.
    """
    config = TournamentConfig(
        tuple(participants), games_per_pair, max_steps, seed, start, training_episode
    )
    for callback in callbacks:
        callback.on_tournament_start(config)
    rng = Random(seed)
    matches: list[TournamentMatch] = []
    for a, b in combinations(participants, 2):
        wins_a = wins_b = draws = truncations = total_steps = 0
        for pair in range(games_per_pair // 2):
            seed_a, seed_b, start_seed = (rng.randrange(2**32) for _ in range(3))
            for a_seat in (0, 1):
                agent_a, agent_b = participants[a](seed_a), participants[b](seed_b)
                agents = (agent_a, agent_b) if a_seat == 0 else (agent_b, agent_a)
                names = (a, b) if a_seat == 0 else (b, a)
                game = Trainer(
                    *agents,
                    TrainingConfig(
                        episodes=1,
                        max_steps=max_steps,
                        learn=False,
                        start=start,
                        seed=start_seed,
                    ),
                ).run_episode()
                metrics = game.metrics
                total_steps += metrics.steps
                if metrics.winner is not None:
                    if metrics.winner == a_seat:
                        wins_a += 1
                    else:
                        wins_b += 1
                elif metrics.truncated:
                    truncations += 1
                else:
                    draws += 1
                event = TournamentGame(
                    training_episode, names, pair * 2 + a_seat + 1, metrics
                )
                for callback in callbacks:
                    callback.on_tournament_game(event)
        match = TournamentMatch(a, b, wins_a, wins_b, draws, truncations, total_steps)
        matches.append(match)
        for callback in callbacks:
            callback.on_tournament_match(match)
    result = TournamentResult(training_episode, tuple(matches))
    for callback in callbacks:
        callback.on_tournament_end(result)
    return result
