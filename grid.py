from card import Tile
from config import TILE_SIZE

class Grid:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.tiles = [[Tile(c, r) for r in range(rows)] for c in range(cols)]
    
    def in_bounds(self, c, r):
        return 0 <= c < self.cols and 0 <= r < self.rows

def cell_center(c, r):
    return c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2
