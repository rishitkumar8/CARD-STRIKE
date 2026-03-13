import random
from config import GRID_COLS, GRID_ROWS, FPS
from game_grid import cell_center, chebyshev_dist
from effects import flame_tiles, regen_effects, burn_effects
from colors import E_FIRE, E_LEAF
from animations import anim_mgr
from status_system import (
    StatusType, create_flame_effect, create_frost_effect,
    create_regen_effect, create_shock_effect, create_thorns_effect,
    create_vulnerable_effect, create_weaken_effect, create_empower_effect
)

RARITY_MULT = {
    "normal": 1.0,
    "rare": 1.1,
    "epic": 1.25,
    "legendary": 1.5
}

# =====================================================
# ELEMENTAL ADVANTAGE TABLE
# Format: ELEMENT_ADVANTAGE[attacker_element][defender_element] = multiplier
# Strong matchup  = 1.5x damage
# Weak matchup    = 0.75x damage
# Neutral         = 1.0x damage
# Combined        = 1.1x vs everything (jack of all trades)
# =====================================================
#   fire  -> beats leaf  (burns plants)
#   leaf  -> beats water (absorbs water)
#   water -> beats fire  (extinguishes fire)
#   wind  -> beats leaf  (uproots plants)
#   null  -> beats wind  (void absorbs air)
# =====================================================
ELEMENT_ADVANTAGE = {
    "fire":     {"leaf": 1.5, "water": 0.75, "fire": 1.0, "wind": 1.0, "null": 1.0, "combined": 1.0},
    "water":    {"fire": 1.5, "leaf": 0.75, "water": 1.0, "wind": 1.0, "null": 1.0, "combined": 1.0},
    "leaf":     {"water": 1.5, "fire": 0.75, "leaf": 1.0, "wind": 0.75, "null": 1.0, "combined": 1.0},
    "wind":     {"leaf": 1.3, "null": 0.75, "wind": 1.0, "fire": 1.0, "water": 1.0, "combined": 1.0},
    "null":     {"wind": 1.3, "null": 1.0, "fire": 1.0, "water": 1.0, "leaf": 1.0, "combined": 1.0},
    "combined": {"fire": 1.1, "water": 1.1, "leaf": 1.1, "wind": 1.1, "null": 1.1, "combined": 1.0},
}

def get_element_multiplier(atk_element, def_element):
    """Get the elemental advantage multiplier for attack vs defender."""
    return ELEMENT_ADVANTAGE.get(atk_element, {}).get(def_element, 1.0)

def decrement_cooldowns(grid, owner):
    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if card and card.owner == owner:
                for atk in card.attacks:
                    if atk.current_cooldown > 0:
                        atk.current_cooldown -= 1




def process_turn_start_statuses(grid, owner):
    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if card and card.owner == owner:
                # Process New Status Effects
                expired = []
                for effect in card.active_effects:
                    # Apply DoT / HoT
                    if effect.type == StatusType.FLAME:
                        dmg = effect.value
                        card.hp -= dmg
                        anim_mgr.add_floating_text(f"-{dmg} FLAME", *cell_center(c, r), E_FIRE)
                    elif effect.type == StatusType.REGEN:
                        heal = effect.value
                        card.hp = min(card.max_hp, card.hp + heal)
                        anim_mgr.add_floating_text(f"+{heal} REGEN", *cell_center(c, r), E_LEAF)
                    
                    # Decrement Duration
                    if effect.decrement():
                        expired.append(effect)
                
                # Remove expired
                for e in expired:
                    card.active_effects.remove(e)
                    anim_mgr.add_floating_text(f"{e.name} END", *cell_center(c, r), (200, 200, 200))
                    
                # Check for death by DoT
                if card.hp <= 0:
                    grid.tiles[c][r].card = None
                    continue

                # Legacy Clean up (Optional: keep for backward compat if needed, or remove)
                # For now, we sync legacy fields for UI/AI that reads them directly
                has_burn = any(e.type == StatusType.FLAME for e in card.active_effects)
                card.burn_duration = 1 if has_burn else 0
                
                has_stun = any(e.type == StatusType.STUN for e in card.active_effects)
                card.stun_duration = 1 if has_stun else 0
                
                has_root = any(e.type == StatusType.ROOT for e in card.active_effects)
                card.root_duration = 1 if has_root else 0



