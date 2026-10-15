"""Publish and reload algorithm-owned checkpoints with JSON manifests."""

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from santorinai.training.agents import CheckpointableAgent
from santorinai.training.records import CheckpointInfo


class CheckpointManager:
    """Checkpoints are immutable directories; existing names are never overwritten.

    Only directories with a completed manifest are listed. Artifacts are loaded
    by an explicitly supplied agent class, never by importing manifest content.
    """

    def __init__(self, directory: str | Path):
        self.directory = Path(directory).resolve()

    @staticmethod
    def _validate_name(name: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError("Checkpoint names must be simple file names")

    def save(
        self,
        agent: CheckpointableAgent,
        episode: int,
        name: str | None = None,
        *,
        purpose: Literal["training", "evaluation"] = "training",
    ) -> CheckpointInfo:
        self.directory.mkdir(parents=True, exist_ok=True)
        if name is None:
            prefix = "checkpoint" if purpose == "training" else "evaluation"
            index = 1
            while (self.directory / f"{prefix}-{index:06d}").exists():
                index += 1
            name = f"{prefix}-{index:06d}"
        self._validate_name(name)
        target = self.directory / name
        target.mkdir()  # Exclusive reservation, including incomplete checkpoints.
        agent.save_checkpoint(target / "agent")
        info = CheckpointInfo(
            name, episode, self._agent_type(type(agent)), str(target), purpose
        )
        temporary = target / ".manifest.tmp"
        temporary.write_text(
            json.dumps({"version": 1, **asdict(info)}), encoding="utf-8"
        )
        temporary.replace(target / "manifest.json")
        return info

    @staticmethod
    def _agent_type(agent_type: type[CheckpointableAgent]) -> str:
        return f"{agent_type.__module__}.{agent_type.__qualname__}"

    def get(self, name: str) -> CheckpointInfo:
        self._validate_name(name)
        target = self.directory / name
        data = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        if data["version"] != 1 or data["name"] != name:
            raise ValueError("Invalid checkpoint manifest")
        return CheckpointInfo(
            name,
            data["episode"],
            data["agent_type"],
            str(target),
            data.get("purpose", "training"),
        )

    def list_checkpoints(self) -> tuple[CheckpointInfo, ...]:
        return tuple(
            self.get(path.parent.name)
            for path in sorted(self.directory.glob("*/manifest.json"))
        )

    def load[T: CheckpointableAgent](
        self, name: str, agent_type: type[T], seed: int | None = None
    ) -> T:
        info = self.get(name)
        if info.agent_type != self._agent_type(agent_type):
            raise ValueError("Checkpoint was saved by a different agent type")
        return agent_type.load_checkpoint(Path(info.path) / "agent", seed)
