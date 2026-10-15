"""Exercise the training contract; the dummy agents do not improve at the game.

Run from the project root: uv run python -m examples.train_dummy_agents
"""

import argparse
from pathlib import Path

from santorinai.training import (
    DummyAgent,
    HistoryCallback,
    JSONLLogger,
    Trainer,
    TrainingConfig,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log", type=Path, default=Path("runs/dummy-training.jsonl"))
    parser.add_argument("--evaluate", action="store_true", help="Disable update calls")
    args = parser.parse_args()
    history = HistoryCallback()
    trainer = Trainer(
        DummyAgent(seed=args.seed),
        DummyAgent(seed=args.seed + 1),
        TrainingConfig(episodes=args.episodes, learn=not args.evaluate, seed=args.seed),
        callbacks=[history, JSONLLogger(args.log)],
    )
    result = trainer.run()
    for episode in history.episodes:
        print(
            f"Episode {episode.episode}: winner={episode.winner}, "
            f"steps={episode.steps}, rewards={episode.rewards}, "
            f"truncated={episode.truncated}"
        )
    print(f"Wins by seat: {result.wins}; updates: {len(history.updates)}")
    print(f"Metrics appended to {args.log}")


if __name__ == "__main__":
    main()
