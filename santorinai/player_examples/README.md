
# Player examples

We provide some examples of players in this directory.


## Randy Random: The random player

A player that choose a random action among the possible ones.

## Firsty First: The first choice player

A player that always choose the first possible action.

## Extra BaThick!: The basic player

Answer to simple rules:
- If there is a winning move, play it.
- If we can prevent the opponent from winning, do it.
- Move up if we can
- Build randomly

# Statistics

We ran 1000 games between each pair of players, and computed the winning rates:

| Players            | p2. Randy Random | p2. Firsty First | p2. Extra BaThick! |
| ------------------ | ---------------- | ---------------- | ------------------ |
| p1. Randy Random   | -                | 13%              | 1%                 |
| p1. Firsty First   | 87%              | -                | 18%                |
| p1. Extra BaThick! | 98%              | 86%              | -                  |

Global Winning Rates:
- Randy Random: 7.60%
- Firsty First: 52.60%
- Extra BaThick!: 92.10%