"""Learning and checkpoint contracts; only a legal random dummy is implemented."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from random import Random
from typing import Self

from santorinai.agents import Agent
from santorinai.core import GameState
from santorinai.training.records import EpisodeResult


class TrainableAgent(Agent, ABC):
    """Seat-independent policy; the runner supplies the learning seat explicitly."""

    @abstractmethod
    def update(self, episode: EpisodeResult, player: int) -> dict[str, float]:
        """Consume a complete episode and return scalar tracking metrics."""


class CheckpointableAgent(TrainableAgent):
    """Algorithms choose their own artifact format, without a pickle dependency."""

    @abstractmethod
    def save_checkpoint(self, path: Path) -> None:
        """Save model/optimizer/RNG state at path (a file or directory)."""

    @classmethod
    @abstractmethod
    def load_checkpoint(cls, path: Path, seed: int | None = None) -> Self:
        """Load an independent agent; seed optionally resets action-selection RNG."""


class DummyAgent(CheckpointableAgent):
    """Seeded random legal actions and an update counter, without learning."""

    def __init__(self, seed: int | None = None):
        self.rng = Random(seed)
        self.updates = 0

    def select_action(self, state: GameState) -> int:
        return self.rng.choice(state.legal_actions())

    def update(self, episode: EpisodeResult, player: int) -> dict[str, float]:
        self.updates += 1
        return {
            "updates": float(self.updates),
            "own_actions": float(sum(t.player == player for t in episode.transitions)),
            "episode_reward": episode.metrics.rewards[player],
        }

    def save_checkpoint(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {"version": 1, "updates": self.updates, "rng": self.rng.getstate()}
            ),
            encoding="utf-8",
        )

    @classmethod
    def load_checkpoint(cls, path: Path, seed: int | None = None) -> Self:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["version"] != 1:
            raise ValueError("Unsupported dummy checkpoint version")
        agent = cls(seed)
        agent.updates = data["updates"]
        if seed is None:
            version, internal, gaussian = data["rng"]
            agent.rng.setstate((version, tuple(internal), gaussian))
        return agent