def apply_effect_to_card(card, effect, c, r):
    # Check if effect already exists
    for e in card.active_effects:
        if e.type == effect.type:
            e.duration = max(e.duration, effect.duration) # Refresh
            return
    
    card.active_effects.append(effect)
    anim_mgr.add_floating_text(f"+{effect.name}", *cell_center(c, r), (255, 255, 0))



def perform_attack_logic(ac, ar, tc, tr, atk, grid, dist=0):
    # ------------------------------
    # RANGE SAFETY CHECK
    # ------------------------------
    # RANGE SAFETY CHECK
    # ------------------------------
    dist = chebyshev_dist(ac, ar, tc, tr)
    if dist > atk.attack_range:
        return

    attacker = grid.tiles[ac][ar].card
    target = grid.tiles[tc][tr].card
    if not attacker:
        return

    # ------------------------------
    # DAMAGE BASE CALCULATION
    # ------------------------------
    dmg_reduction = dist
    base_dmg = atk.dmg - dmg_reduction

    if target:
        MAX_HIT_DAMAGE = int(target.max_hp * 0.25)
        base_dmg = max(1, min(base_dmg, MAX_HIT_DAMAGE))

    # =====================================================
    # 1. Burning Trail (FIRE) — NO FRIENDLY DAMAGE
    # =====================================================
    if atk.name == "Burning Trail":
        dx = 1 if tc > ac else -1

        for i in range(1, 6):
            nc = ac + dx * i
            if grid.in_bounds(nc, ar):
                if not any(ft[0] == nc and ft[1] == ar for ft in flame_tiles):
                    flame_tiles.append([nc, ar, FPS * 3, attacker.owner])

        anim_mgr.add_floating_text("🔥 FIRE TRAIL", *cell_center(ac, ar), E_FIRE)

        # upfront hit only if opponent
        if target and target.owner != attacker.owner:
            dmg = max(1, int(base_dmg * 0.5))
            target.hp -= dmg
            target.flash_timer = 10
            anim_mgr.add_floating_text(f"-{dmg}", *cell_center(tc, tr), E_FIRE)

            if target.hp <= 0:
                grid.tiles[tc][tr].card = None
        return

    # =====================================================
    # 2. Nature’s Embrace (LEAF) — HEAL ONCE ONLY
    # =====================================================
    if atk.name == "Nature's Embrace":
        plus = [(tc,tr),(tc+1,tr),(tc-1,tr),(tc,tr+1),(tc,tr-1)]

        for (x, y) in plus:
            if grid.in_bounds(x,y) and grid.tiles[x][y].card:
                c = grid.tiles[x][y].card

                # 🟢 HEAL TEAM ONLY (ONCE)
                if c.owner == attacker.owner and not c.healed_once:
                    regen_effects.append([c, 5, FPS * 2, (x,y)])
                    c.healed_once = True
                    anim_mgr.add_floating_text("+HEAL", *cell_center(x,y), E_LEAF)

        return

    # =====================================================
    # 2. HEALING (Generalized)
    # =====================================================
    if atk.is_healing:
        heal_val = atk.heal_amount if atk.heal_amount > 0 else 20
        anim_mgr.add_floating_text(f"+{heal_val}", *cell_center(ac, ar), E_LEAF)
        
        attacker.hp = min(attacker.max_hp, attacker.hp + heal_val)
        attacker.heal_flash_timer = 20
        
        # Also heal allies within range? User said based on range.
        # "Ally heals: 18-22 HP with range 3-4"
        # If range > 0, check neighbors
        if atk.attack_range > 0:
             from game_grid import bfs_reachable
             reachable = bfs_reachable((ac, ar), atk.attack_range, grid, diagonal=True)
             for (rx, ry) in reachable:
                 if (rx, ry) == (ac, ar): continue
                 ally_card = grid.tiles[rx][ry].card
                 if ally_card and ally_card.owner == attacker.owner:
                     ally_card.hp = min(ally_card.max_hp, ally_card.hp + heal_val)
                     ally_card.heal_flash_timer = 20
                     anim_mgr.add_floating_text(f"+{heal_val}", *cell_center(rx, ry), E_LEAF)
        return

    # =====================================================
    # 2b. Generic Heal attacks - RESTORE HP
    # =====================================================
    is_heal = ("heal" in atk.name.lower()) or ("heal" in getattr(atk, 'animation', '').lower())
    if is_heal:
        heal_amount = atk.dmg
        healed_any = False

        # Heal ALL allies on the board (except the attacker)
        for gx in range(grid.cols):
            for gy in range(grid.rows):
                ally = grid.tiles[gx][gy].card
                if ally and ally.owner == attacker.owner:
                    ally_old = ally.hp
                    ally.hp = min(ally.max_hp, ally.hp + heal_amount)
                    ally_gained = ally.hp - ally_old
                    if ally_gained > 0:
                        ally.heal_flash_timer = 15
                        anim_mgr.add_floating_text(f"+{ally_gained} HP", *cell_center(gx, gy), E_LEAF)
                        healed_any = True

        if healed_any:
            anim_mgr.add_floating_text("HEAL!", *cell_center(ac, ar), E_LEAF)
        else:
            anim_mgr.add_floating_text("ALLIES FULL", *cell_center(ac, ar), E_LEAF)
        return

    # =====================================================
    # 3. LIFE DRAIN
    # =====================================================
    if atk.is_life_drain:
        base_drain_dmg = base_dmg  # Use capped damage, not raw atk.dmg
        base_heal = atk.heal_amount if atk.heal_amount > 0 else 15
        
        if target:
            target.hp -= base_drain_dmg
            target.flash_timer = 10
            print(f"[DEBUG_ATK] Life Drain {atk.name} dealt {base_drain_dmg} to {getattr(target, 'name', 'Unit')} (HP: {target.hp})")
            anim_mgr.add_floating_text(f"-{base_drain_dmg}", *cell_center(tc, tr), (200, 50, 200))
            if target.hp <= 0:
                grid.tiles[tc][tr].card = None
        
        attacker.hp = min(attacker.max_hp, attacker.hp + base_heal)
        attacker.heal_flash_timer = 15
        anim_mgr.add_floating_text(f"+{base_heal}", *cell_center(ac, ar), E_LEAF)
        return

    if target and target.owner != attacker.owner:
        base = base_dmg + random.randint(-2, 2)
        rarity_mult = RARITY_MULT.get(attacker.rarity, 1.0)
        elem_mult = get_element_multiplier(atk.element, getattr(target, 'element', 'null'))
        
        # 1. Apply Attacker Buffs/Debuffs
        atk_mod = 0
        for e in attacker.active_effects:
            if e.type == StatusType.WEAKEN:
                atk_mod -= e.value
            elif e.type == StatusType.EMPOWER:
                atk_mod += e.value
        
        dmg = int(base * rarity_mult * elem_mult) + atk_mod
        
        # 2. Apply Target Debuffs (Vulnerable)
        for e in target.active_effects:
            if e.type == StatusType.VULNERABLE:
                dmg += e.value
                anim_mgr.add_floating_text("VULNERABLE!", *cell_center(tc, tr), (255, 100, 100))

        if elem_mult > 1.0:
            print(f"[DEBUG_ELEM] {atk.element} vs {target.element} -> {elem_mult}x (SUPER EFFECTIVE)")
        elif elem_mult < 1.0:
            print(f"[DEBUG_ELEM] {atk.element} vs {target.element} -> {elem_mult}x (NOT VERY EFFECTIVE)")

        if target.shield > 0:
            absorbed = min(target.shield, dmg)
            target.shield -= absorbed
            dmg -= absorbed
            anim_mgr.add_floating_text(f"-{absorbed}🛡", *cell_center(tc,tr))

        if dmg > 0:
            target.hp -= dmg
            print(f"[DEBUG_ATK] {atk.name} dealt {dmg} to {getattr(target, 'name', 'Unit')} (HP: {target.hp}/{target.max_hp})")
            anim_mgr.add_floating_text(f"-{dmg}", *cell_center(tc,tr))
            
            # 3. Thorns Logic (Reflect Damage)
            for e in target.active_effects:
                if e.type == StatusType.THORNS:
                    reflect = e.value
                    attacker.hp -= reflect
                    anim_mgr.add_floating_text(f"-{reflect} THORNS", *cell_center(ac, ar), E_LEAF)

        target.flash_timer = 8
        
        # 4. Apply Elemental Status Effects (Probabilistic)
        if random.random() < 0.4: # 40% chance
            if atk.element == "fire":
                apply_effect_to_card(target, create_flame_effect(), tc, tr)
            elif atk.element == "water":
                if random.random() < 0.5:
                    apply_effect_to_card(target, create_frost_effect(), tc, tr)
                else:
                    apply_effect_to_card(target, create_weaken_effect(), tc, tr)
            elif atk.element == "wind":
                apply_effect_to_card(target, create_vulnerable_effect(), tc, tr)
            elif atk.element == "leaf":
                # Leaf attacks usually don't debuff enemies heavily, maybe Root?
                # User said "plant type attacks will have some buffs which cqn be used on allys"
                pass 

        # Legacy Status Application
        if atk.status_type != "none":
            # We map legacy strings to new system if possible
             if atk.status_type == "burn":
                 apply_effect_to_card(target, create_flame_effect(), tc, tr)
             elif atk.status_type == "stun":
                 apply_effect_to_card(target, create_shock_effect(), tc, tr)

        if target.hp <= 0:
            grid.tiles[tc][tr].card = None

    # =====================================================
    # 4. PLANT ALLY BUFF LOGIC
    # =====================================================
    elif target and target.owner == attacker.owner and atk.element == "leaf":
        # Buffing an ally
        apply_effect_to_card(target, create_regen_effect(), tc, tr)
        apply_effect_to_card(target, create_thorns_effect(), tc, tr)
        anim_mgr.add_floating_text("BUFFED!", *cell_center(tc, tr), E_LEAF)


