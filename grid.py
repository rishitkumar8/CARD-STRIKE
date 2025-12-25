"""
Grid is treated as an implicit unweighted graph:
- Each tile is a node
- Adjacent tiles are edges
- BFS is used for movement and attack range evaluation
"""

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

def get_neighbors(c, r, grid):
    """
    Graph adjacency: returns neighboring nodes (up, down, left, right)
    """
    neighbors = []
    for dc, dr in [(1,0), (-1,0), (0,1), (0,-1)]:
        nc, nr = c + dc, r + dr
        if grid.in_bounds(nc, nr):
            neighbors.append((nc, nr))
    return neighbors

from collections import deque

def bfs_reachable(start, max_depth, grid):
    """
    Graph traversal (BFS) to find reachable nodes within depth
    """
    visited = set()
    queue = deque([(start, 0)])
    reachable = set()

    while queue:
        (c, r), d = queue.popleft()
        if d > max_depth:
            continue

        reachable.add((c, r))

        for nc, nr in get_neighbors(c, r, grid):
            if (nc, nr) not in visited:
                visited.add((nc, nr))
                queue.append(((nc, nr), d + 1))

    return reachable

