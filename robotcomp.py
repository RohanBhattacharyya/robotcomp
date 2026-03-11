"""
robotcomp.py

A tiny CLI robot competition engine.

Usage:

    import robotcomp

    def chaser(api):
        if api.robot_in_right():
            api.tag_right()
        elif api.same_row() and api.can_move_right():
            api.move_right()
        elif api.same_column() and api.can_move_back():
            api.move_back()
        else:
            api.wait()

    player = robotcomp.create_bot("Player", chaser, "P")
    robotcomp.play(player, fast=False)

You can also pit two user bots against each other:

    bot1 = robotcomp.create_bot("Bot 1", bot1_logic, "1")
    bot2 = robotcomp.create_bot("Bot 2", bot2_logic, "2")
    robotcomp.play(bot1, bot2, fast=True)

Persistent bot memory example:

    def move_pattern():
        while True:
            yield "back"
            yield "right"

    def my_bot(api):
        pattern = api.remember("pattern", move_pattern)
        move = next(pattern)

        if api.robot_in_front():
            api.tag_forward()
        elif move == "back":
            api.move_back()
        elif move == "right":
            api.move_right()
        else:
            api.wait()
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


Position = Tuple[int, int]
Controller = Callable[["BotAPI"], None]

__all__ = [
    "ActionLimitError",
    "Bot",
    "BotAPI",
    "create_bot",
    "create_random_bot",
    "play",
]


class ActionLimitError(RuntimeError):
    """Raised when a bot tries to take more than one action in a single tick."""


@dataclass(frozen=True)
class Bot:
    """A robot entry for the competition."""
    name: str
    controller: Controller
    symbol: str


@dataclass
class _BotState:
    bot: Bot
    pos: Position
    memory: Dict[str, Any] = field(default_factory=dict)


class BotAPI:
    """
    Per-tick API exposed to a bot controller.

    A bot may do unlimited checks, but may only take one action per tick.

    The `memory` dictionary persists across ticks for the duration of a match,
    so bots can store generators, counters, modes, etc.
    """

    def __init__(
        self,
        *,
        width: int,
        height: int,
        me: _BotState,
        opponent: _BotState,
        tick: int,
        goes_first: bool,
        memory: Dict[str, Any],
    ) -> None:
        self.width = width
        self.height = height
        self._me = me
        self._opponent = opponent
        self.tick = tick
        self.goes_first = goes_first
        self.memory = memory
        self._action: Optional[Tuple[str, str]] = None

    # ----------------------------
    # Read-only info
    # ----------------------------
    @property
    def name(self) -> str:
        return self._me.bot.name

    @property
    def symbol(self) -> str:
        return self._me.bot.symbol

    @property
    def position(self) -> Position:
        return self._me.pos

    @property
    def opponent_name(self) -> str:
        return self._opponent.bot.name

    @property
    def opponent_symbol(self) -> str:
        return self._opponent.bot.symbol

    @property
    def opponent_position(self) -> Position:
        return self._opponent.pos

    def x(self) -> int:
        return self._me.pos[0]

    def y(self) -> int:
        return self._me.pos[1]

    def opponent_x(self) -> int:
        return self._opponent.pos[0]

    def opponent_y(self) -> int:
        return self._opponent.pos[1]

    def same_row(self) -> bool:
        return self.y() == self.opponent_y()

    def same_column(self) -> bool:
        return self.x() == self.opponent_x()

    def robot_adjacent(self) -> bool:
        return self.manhattan_distance() == 1

    def manhattan_distance(self) -> int:
        return abs(self.x() - self.opponent_x()) + abs(self.y() - self.opponent_y())

    def nearest_edge_distance(self) -> int:
        return min(
            self.x(),
            self.y(),
            self.width - 1 - self.x(),
            self.height - 1 - self.y(),
        )

    def in_bounds(self, x: int, y: int) -> bool:
        return _in_bounds((x, y), self.width, self.height)

    def remember(self, key: str, factory: Callable[[], Any]) -> Any:
        """
        Store something once for this bot during the current match and reuse it.

        Example:
            pattern = api.remember("pattern", move_pattern)
            move = next(pattern)
        """
        if key not in self.memory:
            self.memory[key] = factory()
        return self.memory[key]

    # ----------------------------
    # Relative robot checks
    # ----------------------------
    def robot_in_front(self) -> bool:
        return self._is_adjacent("forward")

    def robot_in_back(self) -> bool:
        return self._is_adjacent("back")

    def robot_in_left(self) -> bool:
        return self._is_adjacent("left")

    def robot_in_right(self) -> bool:
        return self._is_adjacent("right")

    # ----------------------------
    # Movement feasibility checks
    # ----------------------------
    def can_move_forward(self) -> bool:
        return self._can_move("forward")

    def can_move_back(self) -> bool:
        return self._can_move("back")

    def can_move_left(self) -> bool:
        return self._can_move("left")

    def can_move_right(self) -> bool:
        return self._can_move("right")

    # ----------------------------
    # Actions: exactly one per tick
    # ----------------------------
    def move_forward(self) -> bool:
        return self._set_action("move", "forward")

    def move_back(self) -> bool:
        return self._set_action("move", "back")

    def move_left(self) -> bool:
        return self._set_action("move", "left")

    def move_right(self) -> bool:
        return self._set_action("move", "right")

    def tag_forward(self) -> bool:
        return self._set_action("tag", "forward")

    def tag_back(self) -> bool:
        return self._set_action("tag", "back")

    def tag_left(self) -> bool:
        return self._set_action("tag", "left")

    def tag_right(self) -> bool:
        return self._set_action("tag", "right")

    def wait(self) -> bool:
        return self._set_action("wait", "wait")

    def action_taken(self) -> Optional[Tuple[str, str]]:
        return self._action

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _set_action(self, kind: str, direction: str) -> bool:
        if self._action is not None:
            raise ActionLimitError(
                f"{self.name} tried to take more than one action in tick {self.tick}."
            )
        self._action = (kind, direction)
        return True

    def _can_move(self, direction: str) -> bool:
        next_pos = _step(self._me.pos, direction)
        return (
            _in_bounds(next_pos, self.width, self.height)
            and next_pos != self._opponent.pos
        )

    def _is_adjacent(self, direction: str) -> bool:
        return _step(self._me.pos, direction) == self._opponent.pos


def create_bot(name: str, controller: Controller, symbol: Optional[str] = None) -> Bot:
    """
    Create a user bot that can be passed to play().

    Example:
        def hunter(api):
            if api.robot_in_right():
                api.tag_right()
            elif api.can_move_right():
                api.move_right()
            else:
                api.wait()

        bot = create_bot("Hunter", hunter, "H")
    """
    if not name:
        raise ValueError("Bot name must not be empty.")
    if symbol is None:
        symbol = name[0].upper()
    if len(symbol) != 1:
        raise ValueError("Bot symbol must be exactly one character.")
    return Bot(name=name, controller=controller, symbol=symbol)


def create_random_bot(name: str = "Computer", symbol: str = "C") -> Bot:
    """
    Create the built-in computer bot.

    Strategy:
    - If the opponent is adjacent, tag immediately.
    - Otherwise move randomly among all valid moves.
    - If no move is valid, wait.
    """

    def random_controller(api: BotAPI) -> None:
        adjacent_tags = [
            (api.robot_in_front, api.tag_forward),
            (api.robot_in_back, api.tag_back),
            (api.robot_in_left, api.tag_left),
            (api.robot_in_right, api.tag_right),
        ]

        for check, action in adjacent_tags:
            if check():
                action()
                return

        moves: List[Callable[[], bool]] = []
        if api.can_move_forward():
            moves.append(api.move_forward)
        if api.can_move_back():
            moves.append(api.move_back)
        if api.can_move_left():
            moves.append(api.move_left)
        if api.can_move_right():
            moves.append(api.move_right)

        if moves:
            random.choice(moves)()
        else:
            api.wait()

    return create_bot(name=name, controller=random_controller, symbol=symbol)


def play(
    player1: Bot,
    player2: Optional[Bot] = None,
    *,
    width: int = 10,
    height: int = 10,
    fast: bool = False,
    max_ticks: int = 500,
    seed: Optional[int] = None,
    show_board: bool = True,
    clear_screen: bool = True,
    start_pos1: Optional[Position] = None,
    start_pos2: Optional[Position] = None,
) -> str:
    """
    Run a match and return the winning bot name, or "Draw".

    Rules:
    - If player2 is omitted, player1 plays against the built-in computer bot.
    - Player 1 acts first on tick 1.
    - First mover alternates every tick.
    - A successful tag ends the match immediately.
    - The board is printed every tick. In normal mode it waits 0.5 seconds
      between ticks; in fast mode there is no delay.

    Defaults:
    - Player 1 starts at (0, 0)
    - Player 2 starts at (width - 1, height - 1)
    """
    if width < 1 or height < 1 or (width * height) < 2:
        raise ValueError("The board must contain at least two squares.")
    if max_ticks < 1:
        raise ValueError("max_ticks must be at least 1.")

    vs_computer = player2 is None
    if player2 is None:
        player2 = create_random_bot()

    if player1.name == player2.name:
        raise ValueError("Bots must have different names.")
    if player1.symbol == player2.symbol:
        raise ValueError("Bots must have different symbols.")

    if seed is not None:
        random.seed(seed)

    pos1 = start_pos1 if start_pos1 is not None else (0, 0)
    pos2 = start_pos2 if start_pos2 is not None else (width - 1, height - 1)

    if not _in_bounds(pos1, width, height):
        raise ValueError("start_pos1 is out of bounds.")
    if not _in_bounds(pos2, width, height):
        raise ValueError("start_pos2 is out of bounds.")
    if pos1 == pos2:
        raise ValueError("Robots cannot start on the same square.")

    state1 = _BotState(bot=player1, pos=pos1)
    state2 = _BotState(bot=player2, pos=pos2)

    if show_board:
        _print_board(width, height, state1, state2, tick=0, clear_screen=clear_screen)

    for tick in range(1, max_ticks + 1):
        if tick % 2 == 1:
            turn_order = [(state1, state2), (state2, state1)]
        else:
            turn_order = [(state2, state1), (state1, state2)]

        winner_state: Optional[_BotState] = None

        for index, (current, other) in enumerate(turn_order):
            winner_state = _run_turn(
                width=width,
                height=height,
                current=current,
                other=other,
                tick=tick,
                goes_first=(index == 0),
            )
            if winner_state is not None:
                break

        if show_board:
            _print_board(width, height, state1, state2, tick=tick, clear_screen=clear_screen)

        if winner_state is not None:
            if vs_computer:
                print("Player wins!" if winner_state.bot == player1 else "Computer wins!")
            else:
                print("Player 1 wins!" if winner_state.bot == player1 else "Player 2 wins!")
            return winner_state.bot.name

        if show_board and not fast:
            time.sleep(0.5)

    if show_board:
        print("Draw!")
    return "Draw"


def _run_turn(
    *,
    width: int,
    height: int,
    current: _BotState,
    other: _BotState,
    tick: int,
    goes_first: bool,
) -> Optional[_BotState]:
    api = BotAPI(
        width=width,
        height=height,
        me=current,
        opponent=other,
        tick=tick,
        goes_first=goes_first,
        memory=current.memory,
    )

    try:
        current.bot.controller(api)
    except ActionLimitError:
        # The bot already used its first action; ignore any extra attempt.
        pass
    except Exception:
        # A crashing bot simply loses its action for this tick.
        return None

    action = api.action_taken()
    if action is None:
        return None

    kind, direction = action

    if kind == "wait":
        return None

    if kind == "move":
        next_pos = _step(current.pos, direction)
        if _in_bounds(next_pos, width, height) and next_pos != other.pos:
            current.pos = next_pos
        return None

    if kind == "tag":
        if _step(current.pos, direction) == other.pos:
            return current
        return None

    return None


def _print_board(
    width: int,
    height: int,
    state1: _BotState,
    state2: _BotState,
    *,
    tick: int,
    clear_screen: bool,
) -> None:
    if clear_screen:
        print("\033[H\033[J", end="")

    print(f"Tick: {tick}")
    for y in range(height):
        row: List[str] = []
        for x in range(width):
            pos = (x, y)
            if pos == state1.pos:
                row.append(state1.bot.symbol)
            elif pos == state2.pos:
                row.append(state2.bot.symbol)
            else:
                row.append(".")
        print(" ".join(row))
    print()


def _step(pos: Position, direction: str) -> Position:
    x, y = pos

    if direction == "forward":
        return (x, y - 1)
    if direction == "back":
        return (x, y + 1)
    if direction == "left":
        return (x - 1, y)
    if direction == "right":
        return (x + 1, y)
    if direction == "wait":
        return (x, y)

    raise ValueError(f"Unknown direction: {direction}")


def _in_bounds(pos: Position, width: int, height: int) -> bool:
    x, y = pos
    return 0 <= x < width and 0 <= y < height