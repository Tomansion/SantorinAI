"""League integration, checkpoint isolation and tournament accounting."""

import json
import tempfile
import unittest
from pathlib import Path
from random import Random
from unittest.mock import patch

from santorinai.agents import FirstChoiceAgent, RandomAgent
from santorinai.core import GameState, StartMode
from santorinai.training import (
    CheckpointManager,
    DummyAgent,
    HistoryCallback,
    JSONLLogger,
    LeagueConfig,
    LeagueTrainer,
    OpponentPool,
    TrainingCallback,
    run_tournament,
)
from test.test_training import IllegalAgent, Recorder, StopAfterEpisode


class TestCheckpoints(unittest.TestCase):
    def test_restore_rng_counters_and_independent_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = CheckpointManager(directory)
            agent = DummyAgent(7)
            agent.updates = 12
            agent.select_action(GameState.new_game())
            info = manager.save(agent, episode=12)
            restored = manager.load(info.name, DummyAgent)
            self.assertEqual(restored.updates, 12)
            self.assertEqual(agent.rng.getstate(), restored.rng.getstate())
            self.assertIsNot(restored, agent)
            state = GameState.new_game()
            self.assertEqual(
                [agent.select_action(state) for _ in range(10)],
                [restored.select_action(state) for _ in range(10)],
            )
            restored.updates += 1
            self.assertEqual(manager.load(info.name, DummyAgent).updates, 12)
            reseeded = manager.load(info.name, DummyAgent, seed=9)
            self.assertEqual(reseeded.rng.getstate(), Random(9).getstate())
            self.assertEqual(reseeded.updates, 12)
            # A fresh manager can discover and reload saved checkpoints.
            self.assertEqual(CheckpointManager(directory).list_checkpoints(), (info,))

    def test_no_overwrites_path_traversal_or_wrong_agent_types(self):
        class OtherDummy(DummyAgent):
            pass

        with tempfile.TemporaryDirectory() as directory:
            manager = CheckpointManager(directory)
            info = manager.save(OtherDummy(1), 0, name="initial")
            with self.assertRaises(FileExistsError):
                manager.save(DummyAgent(), 1, name="initial")
            with self.assertRaises(ValueError):
                manager.save(DummyAgent(), 1, name="../outside")
            with self.assertRaises(ValueError):
                manager.load(info.name, DummyAgent)

    def test_failed_save_is_not_published(self):
        class BrokenSave(DummyAgent):
            def save_checkpoint(self, path):
                raise RuntimeError("save failed")

        with tempfile.TemporaryDirectory() as directory:
            manager = CheckpointManager(directory)
            with self.assertRaisesRegex(RuntimeError, "save failed"):
                manager.save(BrokenSave(), 0)
            self.assertEqual(manager.list_checkpoints(), ())
            info = manager.save(DummyAgent(), 0)
            self.assertEqual(manager.list_checkpoints(), (info,))


