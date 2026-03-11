# robotcomp

`robotcomp` is a small Python module for running a CLI robot tag competition on a 2D grid.

It supports:

- **user bot vs computer bot**
- **user bot vs user bot**
- a simple built-in **random computer algorithm**
- **persistent bot memory** across ticks
- **one action per tick** enforcement
- animated CLI board rendering with optional **fast mode**

---

## Overview

Each match places two robots on a grid.

The goal is simple:

- move around the board
- get adjacent to the opponent
- **tag** them before they tag you

A robot can do:

- unlimited **checks** each tick
- **exactly one action** each tick

Actions include:

- moving: forward, back, left, right
- tagging: forward, back, left, right
- waiting

---

## Installation

There is no package install required.

Just save the file as:

```python
robotcomp.py
````

Then import it in another Python file:

```python
import robotcomp
```

---

## Quick Start

### Player vs Computer

```python
import robotcomp


def my_bot(api: robotcomp.BotAPI) -> None:
    if api.robot_in_front():
        api.tag_forward()
    elif api.robot_in_back():
        api.tag_back()
    elif api.robot_in_left():
        api.tag_left()
    elif api.robot_in_right():
        api.tag_right()
    elif api.can_move_right():
        api.move_right()
    else:
        api.wait()


player = robotcomp.create_bot("Player", my_bot, "P")
robotcomp.play(player)
```

---

## Two User Bots

```python
import robotcomp


def bot1_logic(api: robotcomp.BotAPI) -> None:
    if api.robot_in_right():
        api.tag_right()
    elif api.can_move_right():
        api.move_right()
    else:
        api.wait()


def bot2_logic(api: robotcomp.BotAPI) -> None:
    if api.robot_in_left():
        api.tag_left()
    elif api.can_move_left():
        api.move_left()
    else:
        api.wait()


bot1 = robotcomp.create_bot("Bot 1", bot1_logic, "1")
bot2 = robotcomp.create_bot("Bot 2", bot2_logic, "2")

robotcomp.play(bot1, bot2)
```

---

## Match Rules

### Turn Order

* On **tick 1**, `player1` always goes first.
* After that, turn order **alternates every tick**.
* In player-vs-computer mode, the player is always `player1`.
* In player-vs-player mode, the first bot passed into `play()` is always `player1`.

### Winning

A robot wins immediately when a tag action successfully targets the square occupied by the opponent.

Final messages are:

* `Player wins!`
* `Computer wins!`
* `Player 1 wins!`
* `Player 2 wins!`

If no robot wins by `max_ticks`, the result is:

* `Draw!`

---

## Coordinate System

The board is a grid of `(x, y)` coordinates.

* `(0, 0)` is the **top-left**
* `x` increases to the **right**
* `y` increases **downward**

Direction meanings:

* `forward` = up = `(x, y - 1)`
* `back` = down = `(x, y + 1)`
* `left` = `(x - 1, y)`
* `right` = `(x + 1, y)`

---

## Main Functions

## `create_bot(name, controller, symbol=None)`

Creates a user-controlled bot.

### Parameters

* `name`: bot name as a string
* `controller`: function that accepts a `BotAPI`
* `symbol`: single-character symbol shown on the board

### Example

```python
def my_bot(api):
    api.wait()

bot = robotcomp.create_bot("My Bot", my_bot, "M")
```

---

## `create_random_bot(name="Computer", symbol="C")`

Creates the built-in computer bot.

The built-in algorithm:

1. checks whether the opponent is adjacent
2. tags immediately if possible
3. otherwise makes a random valid move
4. waits if no move is possible

### Example

```python
computer = robotcomp.create_random_bot()
```

---

## `play(player1, player2=None, *, width=10, height=10, fast=False, max_ticks=500, seed=None, show_board=True, clear_screen=True, start_pos1=None, start_pos2=None)`

Runs a match.

### Parameters

* `player1`: first bot
* `player2`: second bot; if omitted, uses the built-in computer bot
* `width`: board width
* `height`: board height
* `fast`: if `False`, pauses `0.5` seconds between ticks; if `True`, runs as fast as possible
* `max_ticks`: maximum ticks before declaring a draw
* `seed`: optional random seed
* `show_board`: whether to print the board every tick
* `clear_screen`: whether to clear the terminal before each frame
* `start_pos1`: optional starting position for player 1
* `start_pos2`: optional starting position for player 2

### Returns

Returns:

* winner bot name as a string
* or `"Draw"`

### Example

```python
winner = robotcomp.play(player1, player2, width=8, height=6, fast=True)
print(winner)
```

---

## Bot Controller Function

A bot controller is a function like this:

```python
def my_bot(api: robotcomp.BotAPI) -> None:
    ...
