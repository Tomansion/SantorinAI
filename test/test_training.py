"""Training contracts on the current integer-action engine."""

import json
import tempfile
import unittest
from itertools import pairwise
from pathlib import Path
from unittest.mock import patch

from santorinai.agents import FirstChoiceAgent, RandomAgent
from santorinai.core import GameState, StartMode
from santorinai.training import (
    BoardState,
    DummyAgent,
    HistoryCallback,
    JSONLLogger,
    Trainer,
    TrainingCallback,
    TrainingConfig,
)


class Recorder(TrainingCallback):
    def __init__(self):
        self.events = []
        self.episodes = []

    def on_training_start(self, config):
        self.events.append("start")

    def on_episode_start(self, episode):
        self.events.append("episode_start")

    def on_step(self, transition):
        self.events.append("step")

    def on_update(self, update):
        self.events.append(f"update_{update.player}")

    def on_episode_end(self, episode):
        self.events.append("episode_end")
        self.episodes.append(episode)

    def on_training_end(self, result):
        self.events.append("end")


class IllegalAgent:
    def select_action(self, state):
        return -1


class StopAfterEpisode(TrainingCallback):
    def on_episode_end(self, episode):
        return False


class TestTraining(unittest.TestCase):
    def test_episode_lifecycle_terminal_rewards_and_snapshots(self):
        recorder = Recorder()
        agents = DummyAgent(seed=12), DummyAgent(seed=34)
        result = Trainer(*agents, TrainingConfig(episodes=1), [recorder]).run()
        episode = recorder.episodes[0]
        steps = episode.transitions
        self.assertEqual(
            recorder.events,
            ["start", "episode_start"]
            + ["step"] * len(steps)
            + ["update_0", "update_1", "episode_end", "end"],
        )
        self.assertEqual([a.updates for a in agents], [1, 1])
        self.assertEqual([t.phase for t in steps[:4]], ["placement"] * 4)
        self.assertEqual([t.player for t in steps[:4]], [0, 1, 0, 1])
        self.assertTrue(all(t.phase == "move" for t in steps[4:]))
        self.assertTrue(all(t.valid for t in steps))
        self.assertTrue(all(t.rewards == (0, 0) for t in steps[:-1]))
        self.assertTrue(steps[-1].terminated)
        self.assertFalse(steps[-1].truncated)
        winner = episode.metrics.winner
        assert winner is not None
        self.assertEqual(episode.metrics.rewards[winner], 1)
        self.assertEqual(episode.metrics.rewards[1 - winner], -1)
        self.assertEqual(result.wins[winner], 1)
        self.assertEqual(result.total_steps, len(steps))
        for current, following in pairwise(steps):
            self.assertEqual(current.next_state, following.state)
        final = steps[-1].next_state.to_state()
        self.assertEqual(final.winner, winner)
        self.assertEqual(final.legal_actions(), [])
        self.assertEqual(BoardState.from_state(final), steps[-1].next_state)

    def test_per_seat_learning_and_global_evaluation_switch(self):
        for flags in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(flags=flags):
                agents = DummyAgent(1), DummyAgent(2)
                history = HistoryCallback()
                Trainer(
                    *agents,
                    TrainingConfig(episodes=2, max_steps=5, learning_seats=flags),
                    [history],
                ).run()
                self.assertEqual(
                    [a.updates for a in agents], [int(f) * 2 for f in flags]
                )
                self.assertEqual(
                    [u.player for u in history.updates],
                    [seat for _ in range(2) for seat in (0, 1) if flags[seat]],
                )
        agents = DummyAgent(1), DummyAgent(2)
        Trainer(*agents, TrainingConfig(episodes=1, learn=False)).run()
        self.assertEqual([a.updates for a in agents], [0, 0])

    def test_invalid_actions_lose_for_either_seat_in_either_phase(self):
        class IllegalMove(IllegalAgent):
            def select_action(self, state):
                return state.legal_actions()[0] if state.in_placement else -1

        for bad_type in (IllegalAgent, IllegalMove):
            for seat in (0, 1):
                with self.subTest(agent=bad_type, seat=seat):
                    players = [FirstChoiceAgent(), FirstChoiceAgent()]
                    players[seat] = bad_type()
                    recorder = Recorder()
                    result = Trainer(
                        players[0], players[1], TrainingConfig(episodes=1), [recorder]
                    ).run()
                    episode = recorder.episodes[0]
                    self.assertEqual(result.wins[1 - seat], 1)
                    self.assertEqual(sum(result.wins), 1)
                    self.assertFalse(episode.transitions[-1].valid)
                    self.assertEqual(episode.metrics.rewards[seat], -1)
                    expected = seat + 1 + (4 if bad_type is IllegalMove else 0)
                    self.assertEqual(result.total_steps, expected)

    def test_non_integer_actions_are_forfeits(self):
        agent = DummyAgent()
        for action in (None, True, 1.0, [1]):
            with self.subTest(action=action):
                with patch.object(agent, "select_action", return_value=action):
                    result = Trainer(
                        agent, RandomAgent(0), TrainingConfig(episodes=1)
                    ).run()
                self.assertEqual(result.wins, (0, 1))

    def test_winning_move_and_terminal_observation(self):
        heights = [0] * 25
        heights[0], heights[1] = 2, 3
        state = GameState(workers=[0, 24, 12, 14], heights=heights)
        action = next(a for a in state.legal_actions() if state.is_winning_action(a))
        agent = DummyAgent()
        recorder = Recorder()
        with (
            patch.object(GameState, "new_game", return_value=state),
            patch.object(agent, "select_action", return_value=action),
        ):
            result = Trainer(
                agent, DummyAgent(), TrainingConfig(episodes=1), [recorder]
            ).run()
        self.assertEqual(result.wins, (1, 0))
        self.assertEqual(result.total_steps, 1)
        final = recorder.episodes[0].transitions[-1]
        self.assertEqual(final.next_state.workers[0], 1)
        self.assertEqual(final.next_state.heights[0], 2)
        self.assertEqual(final.rewards, (1, -1))

    def test_step_limit_is_truncation_and_does_not_count_as_a_draw(self):
        for limit in (1, 4, 5):
            with self.subTest(limit=limit):
                recorder = Recorder()
                result = Trainer(
                    DummyAgent(),
                    DummyAgent(),
                    TrainingConfig(episodes=2, max_steps=limit),
                    [recorder],
                ).run()
                self.assertEqual(result.truncated_episodes, 2)
                self.assertEqual(result.draws, 0)
                self.assertEqual(result.wins, (0, 0))
                for episode in recorder.episodes:
                    self.assertEqual(episode.metrics.steps, limit)
                    self.assertEqual(episode.metrics.rewards, (0, 0))
                    self.assertFalse(episode.metrics.terminated)
                    self.assertTrue(episode.transitions[-1].truncated)

    def test_seeded_experience_is_reproducible(self):
        runs = []
        for _ in range(2):
            recorder = Recorder()
            Trainer(
                DummyAgent(11),
                DummyAgent(22),
                TrainingConfig(episodes=3, start=StartMode.random, seed=33),
                [recorder],
            ).run()
            runs.append([e.transitions for e in recorder.episodes])
        self.assertEqual(runs[0], runs[1])

    def test_ordinary_and_trainable_agents_mix_in_either_seat(self):
        for first in (DummyAgent, RandomAgent):
            for second in (DummyAgent, RandomAgent):
                with self.subTest(first=first, second=second):
                    history = HistoryCallback()
                    result = Trainer(
                        first(1), second(2), TrainingConfig(episodes=1), [history]
                    ).run()
                    self.assertEqual(result.episodes_completed, 1)
                    self.assertEqual(
                        len(history.updates),
                        (first is DummyAgent) + (second is DummyAgent),
                    )

    def test_early_stop_notifies_remaining_callbacks(self):
        history = HistoryCallback()
        result = Trainer(
            DummyAgent(),
            DummyAgent(),
            TrainingConfig(episodes=10),
            [StopAfterEpisode(), history],
        ).run()
        self.assertTrue(result.stopped_early)
        self.assertEqual(result.episodes_completed, 1)
        self.assertEqual(len(history.episodes), 1)
        self.assertEqual(history.result, result)

    def test_jsonl_append_and_history_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "metrics.jsonl"
            history = HistoryCallback()
            trainer = Trainer(
                DummyAgent(),
                DummyAgent(),
                TrainingConfig(episodes=2),
                [history, JSONLLogger(path)],
            )
            for _ in range(2):
                result = trainer.run()
                self.assertEqual(len(history.episodes), 2)
                self.assertEqual(len(history.updates), 4)
                self.assertEqual(history.result, result)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(
            [r["event"] for r in records],
            (
                ["training_start"]
                + ["update", "update", "episode_end"] * 2
                + ["training_end"]
            )
            * 2,
        )
        self.assertNotIn("transitions", records[3])
        self.assertIn("episode_reward", records[1]["metrics"])

    def test_player_cannot_mutate_live_state_or_legal_action_cache(self):
        class MutatingAgent:
            def select_action(self, state):
                action = state.legal_actions()[0]
                state.heights[0] = 4
                state.workers[:] = [-1] * 4
                state.legal_actions().clear()
                state.to_play = 1
                return action

        recorder = Recorder()
        Trainer(
            MutatingAgent(),
            MutatingAgent(),
            TrainingConfig(episodes=1, max_steps=4),
            [recorder],
        ).run()
        episode = recorder.episodes[0]
        self.assertTrue(all(t.valid for t in episode.transitions))
        self.assertEqual(episode.transitions[-1].next_state.heights, (0,) * 25)
        self.assertEqual(len(set(episode.transitions[-1].next_state.workers)), 4)

    def test_snapshot_roundtrip_is_independent(self):
        state = GameState.new_game()
        state.step(state.legal_actions()[0])
        snapshot = BoardState.from_state(state)
        restored = snapshot.to_state()
        self.assertEqual(restored.to_play, 1)
        self.assertEqual(BoardState.from_state(restored), snapshot)
        restored.heights[0] = 4
        restored.workers[0] = 20
        self.assertEqual(snapshot.heights[0], 0)
        self.assertEqual(snapshot.workers[0], 0)

    def test_bad_configuration_and_shared_learner_fail_early(self):
        for value in (0, -1, 1.5, True):
            self.assertRaises(ValueError, TrainingConfig, episodes=value)
            self.assertRaises(ValueError, TrainingConfig, max_steps=value)
        self.assertRaises(ValueError, TrainingConfig, learning_seats=(True,))
        self.assertRaises(TypeError, Trainer, None, DummyAgent())
        shared = DummyAgent()
        self.assertRaises(ValueError, Trainer, shared, shared)
        Trainer(
            shared,
            shared,
            TrainingConfig(episodes=1, learning_seats=(True, False)),
        ).run()
        self.assertEqual(shared.updates, 1)

    def test_callback_and_agent_errors_propagate(self):
        class BrokenCallback(TrainingCallback):
            def on_step(self, transition):
                raise RuntimeError("tracking failed")

        with self.assertRaisesRegex(RuntimeError, "tracking failed"):
            Trainer(
                DummyAgent(),
                DummyAgent(),
                TrainingConfig(episodes=1),
                [BrokenCallback()],
            ).run()
        with (
            patch.object(
                DummyAgent, "select_action", side_effect=RuntimeError("agent bug")
            ),
            self.assertRaisesRegex(RuntimeError, "agent bug"),
        ):
            Trainer(DummyAgent(), DummyAgent(), TrainingConfig(episodes=1)).run()
