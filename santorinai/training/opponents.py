"""A weighted pool of independently constructed opponents."""

import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from random import Random

from santorinai.agents import Agent
from santorinai.training.agents import CheckpointableAgent
from santorinai.training.checkpoints import CheckpointManager
from santorinai.training.records import CheckpointInfo

type AgentFactory = Callable[[int], Agent]


@dataclass(frozen=True)
class Opponent:
    name: str
    factory: AgentFactory
    weight: float = 1.0
    checkpoint: CheckpointInfo | None = None

    def create(self, seed: int) -> Agent:
        agent = self.factory(seed)
        if not callable(getattr(agent, "select_action", None)):
            raise TypeError(f"Opponent factory {self.name!r} did not return an Agent")
        return agent


class OpponentPool:
    """Uniform sampling by default; positive weights allow custom mixtures.

    Factories must construct independent agents, not return a live learner.
    Checkpoint factories reload saved state for every game.
    """

    def __init__(self):
        self._entries: dict[str, Opponent] = {}

    @property
    def entries(self) -> tuple[Opponent, ...]:
        return tuple(self._entries.values())

    def add(
        self,
        name: str,
        factory: AgentFactory,
        weight: float = 1.0,
        checkpoint: CheckpointInfo | None = None,
    ) -> Opponent:
        if not name or name in self._entries:
            raise ValueError("Opponent names must be nonempty and unique")
        self._validate_weight(weight)
        if not callable(factory):
            raise TypeError("An opponent factory must be callable")
        opponent = Opponent(name, factory, weight, checkpoint)
        self._entries[name] = opponent
        return opponent

    def add_checkpoint(
        self,
        manager: CheckpointManager,
        info: CheckpointInfo,
        agent_type: type[CheckpointableAgent],
        *,
        name: str | None = None,
        weight: float = 1.0,
    ) -> Opponent:
        return self.add(
            name if name is not None else info.name,
            lambda seed: manager.load(info.name, agent_type, seed),
            weight,
            info,
        )

    @staticmethod
    def _validate_weight(weight: float) -> None:
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("Opponent weights must be finite and positive")

    def set_weight(self, name: str, weight: float) -> None:
        self._validate_weight(weight)
        self._entries[name] = replace(self._entries[name], weight=weight)

    def remove(self, name: str) -> None:
        del self._entries[name]

    def sample(self, rng: Random) -> Opponent:
        if not self._entries:
            raise ValueError("Cannot sample an empty opponent pool")
        entries = self.entries
        return rng.choices(entries, weights=[entry.weight for entry in entries], k=1)[0]