```

The engine calls this function once per tick for that bot.

Inside that function, the bot may:

* do unlimited checks
* take exactly one action

If the bot tries to take more than one action, extra actions are ignored through the action limit handling.

---

## `BotAPI` Reference

The `BotAPI` object is what your bot uses to inspect the board and act.

---

## Read-Only Information

### `api.name`

Your bot's name.

### `api.symbol`

Your bot's display symbol.

### `api.position`

Your bot's current `(x, y)` position.

### `api.opponent_name`

Opponent name.

### `api.opponent_symbol`

Opponent symbol.

### `api.opponent_position`

Opponent `(x, y)` position.

### `api.tick`

Current tick number.

### `api.goes_first`

`True` if this bot is acting first on the current tick, otherwise `False`.

### `api.width`

Board width.

### `api.height`

Board height.

---

## Position Helpers

### `api.x()`

Returns your x-coordinate.

### `api.y()`

Returns your y-coordinate.

### `api.opponent_x()`

Returns opponent x-coordinate.

### `api.opponent_y()`

Returns opponent y-coordinate.

### `api.same_row()`

Returns `True` if both robots are in the same row.

### `api.same_column()`

Returns `True` if both robots are in the same column.

### `api.robot_adjacent()`

Returns `True` if the opponent is exactly 1 tile away.

### `api.manhattan_distance()`

Returns Manhattan distance to the opponent.

### `api.nearest_edge_distance()`

Returns the distance from your robot to the nearest board edge.

### `api.in_bounds(x, y)`

Returns `True` if `(x, y)` is inside the board.

---

## Adjacency Checks

These check whether the opponent is directly adjacent in a specific direction.

### `api.robot_in_front()`

### `api.robot_in_back()`

### `api.robot_in_left()`

### `api.robot_in_right()`

Example:

```python
if api.robot_in_left():
    api.tag_left()
```

---

## Movement Feasibility Checks

These check whether a move is legal.

A move is legal only if:

* it stays inside the board
* it does not move into the opponent's square

### `api.can_move_forward()`

### `api.can_move_back()`

### `api.can_move_left()`

### `api.can_move_right()`

Example:

```python
if api.can_move_forward():
    api.move_forward()
else:
    api.wait()
```

---

## Actions

A bot may perform only **one** of these per tick.

### Movement

* `api.move_forward()`
* `api.move_back()`
* `api.move_left()`
* `api.move_right()`

### Tagging

* `api.tag_forward()`
* `api.tag_back()`
* `api.tag_left()`
* `api.tag_right()`

### Do Nothing

* `api.wait()`

---

## Persistent Match Memory

One important feature of this version is **persistent per-bot memory**.

This allows you to store state across ticks, including:

* generators
* counters
* modes
* path plans
* toggles
* custom strategy state

Use:

```python
api.remember(key, factory)
```

If `key` does not exist yet, `factory()` is called once and stored.
After that, the same stored value is returned every future tick for that bot in the same match.

### Example with a Generator

```python
import robotcomp


def move_pattern():
    while True:
        yield "back"
        yield "right"


def my_bot(api: robotcomp.BotAPI) -> None:
    if api.robot_in_front():
        api.tag_forward()
    elif api.robot_in_back():
        api.tag_back()
    elif api.robot_in_left():
        api.tag_left()
    elif api.robot_in_right():
        api.tag_right()
    else:
        pattern = api.remember("move_pattern", move_pattern)
        move = next(pattern)

        if move == "forward":
            api.move_forward()
        elif move == "back":
            api.move_back()
        elif move == "left":
            api.move_left()
        elif move == "right":
            api.move_right()
        else:
            api.wait()


player = robotcomp.create_bot("Pattern Bot", my_bot, "P")
robotcomp.play(player)
```

### Why This Is Needed

This does **not** work correctly:

```python
move = next(move_pattern())
```

because that creates a **new generator every tick**, so it always starts from the first `yield`.

Using `api.remember("move_pattern", move_pattern)` stores the generator once and reuses it, so the yields progress properly over time.

---

## Example Strategies

## 1. Aggressive Chaser

```python
def aggressive(api):
    if api.robot_in_front():
        api.tag_forward()
    elif api.robot_in_back():
        api.tag_back()
    elif api.robot_in_left():
        api.tag_left()
    elif api.robot_in_right():
        api.tag_right()
    else:
        delta = api.direction_to_opponent()

        if delta["dx"] > 0 and api.can_move_right():
            api.move_right()
        elif delta["dx"] < 0 and api.can_move_left():
            api.move_left()
        elif delta["dy"] > 0 and api.can_move_back():
            api.move_back()
        elif delta["dy"] < 0 and api.can_move_forward():
            api.move_forward()
        else:
            api.wait()
