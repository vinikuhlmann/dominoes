from collections import deque
from dataclasses import dataclass
from random import shuffle
from typing import Deque, Literal, Optional


class Tile:
    def __init__(self, left: int, right: int):
        if left < 1 or left > 6 or right < 1 or right > 6:
            raise ValueError("Domino tiles must have values between 1 and 6")

        self.left = left
        self.right = right

    def __str__(self):
        return f"[{self.left}|{self.right}]"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.left == other.left and self.right == other.right

        if isinstance(other, tuple):
            return len(other) == 2 and (
                self.left == other[0]
                and self.right == other[1]
                or self.left == other[1]
                and self.right == other[0]
            )

        return False

    def __hash__(self):
        return hash((self.left, self.right))

    def rotate(self):
        self.left, self.right = self.right, self.left

    @property
    def is_double(self):
        return self.left == self.right


DOMINO_SET = frozenset(
    Tile(left, right) for left in range(7) for right in range(left, 7)
)


class Table:
    def __init__(self):
        self.tiles: Deque[Tile] = deque()
        self._value_counts = [0] * 7

    @property
    def is_empty(self):
        return not bool(self.tiles)

    @property
    def left_end(self):
        return self.tiles[0].left if not self.is_empty else None

    @property
    def right_end(self):
        return self.tiles[-1].right if not self.is_empty else None
    
    @property
    def is_blocked(self):
        if self.left_end != self.right_end:
            return False

        return self._value_counts[self.left_end] == 8

    def can_play_left(self, tile: Tile):
        return tile.left == self.left_end or tile.right == self.left_end

    def can_play_right(self, tile: Tile):
        return tile.left == self.right_end or tile.right == self.right_end

    def can_play(self, tile: Tile):
        return self.can_play_left(tile) or self.can_play_right(tile)

    class InvalidTilePlacement(Exception):
        pass

    def _add_left(self, tile: Tile):
        if not self.can_play_left(tile):
            raise self.InvalidTilePlacement("Cannot add tile to the left end")
        
        if not tile.right == self.left_end:
            tile.rotate()

        self.tiles.appendleft(tile)
        self._value_counts[tile.left] += 1
        self._value_counts[tile.right] += 1

    def _add_right(self, tile: Tile):
        if not self.can_play_right(tile):
            raise self.InvalidTilePlacement("Cannot add tile to the right end")
        
        if not tile.left == self.right_end:
            tile.rotate()
            
        self.tiles.append(tile)
        self._value_counts[tile.left] += 1
        self._value_counts[tile.right] += 1

    class AmbiguousTilePlacement(Exception):
        pass

    def add_tile(self, tile: Tile, side: Literal["left", "right"] = None):
        if side is not None and side not in ("left", "right"):
            raise ValueError("Side must be either 'left' or 'right' if provided")

        if self.is_empty:
            self.tiles.append(tile)
            return

        if side == "left":
            self._add_left(tile)
            return

        elif side == "right":
            self._add_right(tile)
            return

        if (
            not tile.is_double
            and self.can_play_left(tile)
            and self.can_play_right(tile)
        ):
            raise self.AmbiguousTilePlacement("Tile can be added to both ends")

        try:
            self._add_left(tile)
        except self.InvalidTilePlacement:
            self._add_right(tile)


@dataclass
class Player:
    name: str
    hand: set[Tile]

    @property
    def score(self):
        return sum(tile.left + tile.right for tile in self.hand)


class Game:
    def __init__(self, players: list[Player]):
        if len(players) < 2 or len(players) > 4:
            raise ValueError("A game must have between 2 and 4 players")

        self.players = players
        self.table = Table()
        self.stock = list(DOMINO_SET)
        self.first_player: Optional[int] = None
        self.turn = 0

    def deal(self):
        shuffle(self.stock)
        for _ in range(7):
            for index, player in enumerate(self.players):
                tile = self.stock.pop()
                if tile.left == 6 and tile.right == 6:
                    self.first_player = index
                player.hand.add(tile)

    @property
    def current_player(self) -> Player | None:
        if not self.first_player:
            raise ValueError("Game has not started yet, deal the tiles first")

        index = (self.turn + self.first_player) % len(self.players)
        return self.players[index]

    @property
    def available_plays(self):
        return {tile for tile in self.current_player.hand if self.table.can_play(tile)}

    def play(self, tile: Tile, side: Optional[Literal["left", "right"]] = None) -> Player | None:
        if tile not in self.current_player.hand:
            raise ValueError("Player does not have this tile in hand")

        self.table.add_tile(tile, side)
        self.current_player.hand.remove(tile)
        if not self.current_player.hand:
            return self.current_player
        
        if self.table.is_blocked:
            min_scoring_player = min(self.players, key=lambda player: player.score)
            return min_scoring_player
        
        self.turn += 1
    
    def draw_until_playable(self):
        while self.stock and not self.available_plays:
            self.current_player.hand.add(self.stock.pop())
