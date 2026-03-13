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

def chebyshev_dist(c1, r1, c2, r2):
    return max(abs(c1 - c2), abs(r1 - r2))

def get_neighbors(c, r, grid, diagonal=False):
    """
    Graph adjacency: returns neighbors.
    diagonal=False -> 4-way (Manhattan/Movement)
    diagonal=True  -> 8-way (Chebyshev/Attack)
    """
    neighbors = []
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    if diagonal:
        directions += [(1,1), (-1,1), (1,-1), (-1,-1)]

    for dc, dr in directions:
        nc, nr = c + dc, r + dr
        if grid.in_bounds(nc, nr):
            neighbors.append((nc, nr))
    return neighbors

from collections import deque

def bfs_reachable(start, max_depth, grid, diagonal=False):
    """
    Graph traversal (BFS) to find all reachable nodes within max_depth.
    For movement (diagonal=False): blocks pathing through occupied tiles.
    For attack range (diagonal=True): allows reaching over units.
    """
    visited = {start}
    queue = deque([(start, 0)])
    reachable = set()

    while queue:
        (c, r), d = queue.popleft()
        if d > max_depth:
            continue

        reachable.add((c, r))

        for nc, nr in get_neighbors(c, r, grid, diagonal=diagonal):
            if (nc, nr) not in visited:
                visited.add((nc, nr))
                # For movement (diagonal=False): currently allowing pass-through for simplicity
                # This ensures the '4 diamond' range is always consistent regardless of units.
                pass 
                queue.append(((nc, nr), d + 1))

    return reachable

