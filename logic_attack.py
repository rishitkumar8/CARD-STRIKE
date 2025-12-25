import random
from config import GRID_COLS, GRID_ROWS, FPS
from grid import cell_center
from effects import flame_tiles, regen_effects, burn_effects
from colors import E_FIRE, E_LEAF
from animations import anim_mgr

RARITY_MULT = {
    "normal": 1.0,
    "rare": 1.1,
    "epic": 1.25,
    "legendary": 1.5
}


def perform_attack_logic(ac, ar, tc, tr, atk, grid, dist=0):
    # HARD SAFETY CHECK — NEVER ALLOW OUT-OF-RANGE ATTACKS
    from grid import bfs_reachable

    dist = abs(ac - tc) + abs(ar - tr)
    if dist > atk.attack_range:
        return



    attacker = grid.tiles[ac][ar].card
    target = grid.tiles[tc][tr].card

    # Calculate distance-based damage reduction
    if dist == 0:
        dist = abs(ac - tc) + abs(ar - tr)
    dmg_reduction = dist
    base_dmg = atk.dmg - dmg_reduction

    # Clamp damage so enemies never get one-shot
    MAX_HIT_DAMAGE = int(target.max_hp * 0.25) if target else atk.dmg
    base_dmg = max(1, min(base_dmg, MAX_HIT_DAMAGE))


    # =====================================================
    # 1. Burning Trail (FIRE)
    # =====================================================
    if atk.name == "Burning Trail":
        # Direction of trail
        dx = 1 if tc > ac else -1

        # Create burning tiles (area denial)
        for i in range(1, 6):
            nc = ac + dx * i
            if grid.in_bounds(nc, ar):
                # Avoid stacking same tile infinitely
                if not any(ft[0] == nc and ft[1] == ar for ft in flame_tiles):
                    flame_tiles.append([nc, ar, FPS * 3, attacker.owner])  # 3 seconds

        anim_mgr.add_floating_text("🔥 FIRE TRAIL", *cell_center(ac, ar), E_FIRE)

        # Reduced upfront damage (trail is main threat)
        if target:
            dmg = max(1, int(base_dmg * 0.5))
            target.hp -= dmg
            target.flash_timer = 10

            cx, cy = cell_center(tc, tr)
            anim_mgr.add_floating_text(f"-{dmg}", cx, cy - 10, E_FIRE)

            if target.hp <= 0:
                grid.tiles[tc][tr].card = None

        return


    # =====================================================
    # 2. Nature’s Embrace (LEAF)
    # =====================================================
    if atk.name == "Nature's Embrace":
        plus = [(tc, tr), (tc + 1, tr), (tc - 1, tr), (tc, tr + 1), (tc, tr - 1)]
        for (x, y) in plus:
            if grid.in_bounds(x, y) and grid.tiles[x][y].card:
                c = grid.tiles[x][y].card
                if c.owner == attacker.owner:
                    regen_effects.append([c, 5, FPS * 3, (x, y)])
                    c.heal_flash_timer = 12   # ⭐ ADD
                    anim_mgr.add_floating_text("+HEAL", *cell_center(x, y), E_LEAF)
                else:
                    burn_effects.append([c, 10, FPS * 2, (x, y)])
                    anim_mgr.add_floating_text("-THORN", *cell_center(x, y), (0, 255, 0))
        # Also damage the target
        # Apply only ONE direct hit; effects handle rest over time
        if target:
            dmg = max(1, int(base_dmg * 0.6))  # reduced upfront damage
            target.hp -= dmg
            target.flash_timer = 10
            cx, cy = cell_center(tc, tr)
            anim_mgr.add_floating_text(f"-{dmg}", cx, cy - 10)

            if target.hp <= 0:
                grid.tiles[tc][tr].card = None

                return

    # =====================================================
    # 3. Fusion Attack
    # =====================================================
    if atk.name == "Burning-Embrace Fusion":
        around = [
            (tc + 1, tr), (tc - 1, tr), (tc, tr + 1), (tc, tr - 1),
            (tc + 1, tr + 1), (tc - 1, tr - 1), (tc + 1, tr - 1), (tc - 1, tr + 1)
        ]
        for (x, y) in around:
            if grid.in_bounds(x, y) and grid.tiles[x][y].card:
                c = grid.tiles[x][y].card
                if c.owner == attacker.owner:
                    regen_effects.append([c, 5, FPS * 2, (x, y)])
                    anim_mgr.add_floating_text("+FUSION HEAL", *cell_center(x, y), E_LEAF)
                else:
                    burn_effects.append([c, 10, FPS * 2, (x, y)])
                    anim_mgr.add_floating_text("-FUSION FIRE", *cell_center(x, y), E_FIRE)
        # Also damage the target
        if target:
            dmg = base_dmg + random.randint(-2, 2)
            target.hp -= dmg
            target.flash_timer = 10
            cx, cy = cell_center(tc, tr)
            anim_mgr.add_floating_text(f"-{dmg}", cx, cy - 10)
            if target.hp <= 0:
                grid.tiles[tc][tr].card = None
        return

    # =====================================================
    # 4. Normal Attack (WITH SHIELD)
    # =====================================================
    if target:
        base = atk.dmg + random.randint(-2, 2)
        mult = RARITY_MULT.get(attacker.rarity, 1.0)
        dmg = int(base * mult)

        # 🛡️ SHIELD ABSORPTION
        if target.shield > 0:
            absorbed = min(target.shield, dmg)
            target.shield -= absorbed
            dmg -= absorbed
            anim_mgr.add_floating_text(f"-{absorbed}🛡", *cell_center(tc, tr))

        # ❤️ APPLY REMAINING DAMAGE
        if dmg > 0:
            target.hp -= dmg
            # ------------------------------
            # CPU retaliation memory
            # ------------------------------
            if target.owner == "enemy":
                from logic_cpu.cpu_controller import (
                    last_attacked_enemy,
                    last_attacked_turn,
                    current_turn
                )
                last_attacked_enemy = (tc, tr)
                last_attacked_turn = current_turn

            anim_mgr.add_floating_text(f"-{dmg}", *cell_center(tc, tr))

        # ⚡ HIT FLASH
        target.flash_timer = 8

        if target.hp <= 0:
            grid.tiles[tc][tr].card = None



