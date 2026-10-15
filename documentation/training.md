# Training, opponent leagues and evaluation

The training package uses the current `GameState` engine and the same
`Agent.select_action(state) -> int` interface as the baseline agents.
Seats are **0 and 1**, matching `GameState.to_play`. Any future human
adapter can implement that same action interface.

Only `DummyAgent` is implemented here. It picks legal actions randomly and
increments a counter during updates; it does not learn. There is no PPO,
MCTS, AlphaZero network, or GAN implementation.

## Try the examples

```bash
uv run python -m examples.train_dummy_agents --episodes 10 --seed 42
uv run python -m examples.train_dummy_agents --episodes 10 --evaluate
uv run python -m examples.train_dummy_league --episodes 12 --seed 42
```

The league demo includes random and first-choice baselines, automatically
adds saved copies of the dummy learner, alternates the learner's seat, and
runs round-robin tournaments. Output goes to `runs/dummy-league/`:
`metrics.jsonl` and a `checkpoints/` directory. Choose another directory
with `--output`.

## A fixed pair and per-seat learning

```python
from santorinai.training import DummyAgent, HistoryCallback, Trainer, TrainingConfig

history = HistoryCallback()
result = Trainer(
    DummyAgent(seed=1),
    DummyAgent(seed=2),
    config=TrainingConfig(
        episodes=100,
        learning_seats=(True, False),
    ),
    callbacks=[history],
).run()
```

Here seat 0 learns and seat 1 only chooses actions. Either seat can instead
hold an ordinary agent such as `RandomAgent`, `GreedyAgent` or
`MinimaxAgent`; these never receive updates. `learn=False` disables all
learning regardless of the seat flags.

A `TrainableAgent` implements
`update(episode: EpisodeResult, player: int) -> dict[str, float]`.
The explicit seat argument lets the same learner play either side.
Passing one shared trainable object into both learning seats is rejected
to prevent duplicate updates. A shared neural model with two player
wrappers will likewise need one central learning process; the league
already uses one live learner and frozen opponents.

## Train against a league

```python
from santorinai.agents import FirstChoiceAgent, RandomAgent
from santorinai.training import (
    CheckpointManager,
    DummyAgent,
    HistoryCallback,
    JSONLLogger,
    LeagueConfig,
    LeagueTrainer,
    OpponentPool,
)

pool = OpponentPool()
pool.add("random", lambda seed: RandomAgent(seed), weight=1)
pool.add("first-choice", lambda seed: FirstChoiceAgent(), weight=1)

history = HistoryCallback()
result = LeagueTrainer(
    learner=DummyAgent(seed=42),
    opponents=pool,
    checkpoints=CheckpointManager("runs/experiment/checkpoints"),
    config=LeagueConfig(
        episodes=100,
        seed=42,
        checkpoint_every=10,
        max_historical_opponents=5,
        tournament_every=25,
        tournament_games_per_pair=4,
    ),
    callbacks=[history, JSONLLogger("runs/experiment/metrics.jsonl")],
).run()

print(result.learner_wins, result.opponent_wins)
print(result.tournaments[-1].win_rates)
```

For each episode the manager samples an opponent and constructs an independent
instance from its factory. It alternates the learner between seats 0 and 1,
and enables updates only for that seat, even when the opponent is itself a
`TrainableAgent`. Returning the live learner from an opponent factory is
rejected.

Sampling is uniform over entries by default. Positive finite weights change
the relative probabilities; use `pool.set_weight(name, weight)` to adjust
them. Factories receive an action-selection seed and must return independent
instances. A constructor without a seed can ignore the argument, as above.
Adding a second independently trained agent or several MCTS search settings
will simply mean adding more factories.

An initial learner checkpoint enters the pool before the first game, so an
empty pool can run historical self-play. Scheduled snapshots and the final
snapshot also enter the pool. Names such as `learner@checkpoint-000001`
identify exact opponents in the logs. At most `max_historical_opponents`
automatically added snapshots remain active; removing them from the pool
does not delete their artifacts. Baseline entries and manually added
checkpoints are retained.

`result.training.wins` counts wins by seat. `result.learner_wins` and
`result.opponent_wins` follow identity across seat changes.
`history.matchups` links each episode to its opponent, opponent seed,
learner seat, and learning flags.

## Checkpoints

An algorithm that participates as the league learner inherits
`CheckpointableAgent` and implements:

- `save_checkpoint(path: Path) -> None`: write the algorithm's state as
  a file or directory at the supplied path, without mutating the live agent.
- `load_checkpoint(path: Path, seed: int | None = None) -> Self`: reconstruct
  an independent agent. With no seed, restore saved RNG state; with a seed,
  reset action-selection randomness without resetting learned parameters.

The algorithm owns its serialization format, so future JAX/Flax models can
use their native checkpoint facilities. The manager writes a versioned JSON
manifest containing agent type, episode, purpose and artifact location.
Loading requires an explicit agent class; manifests are never imported or
executed. Existing checkpoint names are never overwritten. A failed save
does not publish a completed manifest and is excluded from checkpoint listings.

