"""Demonstrate opponent sampling, frozen snapshots and tournament callbacks.

Run: uv run python -m examples.train_dummy_league --episodes 12
"""

import argparse
from pathlib import Path

from santorinai.agents import FirstChoiceAgent, RandomAgent
from santorinai.training import (
    CheckpointManager,
    DummyAgent,
    HistoryCallback,
    JSONLLogger,
    LeagueConfig,
    LeagueTrainer,
    OpponentPool,
    TrainingCallback,
)


class Progress(TrainingCallback):
    def on_matchup(self, matchup):
        print(
            f"Episode {matchup.episode}: learner in seat {matchup.learner_seat} "
            f"against {matchup.opponent}"
        )

    def on_checkpoint_saved(self, checkpoint):
        print(f"Saved {checkpoint.name} after episode {checkpoint.episode}")

    def on_tournament_end(self, result):
        print(f"Tournament after episode {result.training_episode}:")
        for opponent, rate in result.win_rates["learner"].items():
            print(f"  learner vs {opponent}: {rate:.0%} wins")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("runs/dummy-league"))
    parser.add_argument("--resume", help="Checkpoint name to restore the dummy learner")
    args = parser.parse_args()

    pool = OpponentPool()
    pool.add("random", lambda seed: RandomAgent(seed))
    pool.add("first-choice", lambda seed: FirstChoiceAgent())
    checkpoints = CheckpointManager(args.output / "checkpoints")
    learner = (
        checkpoints.load(args.resume, DummyAgent)
        if args.resume
        else DummyAgent(seed=args.seed)
    )
    history = HistoryCallback()
    result = LeagueTrainer(
        learner,
        pool,
        checkpoints,
        config=LeagueConfig(
            episodes=args.episodes,
            seed=args.seed,
            checkpoint_every=4,
            max_historical_opponents=3,
            tournament_every=6,
            tournament_games_per_pair=2,
        ),
        callbacks=[history, JSONLLogger(args.output / "metrics.jsonl"), Progress()],
    ).run()
    print(
        f"Learner wins: {result.learner_wins}; opponent wins: {result.opponent_wins}; "
        f"updates: {learner.updates}"
    )
    print(f"Checkpoints and metrics: {args.output}")


if __name__ == "__main__":
    main()