class TestOpponentPool(unittest.TestCase):
    def test_weighted_sampling_is_seeded_and_weights_can_change(self):
        pool = OpponentPool()
        pool.add("rare", lambda seed: RandomAgent(seed))
        pool.add("frequent", lambda seed: DummyAgent(seed), weight=9)
        selections = []
        for _ in range(2):
            rng = Random(42)
            selections.append([pool.sample(rng).name for _ in range(500)])
        self.assertEqual(selections[0], selections[1])
        self.assertGreater(selections[0].count("frequent"), 400)
        pool.set_weight("rare", 1000)
        rng = Random(42)
        self.assertGreater(sum(pool.sample(rng).name == "rare" for _ in range(100)), 90)

    def test_checkpoint_factories_reload_independent_opponents(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = CheckpointManager(directory)
            agent = DummyAgent(1)
            info = manager.save(agent, 0)
            pool = OpponentPool()
            entry = pool.add_checkpoint(manager, info, DummyAgent)
            first, second = entry.create(11), entry.create(22)
            self.assertIsNot(first, second)
            assert isinstance(first, DummyAgent)
            first.updates = 100
            self.assertEqual(manager.load(info.name, DummyAgent).updates, 0)
            self.assertEqual(agent.updates, 0)

    def test_pool_configuration_errors(self):
        pool = OpponentPool()
        self.assertRaises(ValueError, pool.sample, Random(0))
        for weight in (0, -1, float("inf"), float("nan")):
            self.assertRaises(ValueError, pool.add, "bad", RandomAgent, weight)
        pool.add("random", RandomAgent)
        self.assertRaises(ValueError, pool.add, "random", RandomAgent)


class TournamentRecorder(TrainingCallback):
    def __init__(self):
        self.events = []
        self.games = []

    def on_tournament_start(self, config):
        self.events.append("start")

    def on_tournament_game(self, game):
        self.events.append("game")
        self.games.append(game)

    def on_tournament_match(self, match):
        self.events.append("match")

    def on_tournament_end(self, result):
        self.events.append("end")

    def on_update(self, update):
        raise AssertionError("Tournament must never update an agent")


class TestTournament(unittest.TestCase):
    def test_round_robin_rotates_seats_and_attributes_wins_to_names(self):
        callback = TournamentRecorder()
        result = run_tournament(
            {
                "a": lambda seed: FirstChoiceAgent(),
                "b": lambda seed: FirstChoiceAgent(),
                "illegal": lambda seed: IllegalAgent(),
            },
            games_per_pair=2,
            training_episode=17,
            callbacks=[callback],
        )
        self.assertEqual(
            callback.events, ["start"] + ["game", "game", "match"] * 3 + ["end"]
        )
        self.assertEqual(result.training_episode, 17)
        self.assertEqual(len(result.matches), 3)
        self.assertEqual(len(callback.games), 6)
        for index in range(0, 6, 2):
            self.assertEqual(
                callback.games[index].participants,
                tuple(reversed(callback.games[index + 1].participants)),
            )
        self.assertEqual(result.win_rates["a"]["illegal"], 1)
        self.assertEqual(result.win_rates["illegal"]["a"], 0)
        self.assertTrue(all(match.games == 2 for match in result.matches))

    def test_tournament_never_updates_and_paired_games_reuse_factory_seeds(self):
        class EvaluationOnlyDummy(DummyAgent):
            def update(self, episode, player):
                raise AssertionError("An evaluation agent was updated")

        seeds = {"a": [], "b": []}

        def create(name, seed):
            seeds[name].append(seed)
            return EvaluationOnlyDummy(seed)

        result = run_tournament(
            {"a": lambda seed: create("a", seed), "b": lambda seed: create("b", seed)},
            games_per_pair=4,
            start=StartMode.random,
        )
        self.assertEqual(result.matches[0].games, 4)
        for values in seeds.values():
            self.assertEqual(values[0], values[1])
            self.assertEqual(values[2], values[3])

    def test_truncations_are_not_reported_as_losses_or_draws(self):
        result = run_tournament(
            {"a": RandomAgent, "b": DummyAgent}, games_per_pair=2, max_steps=1
        )
        self.assertEqual(result.matches[0].truncations, 2)
        self.assertEqual(result.matches[0].draws, 0)
        self.assertEqual(result.win_rates, {"a": {"b": 0}, "b": {"a": 0}})

    def test_tournament_requires_a_balanced_schedule(self):
        self.assertRaises(ValueError, run_tournament, {"a": RandomAgent})
        self.assertRaises(
            ValueError,
            run_tournament,
            {"a": RandomAgent, "b": DummyAgent},
            games_per_pair=3,
        )


class TestLeague(unittest.TestCase):
    def test_sampling_rotation_one_update_per_episode_and_checkpoint_retention(self):
        class FrozenDummy(DummyAgent):
            def update(self, episode, player):
                raise AssertionError("Frozen opponent was updated")

        with tempfile.TemporaryDirectory() as directory:
            learner = DummyAgent(3)
            pool = OpponentPool()
            pool.add("baseline", lambda seed: RandomAgent(seed))
            pool.add("frozen", lambda seed: FrozenDummy(seed))
            history = HistoryCallback()
            manager = CheckpointManager(Path(directory) / "checkpoints")
            logger = JSONLLogger(Path(directory) / "metrics.jsonl")
            result = LeagueTrainer(
                learner,
                pool,
                manager,
                LeagueConfig(
                    episodes=6,
                    checkpoint_every=2,
                    max_historical_opponents=2,
                    tournament_every=3,
                    tournament_games_per_pair=2,
                ),
                [history, logger],
            ).run()
            self.assertEqual(learner.updates, 6)
            self.assertEqual([m.learner_seat for m in history.matchups], [0, 1] * 3)
            self.assertEqual([u.player for u in history.updates], [0, 1] * 3)
            self.assertEqual(
                [m.learning_seats for m in history.matchups],
                [(True, False), (False, True)] * 3,
            )
            self.assertGreater(len({m.opponent for m in history.matchups}), 1)
            self.assertEqual([c.episode for c in result.checkpoints], [0, 2, 3, 4, 6])
            self.assertEqual([t.training_episode for t in result.tournaments], [3, 6])
            self.assertEqual(
                len([e for e in pool.entries if e.checkpoint is not None]), 2
            )
            self.assertTrue(
                {"baseline", "frozen"}.issubset(e.name for e in pool.entries)
            )
            self.assertEqual(len(manager.list_checkpoints()), 5)
            self.assertEqual(result.learner_wins + result.opponent_wins, 6)
            self.assertEqual(history.league_result, result)
            records = [
                json.loads(line) for line in logger.path.read_text().splitlines()
            ]
        events = [r["event"] for r in records]
        self.assertEqual(
            events[:3], ["training_start", "league_start", "checkpoint_saved"]
        )
        self.assertEqual(events[-2:], ["training_end", "league_end"])
        self.assertEqual(events.count("update"), 6)
        self.assertEqual(events.count("matchup"), 6)
        self.assertEqual(events.count("tournament_start"), 2)
        self.assertIn("tournament_game", events)
        self.assertIn("tournament_match", events)

    def test_learner_wins_are_independent_of_seat(self):
        with tempfile.TemporaryDirectory() as directory:
            pool = OpponentPool()
            entry = pool.add("illegal", lambda seed: IllegalAgent())
            with patch.object(pool, "sample", return_value=entry):
                result = LeagueTrainer(
                    DummyAgent(),
                    pool,
                    CheckpointManager(directory),
                    LeagueConfig(episodes=4, tournament_every=None),
                ).run()
        self.assertEqual(result.learner_wins, 4)
        self.assertEqual(result.opponent_wins, 0)
        self.assertEqual(result.training.wins, (2, 2))

    def test_evaluation_does_not_change_training_matchups_rng_or_experience(self):
        experiences, matchups, rng_states = [], [], []
        for tournament_every in (None, 1):
            with tempfile.TemporaryDirectory() as directory:
                learner = DummyAgent(42)
                pool = OpponentPool()
                pool.add("random", RandomAgent)
                recorder, history = Recorder(), HistoryCallback()
                LeagueTrainer(
                    learner,
                    pool,
                    CheckpointManager(directory),
                    LeagueConfig(
                        episodes=4,
                        seed=7,
                        checkpoint_every=2,
                        tournament_every=tournament_every,
                        tournament_games_per_pair=2,
                    ),
                    [recorder, history],
                ).run()
                experiences.append([e.transitions for e in recorder.episodes])
                matchups.append(history.matchups)
                rng_states.append(learner.rng.getstate())
        self.assertEqual(experiences[0], experiences[1])
        self.assertEqual(matchups[0], matchups[1])
        self.assertEqual(rng_states[0], rng_states[1])

    def test_empty_pool_starts_with_self_play_and_early_stop_saves_final_state(self):
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryCallback()
            manager = CheckpointManager(directory)
            learner = DummyAgent(0)
            result = LeagueTrainer(
                learner,
                OpponentPool(),
                manager,
                LeagueConfig(episodes=10, tournament_every=1),
                [StopAfterEpisode(), history],
            ).run()
            self.assertEqual(result.training.episodes_completed, 1)
            self.assertTrue(result.training.stopped_early)
            self.assertEqual([c.episode for c in result.checkpoints], [0, 1])
            self.assertEqual(result.tournaments, ())
            self.assertEqual(
                manager.load(result.checkpoints[-1].name, DummyAgent).updates, 1
            )
            self.assertEqual(history.result, result.training)

    def test_reloaded_learner_continues_without_overwriting_checkpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = CheckpointManager(directory)
            old = DummyAgent(9)
            old.updates = 7
            initial = manager.save(old, 7)
            artifact = Path(initial.path) / "agent"
            before = artifact.read_bytes()
            learner = manager.load(initial.name, DummyAgent)
            result = LeagueTrainer(
                learner,
                OpponentPool(),
                manager,
                LeagueConfig(episodes=2, tournament_every=None),
            ).run()
            self.assertEqual(learner.updates, 9)
            self.assertEqual(artifact.read_bytes(), before)
            self.assertEqual(len(manager.list_checkpoints()), 3)
            self.assertNotIn(initial, result.checkpoints)

    def test_live_learner_cannot_be_used_as_its_own_opponent(self):
        with tempfile.TemporaryDirectory() as directory:
            learner = DummyAgent()
            pool = OpponentPool()
            entry = pool.add("bad", lambda seed: learner)
            with (
                patch.object(pool, "sample", return_value=entry),
                self.assertRaisesRegex(ValueError, "live learner"),
            ):
                LeagueTrainer(
                    learner,
                    pool,
                    CheckpointManager(directory),
                    LeagueConfig(episodes=1),
                ).run()
            self.assertEqual(learner.updates, 0)

    def test_configuration_rejects_invalid_intervals_and_unbalanced_tournaments(self):
        for field in (
            "episodes",
            "max_steps",
            "checkpoint_every",
            "max_historical_opponents",
            "tournament_every",
        ):
            self.assertRaises(ValueError, LeagueConfig, **{field: 0})
        self.assertRaises(ValueError, LeagueConfig, tournament_games_per_pair=3)