`DummyAgent` stores its update counter and RNG state in JSON. For example:

```python
manager = CheckpointManager("runs/experiment/checkpoints")
available = manager.list_checkpoints()
learner = manager.load(available[-1].name, DummyAgent)
pool.add_checkpoint(manager, available[0], DummyAgent, weight=2)
```

The demo also supports:

```bash
uv run python -m examples.train_dummy_league --output runs/dummy-league \
    --resume checkpoint-000004 --episodes 12
```

Restoring a learner continues its saved state. It starts a new league run:
episode numbering, scheduler RNG and pool membership are not automatically
restored. Reconstruct historical pool entries explicitly when needed.
Checkpoint listings are sorted by name, not by training episode; use manifest
metadata to select a desired snapshot.

## Tournaments

Scheduled tournaments and a final tournament evaluate every unordered pair
in the current pool plus a snapshot of the latest learner. Disable them with
`tournament_every=None`. Each pair plays an even number of games and swaps
seats after each game. Paired games reuse agent seeds and starting-state
seeds. Configure comparable search/time budgets through the factories.

Evaluation never calls `update()`. All participants are newly constructed;
the live learner is never used for evaluation. Evaluation also owns a separate
RNG. Off-schedule evaluation snapshots use `evaluation-...` names and do
not enter the training pool, so changing the evaluation schedule does not
change training matchups or consume learner randomness.

`TournamentResult.matches` contains each pair's wins, draws, truncations
and total steps. `win_rates[row][column]` reports the fraction of all games
won by the row participant. Truncated games count in the denominator but
are neither losses nor draws, so opposing win rates need not sum to one.

Use the same machinery independently:

```python
from santorinai.training import run_tournament

tournament = run_tournament(
    {
        "random": lambda seed: RandomAgent(seed),
        "first-choice": lambda seed: FirstChoiceAgent(),
    },
    games_per_pair=20,
    seed=42,
    callbacks=[JSONLLogger("runs/tournament.jsonl")],
)
print(tournament.win_rates)
```

For a stable benchmark, keep a separate fixed set of evaluation factories;
the league's automatic tournaments intentionally follow the current pool.

## Experience and rewards

An `EpisodeResult` contains summary `metrics` and a chronological tuple
of `Transition` records from both seats, including worker placement.
Each transition records its actor, phase, attempted action, immutable state
snapshots, validity, reason, both rewards, and termination/truncation flags.
Snapshots expose `to_state()` for independent legal-action enumeration or
search. Players receive private state copies, including a private legal-action
cache, so their mutations cannot alter the live game.

Intermediate rewards are `(0, 0)`. The terminal winner receives +1 and
the loser -1. An illegal returned action forfeits immediately; exceptions
raised by agent code propagate. `max_steps` counts placements and moves
together. A step limit produces zero rewards and `truncated=True`, and
is counted separately from a draw. Algorithms decide how to bootstrap those
truncated samples.

A learning seat receives the whole episode, including the opponent's terminal
action. Algorithms own their encoders, buffers, policy outputs, targets and
optimizers. Neural MCTS will additionally need search visit distributions;
these are not fabricated by the dummy scaffold.

## Callbacks and stopping

Subclass `TrainingCallback` and override only the hooks you need:

| Hook | Data |
| --- | --- |
| `on_training_start` | `TrainingConfig` |
| `on_league_start` | `LeagueConfig` |
| `on_checkpoint_saved` | `CheckpointInfo` |
| `on_matchup` | `Matchup` with opponent identity and rotating seat |
| `on_episode_start` | Episode number |
| `on_step` | `Transition` |
| `on_update` | `UpdateResult` with learning seat and scalar metrics |
| `on_episode_end` | `EpisodeResult` |
| `on_tournament_start` | `TournamentConfig` |
| `on_tournament_game` | `TournamentGame`, participants in seat order |
| `on_tournament_match` | `TournamentMatch`, aggregated pair results |
| `on_tournament_end` | `TournamentResult` |
| `on_training_end` | `TrainingResult` |
| `on_league_end` | `LeagueResult` |

A league begins with training-start, league-start and initial-checkpoint
events. Each episode emits matchup, episode-start, step events, learner
update, and episode-end. Checkpoint and tournament events follow when due.
The training-start seat flags describe the initial assignment; each matchup
records the flags actually used for that episode. Tournament games emit only
tournament hooks, keeping them out of training histories.

Return `False` from `on_episode_end` to stop after the current episode.
Every remaining callback still receives that episode; the league saves a
final checkpoint, skips further tournaments, and emits the end hooks.
Exceptions propagate and do not emit successful end hooks.

`HistoryCallback` stores summaries, update metrics, matchups, checkpoints
and tournament results without retaining trajectories or individual evaluation
games. Training-start clears its history. `JSONLLogger` writes records
immediately, and repeated runs append start/end-delimited records.
Use JSONL alone for long runs to avoid an ever-growing in-memory history.