def initiate_player_attack(player_idx, attack_idx, enemy_idx, grid):
    if anim_mgr.blocking:
        return None

    pc_pos = None
    ec_pos = None

    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            card = grid.tiles[c][r].card
            if card:
                if card.owner == "player" and card.index == player_idx:
                    pc_pos = (c,r)
                elif card.owner == "enemy" and card.index == enemy_idx:
                    ec_pos = (c,r)

    if not pc_pos:
        return False

    attacker = grid.tiles[pc_pos[0]][pc_pos[1]].card
    
    if getattr(attacker, "stun_duration", 0) > 0:
        anim_mgr.add_floating_text("STUNNED!", *cell_center(*pc_pos), (200, 200, 200))
        return False

    if attack_idx >= len(attacker.attacks):
        anim_mgr.add_floating_text("No Attack!", *cell_center(*pc_pos), (255, 100, 100))
        return False
    atk = attacker.attacks[attack_idx]

    # Check if this is a healing/support ability that doesn't need an enemy
    # We check name, is_healing flag, and also animation name (e.g. "heal_aura")
    anim_name = getattr(atk, 'animation', '') or ''
    is_heal_atk = (
        atk.is_healing 
        or ("heal" in atk.name.lower()) 
        or ("embrace" in atk.name.lower())
        or ("heal" in anim_name.lower())
    )
    
    # If it's a heal, we target ourselves if no enemy is selected
    if is_heal_atk:
        # For healing, we don't need a specific enemy. Target self effectively.
        ec_pos = pc_pos 

    if not ec_pos:
        # If still no target (and not a self-cast heal), fail
        return False

    if atk.current_cooldown > 0:
        anim_mgr.add_floating_text(
            f"COOLDOWN {atk.current_cooldown}!",
            *cell_center(*pc_pos),
            (200, 50, 50)
        )
        return False

    # Only check range if it's NOT a self-cast/heal
    if not is_heal_atk:
        from game_grid import bfs_reachable
        reachable = bfs_reachable(pc_pos, atk.attack_range, grid, diagonal=True)

        if ec_pos not in reachable:
            anim_mgr.add_floating_text(
                "OUT OF RANGE!",
                *cell_center(*pc_pos),
                (255,180,0)
            )
            return False

    # Get animation type from attack
    anim_type = getattr(atk, 'animation', None)
    if anim_type is None:
        # Fallback based on element
        anim_type = f"projectile_{atk.element}" if atk.element != "null" else "beam_null"

    # Heal attacks: animation targets self instead of enemy
    anim_target = cell_center(*pc_pos) if is_heal_atk else cell_center(*ec_pos)

    # Apply Cooldown
    atk.current_cooldown = atk.max_cooldown

    anim_mgr.trigger_attack_anim(
        cell_center(*pc_pos),
        anim_target,
        atk.element,
        lambda: perform_attack_logic(
            pc_pos[0], pc_pos[1],
            ec_pos[0], ec_pos[1],
            atk, grid
        ),
        anim_type=anim_type
    )

    return True