```

---

## 2. Patrol Pattern

```python
def patrol_pattern():
    while True:
        yield "right"
        yield "right"
        yield "back"
        yield "back"
        yield "left"
        yield "left"
        yield "forward"
        yield "forward"


def patrol_bot(api):
    if api.robot_in_front():
        api.tag_forward()
        return
    if api.robot_in_back():
        api.tag_back()
        return
    if api.robot_in_left():
        api.tag_left()
        return
    if api.robot_in_right():
        api.tag_right()
        return

    pattern = api.remember("patrol", patrol_pattern)
    move = next(pattern)

    if move == "forward" and api.can_move_forward():
        api.move_forward()
    elif move == "back" and api.can_move_back():
        api.move_back()
    elif move == "left" and api.can_move_left():
        api.move_left()
    elif move == "right" and api.can_move_right():
        api.move_right()
    else:
        api.wait()
```

---

## 3. Row/Column Hunter

```python
def line_hunter(api):
    if api.robot_in_front():
        api.tag_forward()
    elif api.robot_in_back():
        api.tag_back()
    elif api.robot_in_left():
        api.tag_left()
    elif api.robot_in_right():
        api.tag_right()
    elif api.same_row():
        if api.opponent_x() > api.x() and api.can_move_right():
            api.move_right()
        elif api.opponent_x() < api.x() and api.can_move_left():
            api.move_left()
        else:
            api.wait()
    elif api.same_column():
        if api.opponent_y() > api.y() and api.can_move_back():
            api.move_back()
        elif api.opponent_y() < api.y() and api.can_move_forward():
            api.move_forward()
        else:
            api.wait()
    else:
        api.wait()
```

---

## Board Output

The board is printed each tick using:

* the tick number at the top
* each robot symbol in its current position
* `.` for empty spaces

Example:

```text
Tick: 4
P . . . .
. . . . .
. . C . .
. . . . .
```

---

## Error Behavior

### Invalid Bot Names or Symbols

* bot name must not be empty
* symbol must be exactly one character
* both bots must have different names
* both bots must have different symbols

### Invalid Board

The board must contain at least two squares.

### Invalid Start Positions

Start positions must:

* be in bounds
* not overlap

### Bot Exceptions

If a bot controller crashes with an exception during its turn, it simply loses its action for that tick.

---

## Notes on Strategy Design

Because only one action is allowed per tick, a good bot usually follows this pattern:

1. check whether it can tag immediately
2. otherwise decide on one move
3. otherwise wait

A common pattern is:

```python
if can_tag:
    tag
elif can_move:
    move
else:
    wait
```

Persistent memory is especially useful for:

* repeated movement patterns
* multi-step plans
* toggling between attack/retreat modes
* remembering previous direction choices

---

## Full Example

```python
import robotcomp


def move_pattern():
    while True:
        yield "back"
        yield "right"


def my_bot(api: robotcomp.BotAPI) -> None:
    if api.robot_in_front():
        api.tag_forward()
    elif api.robot_in_back():
        api.tag_back()
    elif api.robot_in_left():
        api.tag_left()
    elif api.robot_in_right():
        api.tag_right()
    else:
        pattern = api.remember("move_pattern", move_pattern)
        move = next(pattern)

        if move == "forward" and api.can_move_forward():
            api.move_forward()
        elif move == "back" and api.can_move_back():
            api.move_back()
        elif move == "left" and api.can_move_left():
            api.move_left()
        elif move == "right" and api.can_move_right():
            api.move_right()
        else:
            api.wait()


player = robotcomp.create_bot("Pattern Bot", my_bot, "P")
robotcomp.play(player, width=8, height=6, fast=False)
```

---

## Summary

`robotcomp` is useful when you want to:

* prototype simple game AI
* test turn-based bot logic
* compare strategies
* build deterministic or stateful robot behaviors in a small CLI environment

The most important concepts are:

* **one action per tick**
* **unlimited checks**
* **adjacent tag wins**
* **persistent memory through `api.remember()`**

---