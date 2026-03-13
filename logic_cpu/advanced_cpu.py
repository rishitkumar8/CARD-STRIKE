"""
Advanced CPU Controller with Stealing Phase
Flow: Timing -> Steal Eval -> Greedy Deck -> Combat D&C -> Execute

Advanced CPU Turn Logic

Uses:
- Divide & Conquer for target reduction
- Greedy heuristics for movement and execution

Overall Time Complexity per turn:
O(p + r + a)
where:
p = number of players
r = reachable grid tiles
a = number of attacks
"""


import random
from game_grid import cell_center, chebyshev_dist
from animations import anim_mgr
from logic_attack import perform_attack_logic, decrement_cooldowns, process_turn_start_statuses

from logic_cpu.dc_combat import select_attack_target, select_position, select_attack_placement
from logic_cpu.backtracking_kill_confirm import solve_kill
from logic_cpu.dp_survival_prob import survive_probability
from logic_cpu.backtracking_formation import find_focus_fire_position
from logic_cpu.dp_matchup_matrix import optimize_matchups
from logic_attack import cell_center

current_turn = 0

def advanced_cpu_turn(grid):
    global current_turn
    current_turn += 1
    
    # Decrement enemy cooldowns at start of enemy turn
    decrement_cooldowns(grid, "enemy")
    process_turn_start_statuses(grid, "enemy")
    
    if anim_mgr.blocking:
        return

    # -----------------------------------------------------------------
    # PHASE 2: COMBAT PHASE (Strict Move OR Attack)
    # -----------------------------------------------------------------
    
    enemy_positions = []
    curr_player_positions = []
    
    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if card:
                if card.owner == "enemy":
                    enemy_positions.append((c,r))
                else:
                    curr_player_positions.append((c,r))

    # Evaluate best single action across all cards
    best_action = None
    best_score = -1
    
    # 0. MATCHUP DP: OPTIMAL HEALING ASSIGNMENT
    # Identify Healers and Patients
    healers = []
    patients = []
    
    for e_pos in enemy_positions:
        card = grid.tiles[e_pos[0]][e_pos[1]].card
        # Check if healer
        has_heal = False
        for atk in card.attacks:
            is_heal = ("heal" in atk.name.lower()) or ("Embrace" in atk.name) or atk.is_healing
            if is_heal and atk.current_cooldown == 0:
                has_heal = True
                break
        if has_heal:
            healers.append(card)
        if card.hp < card.max_hp:
            patients.append(card)
            
    healing_assignments = {} # Map healer_card -> patient_card
    
    if healers and patients:
        def heal_score(healer, patient):
            if healer == patient: return 10 # Self-heal low priority
            
            # Find positions
            h_pos = None
            p_pos = None
            for c in range(grid.cols):
                for r in range(grid.rows):
                    if grid.tiles[c][r].card == healer: h_pos = (c,r)
                    if grid.tiles[c][r].card == patient: p_pos = (c,r)
            
            if not h_pos or not p_pos: return 0
            
            dist = chebyshev_dist(h_pos[0], h_pos[1], p_pos[0], p_pos[1])
            gained = min(patient.max_hp - patient.hp, 20)
            
            # Prioritize LOW HP and being in range
            criticality = 1.0
            if patient.hp < patient.max_hp * 0.4: criticality = 5.0
            
            # Distance penalty
            dist_penalty = max(0, dist - 3) * 5
            
            return (gained * criticality) - dist_penalty

        _, assignments = optimize_matchups(healers, patients, heal_score)
        for h, p in assignments:
            healing_assignments[h] = p
            print(f"[Matchup] Assigned {h.name} to heal {p.name}")

    print(f"--- CPU TURN START (Turn {current_turn}) ---")
    print(f"CPU evaluating {len(enemy_positions)} units.")

    # -- PRE-COMPUTE: Debuff check + Focus Fire cache (once per turn) --
    any_debuffed = False
    try:
        from status_system import StatusType
        for p_pos in curr_player_positions:
            pc = grid.tiles[p_pos[0]][p_pos[1]].card
            if pc and any(
                e.type in (StatusType.WEAKEN, StatusType.VULNERABLE)
                for e in pc.active_effects
            ):
                any_debuffed = True
                break
    except Exception:
        pass

    # Build focus fire plan for each CPU unit (one pass, cached)
    focus_fire_cache = {}  # e_pos -> (best_tile, focus_target, focus_count)
    if not any_debuffed and len(enemy_positions) >= 2:
        for e_pos in enemy_positions:
            e_card_ff = grid.tiles[e_pos[0]][e_pos[1]].card
            if not e_card_ff:
                continue
            others = [(grid.tiles[p[0]][p[1]].card, p) for p in enemy_positions if p != e_pos]
            best_tile, f_target, f_count = find_focus_fire_position(
                e_card_ff, e_pos, others, curr_player_positions, grid
            )
            if f_count >= 2 and best_tile != e_pos:
                focus_fire_cache[e_pos] = (best_tile, f_target, f_count)

    for e_pos in enemy_positions:
        e_card = grid.tiles[e_pos[0]][e_pos[1]].card
        if not e_card: continue
        
        # 1. BACKTRACKING: KILL CONFIRM
        # Guard: only run if target is within max attack range (avoids n! backtracking on far targets)
        max_atk_range = max((a.attack_range for a in e_card.attacks if a.current_cooldown == 0), default=0)
        if max_atk_range > 0:
            for p_pos in curr_player_positions:
                dist_to_player = chebyshev_dist(e_pos[0], e_pos[1], p_pos[0], p_pos[1])
                if dist_to_player > max_atk_range:
                    continue  # Skip — clearly out of range, no need for backtracking
                p_card = grid.tiles[p_pos[0]][p_pos[1]].card
                if p_card and solve_kill(e_card, e_pos, p_card, p_pos, grid):
                    print(f"!!! KILL CONFIRMED: {e_card.name} can kill {p_card.name} !!!")
                    target_pos = p_pos
                    attack_obj = select_attack_placement(e_card, e_pos, target_pos, grid)
                    if attack_obj:
                        best_score = 9999
                        best_action = {
                            'type': 'ATTACK',
                            'card': e_card,
                            'pos': e_pos,
                            'target': target_pos,
                            'attack': attack_obj
                        }
                        break

        if best_score > 9000: break  # Kill found — stop evaluating other units

        # 1b. HEAL ASSIGNMENT EXECUTION
        if e_card in healing_assignments:
            patient = healing_assignments[e_card]
            # Find the healing attack
            heal_atk = None
            for atk in e_card.attacks:
                if ("heal" in atk.name.lower() or "Embrace" in atk.name or atk.is_healing) and atk.current_cooldown == 0:
                    heal_atk = atk
                    break
            
            if heal_atk:
                # Find patient pos
                p_pos = None
                for c in range(grid.cols):
                    for r in range(grid.rows):
                        if grid.tiles[c][r].card == patient:
                            p_pos = (c,r)
                            break
                if p_pos:
                     # Check range
                     hd = chebyshev_dist(e_pos[0], e_pos[1], p_pos[0], p_pos[1])
                     if hd <= heal_atk.attack_range:
                         heal_score = 200 # High priority
                         # Execute Heal
                         if heal_score > best_score:
                             best_score = heal_score
                             best_action = {
                                'type': 'ATTACK', # Uses attack logic for healing
                                'card': e_card,
                                'pos': e_pos,
                                'target': p_pos,
                                'attack': heal_atk
                             }
                             print(f"[Matchup] Executing Planned Heal on {patient.name}")

        # 2. FOCUS FIRE — served from pre-computed cache (computed before the loop)
        formation_move, focus_target, focus_count = focus_fire_cache.get(e_pos, (None, None, 0))
        if formation_move:
            print(f"[FocusFire] {e_card.name} -> {formation_move}, target={focus_target}, units={focus_count}")

        # --- OPTION A: ATTACK (from current position) ---
        target_pos = None
        if getattr(e_card, "stun_duration", 0) > 0:
            attack_score = -1
        else:
            target_pos = select_attack_target(e_card, e_pos, curr_player_positions, grid, prioritize_range=True)
        
        attack_obj = None
        attack_score = -1
        
        if target_pos:
            attack_obj = select_attack_placement(e_card, e_pos, target_pos, grid)
            if attack_obj:
                attack_score = attack_obj.dmg
                if attack_obj.element == "fire":
                    attack_score += 2

                t_card = grid.tiles[target_pos[0]][target_pos[1]].card
                if t_card:
                    # Killing blow bonus
                    if t_card.hp <= attack_obj.dmg:
                        attack_score += 50

                    # GREEDY: Big bonus for attacking debuffed targets
                    try:
                        from status_system import StatusType
                        for eff in t_card.active_effects:
                            if eff.type == StatusType.WEAKEN:
                                attack_score += 15  # Enemy hitting weakened: do it NOW
                            elif eff.type == StatusType.VULNERABLE:
                                attack_score += 20  # Vulnerable = more damage, priority
                        # Low HP bonus — finish them
                        if t_card.hp < t_card.max_hp * 0.4:
                            attack_score += 10
                    except Exception:
                        pass

            print(f"[{current_turn}] Eval ATTACK {e_card.name}: Score={attack_score}")
        
        if attack_score > best_score:
            best_score = attack_score
            best_action = {
                'type': 'ATTACK',
                'card': e_card,
                'pos': e_pos,
                'target': target_pos,
                'attack': attack_obj
            }
            print(f"[{current_turn}] New Best: ATTACK {e_card.name} (Score: {best_score})")

        # --- OPTION B: MOVE (no attack) ---
        if getattr(e_card, "root_duration", 0) > 0:
            move_score = -1
            new_pos = e_pos
        else:
            # MOVEMENT TARGET SELECTION
            if e_card in healing_assignments:
                # Healer moves towards patient
                patient = healing_assignments[e_card]
                p_pos = None
                for c in range(grid.cols):
                    for r in range(grid.rows):
                        if grid.tiles[c][r].card == patient:
                            p_pos = (c,r)
                            break
                move_target_pos = p_pos
                print(f"[CPU] {e_card.name} moving towards patient {patient.name}")
            else:
                move_target_pos = select_attack_target(e_card, e_pos, curr_player_positions, grid)
            
            new_pos = select_position(e_card, e_pos, move_target_pos, grid)

            # FOCUS FIRE OVERRIDE: If a better focus-fire tile exists, prefer it
            # BUT only if the unit cannot attack this turn anyway
            if formation_move and formation_move != e_pos:
                fc, fr = formation_move
                if grid.tiles[fc][fr].card is None or formation_move == e_pos:
                    new_pos = formation_move

            move_score = 0
            if new_pos != e_pos:
                move_score = 5  # Very low base — attack (12+) always beats this

                # DP: SURVIVAL CHECK — retreat if low HP
                if e_card.hp < e_card.max_hp * 0.4:
                    prob = survive_probability(e_card.hp, e_card.max_hp, 2, (10, 25))
                    if prob < 0.5:
                        move_score += 50  # Priority Retreat (overrides attack)
                        print(f"DP Survival Warn: {e_card.name} survival prob {prob:.2f} -> RETREAT")

                # Focus fire bonus: small tiebreaker only (max +10, never beats attack)
                if formation_move and new_pos == formation_move:
                    ff_bonus = min(10, 5 * max(0, focus_count - 1))
                    move_score += ff_bonus
                    print(f"[FocusFire] Tiebreaker bonus +{ff_bonus} ({focus_count} units on same target)")
        
        print(f"[{current_turn}] Eval MOVE {e_card.name} to {new_pos}: Score={move_score}")

        # Only register a MOVE action if the unit is actually changing position.
        # A score of 0 (stay in place) must NOT override a score of -1 attack.
        if new_pos != e_pos and move_score > best_score:
            best_score = move_score
            best_action = {
                'type': 'MOVE',
                'card': e_card,
                'pos': e_pos,
                'new_pos': new_pos
            }
            print(f"[{current_turn}] New Best: MOVE {e_card.name} (Score: {best_score})")

    # Execute the SINGLE best action
    if best_action:
        print(f"--- EXECUTING BEST ACTION ---")
        if best_action['type'] == 'MOVE':
            card = best_action['card']
            old_pos = best_action['pos']
            new_pos = best_action['new_pos']
            
            if old_pos == new_pos:
                print(f"[{card.name}] decided to stay at {old_pos}")
            else:
                print(f"CPU Action: MOVE {card.name} from {old_pos} to {new_pos}")
                
                # Helper for move animation callback
                def finalize_move(g=grid, old=old_pos, new=new_pos, c=card):
                    move_grid_card(g, old, new, c)
                    print(f"[DEBUG_MOVE] {c.name} moved from {old} to {new}")
                    
                anim_mgr.trigger_move_anim(
                    cell_center(*old_pos),
                    cell_center(*new_pos),
                    finalize_move
                )
                anim_mgr.add_floating_text(f"Moving {card.name}", cell_center(*new_pos)[0], cell_center(*new_pos)[1] - 40, (255, 255, 255))
            
        elif best_action['type'] == 'ATTACK':
            card = best_action['card']
            pos = best_action['pos']
            target = best_action['target']
            attack = best_action['attack']
            print(f"[{current_turn}] CPU Action: ATTACK {card.name} at {target} with {attack.name}")
            
            dist = chebyshev_dist(pos[0], pos[1], target[0], target[1])
            # Apply Cooldown
            attack.current_cooldown = attack.max_cooldown

            anim_mgr.trigger_attack_anim(
                cell_center(*pos),
                cell_center(*target),
                attack.element,
                lambda ep=pos, tp=target, atk=attack, g=grid, d=dist: perform_attack_logic(
                    ep[0], ep[1], tp[0], tp[1], atk, g, d
                )
            )
            anim_mgr.add_floating_text(f"Attacking!", cell_center(*pos)[0], cell_center(*pos)[1] - 40, (255, 50, 50))
    else:
        print("CPU found no valid actions.")

def move_grid_card(grid, old_pos, new_pos, card):
    if old_pos == new_pos:
        return
    grid.tiles[new_pos[0]][new_pos[1]].card = card
    grid.tiles[old_pos[0]][old_pos[1]].card = None