def initiate_player_attack(player_idx, attack_idx, enemy_idx, grid):
    if anim_mgr.blocking:
        return None

    # Locate player
    pc_pos = None
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            card = grid.tiles[c][r].card
            if card and card.owner == "player" and card.index == player_idx:
                pc_pos = (c, r)
                break

    # Locate enemy
    ec_pos = None
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            card = grid.tiles[c][r].card
            if card and card.owner == "enemy" and card.index == enemy_idx:
                ec_pos = (c, r)
                break

    if pc_pos and ec_pos:
        attacker = grid.tiles[pc_pos[0]][pc_pos[1]].card
        atk = attacker.attacks[attack_idx]

        # ---------------------------------
        # ATTACK RANGE CHECK (OUT OF RANGE)
        # ---------------------------------
        from grid import bfs_reachable

        reachable = bfs_reachable(pc_pos, atk.attack_range, grid)

        if ec_pos not in reachable:
            anim_mgr.add_floating_text(
                "OUT OF RANGE!",
                *cell_center(*pc_pos),
                (255, 180, 0)
            )
            return False


        start = cell_center(*pc_pos)
        end = cell_center(*ec_pos)

        anim_mgr.trigger_attack_anim(
            start, end, atk.element,
            lambda: perform_attack_logic(
                pc_pos[0], pc_pos[1],
                ec_pos[0], ec_pos[1],
                atk, grid
            )
        )
        return True  # Signals CPU turn ready

    return False
