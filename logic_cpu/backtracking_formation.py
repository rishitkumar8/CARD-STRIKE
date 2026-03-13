

"""
Backtracking + DP: Focus Fire Positioning Strategy.

Algorithm: BACKTRACKING over positions, DP for memoizing attack validity.

Goal: Find the tile that the CURRENT CPU unit should move to such that
      the MAXIMUM number of other CPU units can ALSO attack the SAME enemy.

This forces coordinated attacks — 2-3 units all hitting one enemy kills it
faster than spreading damage, which is the #1 strategic failure of naive AI.

How it works:
  1. DP Memoization — For each (cpu_unit, tile) pair, compute the set of
     enemy positions attackable from that tile. Cache result in dp_table.
     This avoids recomputing range checks for every backtracking branch.

  2. Backtracking — For the CURRENT unit (who is about to move), try every
     tile it can reach. For each candidate tile:
       a. Look up dp_table for the current unit at that tile.
       b. Look up dp_table for ALL OTHER CPU units at their CURRENT positions.
       c. Count the overlap — how many units share a common attackable target.
       d. Keep the tile with the highest focus-fire count.

Returns:
  (best_tile, focus_target, focus_count)
  best_tile    — where the current unit should move to
  focus_target — which enemy position to all attack
  focus_count  — how many CPU units can hit that target (including mover)

Time Complexity:
  DP build: O(U * T * E) — units × reachable_tiles × enemies (small constants)
  Backtracking: O(T) per unit — T = reachable tiles (bounded by move_range BFS)
"""

from game_grid import bfs_reachable, chebyshev_dist


def _build_dp_table(units_and_positions, enemy_positions, grid):
    """
    DP Step: For each (unit, tile) pair, build a set of attackable enemy positions.

    dp_table[(unit_idx, tile)] = frozenset of enemy_positions attackable from tile

    Memoized across all queries within the same turn to avoid redundant computation.
    """
    dp_table = {}

    for u_idx, (card, pos) in enumerate(units_and_positions):
        # Get all tiles this unit can reach (including current position)
        reachable = bfs_reachable(pos, card.move_range, grid, diagonal=False)
        reachable.add(pos)

        for tile in reachable:
            tc, tr = tile
            attackable = set()

            for e_pos in enemy_positions:
                ec, er = e_pos
                dist = chebyshev_dist(tc, tr, ec, er)

                # Check if any available attack can hit from this tile
                for atk in card.attacks:
                    if atk.current_cooldown > 0:
                        continue
                    is_heal = "heal" in atk.name.lower() or atk.is_healing
                    if is_heal:
                        continue
                    if dist <= atk.attack_range:
                        attackable.add(e_pos)
                        break  # At least one attack can hit — enough to confirm

            dp_table[(u_idx, tile)] = frozenset(attackable)

    return dp_table


def find_focus_fire_position(current_card, current_pos, other_cpu_units, enemy_positions, grid):
    """
    Main Focus Fire function.

    current_card, current_pos: The CPU unit about to move.
    other_cpu_units: List of (card, pos) for all OTHER cpu units (not moving).
    enemy_positions: List of enemy (col, row) positions.

    Returns: (best_tile, focus_target, focus_count)
             best_tile: where to move for max focus fire
             focus_target: which enemy to concentrate on
             focus_count: how many CPU units (including mover) can hit
    """
    if not enemy_positions:
        return current_pos, None, 0

    # All units = current + others (for DP build)
    all_units = [(current_card, current_pos)] + list(other_cpu_units)
    n_others = len(other_cpu_units)

    # DP Step: Build memoized attack-range table for all units
    dp_table = _build_dp_table(all_units, enemy_positions, grid)

    # Precompute what each OTHER unit can attack from their current position
    # (Other units are NOT moving, so only their current_pos matters)
    other_attackable = []
    for i, (card, pos) in enumerate(other_cpu_units):
        u_idx = i + 1  # index in all_units (0 = current mover)
        other_attackable.append(dp_table.get((u_idx, pos), frozenset()))

    # Backtracking over candidate tiles for the current unit
    reachable = bfs_reachable(current_pos, current_card.move_range, grid, diagonal=False)
    reachable.add(current_pos)

    best_tile = current_pos
    best_target = None
    best_focus_count = 0

    for tile in reachable:
        # Skip occupied tiles (other CPU units or player units)
        tc, tr = tile
        if tile != current_pos and grid.tiles[tc][tr].card is not None:
            continue

        # DP lookup: enemies the current unit can hit from this tile
        mover_attackable = dp_table.get((0, tile), frozenset())

        if not mover_attackable:
            continue

        # For each enemy the mover can hit, count how many other units ALSO hit it
        for e_pos in mover_attackable:
            focus_count = 1  # Mover counts as 1

            for other_atk_set in other_attackable:
                if e_pos in other_atk_set:
                    focus_count += 1

            if focus_count > best_focus_count:
                best_focus_count = focus_count
                best_target = e_pos
                best_tile = tile

    return best_tile, best_target, best_focus_count
