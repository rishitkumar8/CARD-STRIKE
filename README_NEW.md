# Marve-Strike: Advanced Algorithmic AI & Mechanics Update

## 1. Executive Summary
This update transforms **Marve-Strike** from a simple card battler into a sophisticated strategy game powered by advanced Computer Science concepts. We have integrated **5 Backtracking** and **5 Dynamic Programming** algorithms to drive CPU decision-making, ensuring that every move is mathematically grounded rather than random. Additionally, a robust **Status Effect System** (Buffs/Debuffs) has been added to deepen combat mechanics.

---

## 2. New Game Mechanics: Status Effects
*Decision Rationale: To move beyond simple "damage trading," we introduced persistent effects that reward planning and synergy.*

### 2.1 The Status System Architecture
We implemented a flexible `StatusEffect` class and integrated it into the `Card` dataclass. This allows any unit to carry multiple effects simultaneously.

- **Flame (Fire Debuff)**: Deals **2 DMG/turn** for 2 rounds.
  - *Why?* Punishes enemies for staying in combat too long.
- **Frost (Water Debuff)**: **-1 Movement Range** (Concept).
  - *Why?* Allows kiting strategies (Water units are ranged).
- **Regen (Plant Buff)**: Heals **2 HP/turn** for 3 rounds.
  - *Why?* Gives Plant units a "Tank/Support" identity.
- **Thorns (Plant Buff)**: **Reflects** damage back to attacker.
  - *Why?* discourages mindless aggression against tanks.
- **Vulnerable (Wind Debuff)**: Increases incoming damage.
  - *Why?* Enables "Combo" plays (Set up with Wind -> Finish with Fire).

---

## 3. Algorithmic Upgrades: 5 Backtracking Implementations
*Backtracking is used when we need to explore "what if" scenarios to find a guaranteed solution.*

### 3.1 Kill Confirmation ("Mate-in-1")
- **File:** `logic_cpu/backtracking_kill_confirm.py`
- **What it does:** Before moving, the CPU simulates every combination of its available attacks against an adjacent enemy.
- **Why Backtracking?** Heuristics can fail (e.g., they might ignore a "Vulnerable" debuff that makes a weaker attack lethal). Backtracking guarantees that if a kill is possible, the CPU finds it.
- **Impact:** The CPU is now ruthless. If you are low on HP, it *will* calculate the exact sequence to eliminate you.

### 3.2 Complex Pathfinding (Paths of Exact Length K)
- **File:** `logic_cpu/backtracking_pathing.py`
- **What it does:** Finds all valid paths of exactly $K$ steps.
- **Why Backtracking?** Standard BFS finds the *shortest* path. Backtracking finds *all* paths, allowing the CPU to plan complex flanking maneuvers or collect bonuses on specific tiles (future proofing).

### 3.3 Attack Sequence Optimization
- **File:** `logic_cpu/backtracking_sequence.py`
- **What it does:** Determines the order of attacks (e.g., Attack A then B vs B then A) to maximize damage.
- **Why Backtracking?** Order matters due to status effects. (e.g., applying "Weakness" first reduces retaliation). Permutations are small ($n!$ for $n=3$ is 6), making backtracking the perfect lightweight solver.

### 3.4 Deck Subset Selection (Stealing Phase)
- **File:** `logic_cpu/backtracking_deck_subset.py`
- **What it does:** Solves the **Subset Sum Problem**. Identifies which combination of cards in the draft pool sums up to a specific stat target (e.g., "Need exactly 50 Total HP").
- **Why Backtracking?** It ensures the CPU drafts a mathematically balanced deck rather than just greedy picking high-stat cards.

### 3.5 Formation Validation
- **File:** `logic_cpu/backtracking_formation.py`
- **What it does:** Checks if units can move to form specific geometric shapes (e.g., Triangle Formation for defense).
- **Why Backtracking?** It tests combinatorial movement options ($Move(U1) \times Move(U2) \times Move(U3)$) to validate a coordinated team strategy.

---

## 4. Algorithmic Upgrades: 5 Dynamic Programming Implementations
*Dynamic Programming is used to solve optimization problems by breaking them into overlapping subproblems.*

### 4.1 Survival Probability Calculation
- **File:** `logic_cpu/dp_survival_prob.py`
- **What it does:** Calculates the probability $P(Survival)$ over $T$ turns given stochastic enemy damage.
- **Why DP?** The state space (HP remaining) overlaps. $DP(HP, t)$ depends on $DP(HP-dmg, t-1)$. Memoization creates a highly efficient lookup table for risk assessment.
- **Impact:** The CPU now "knows fear." It retreats when the math says survival probability is low (< 50%).

### 4.2 Damage Maximization (Knapsack Problem)
- **File:** `logic_cpu/dp_knapsack_damage.py`
- **What it does:** Given an abstract "Energy" or "Cooldown" limit, selects the set of attacks that yields maximum damage.
- **Why DP?** This is the classic **0/1 Knapsack Problem**. Greedy approaches fail here; DP guarantees the optimal loadout.

### 4.3 Minimum Cost Pathfinding
- **File:** `logic_cpu/dp_min_cost_path.py` (and `_k_steps`)
- **What it does:** Finds movement paths that minimize "Danger Cost" (e.g., moving through Fire Tiles costs 5, Empty costs 1).
- **Why DP?** Standard shortest-path ignores tile danger. DP calculates the min-cost accumulation step-by-step, allowing the CPU to smartly navigate hazards.

### 4.4 Matchup Optimization (Bitmask DP)
- **File:** `logic_cpu/dp_matchup_matrix.py`
- **What it does:** Assigns attackers to targets to maximize total team effectiveness.
- **Why DP?** Solves the Assignment Problem for small $N$. Using a bitmask state $DP(mask)$ represents the set of occupied targets, ensuring no two attackers over-kill the same target inefficiently.

### 4.5 Resource Allocation
- **File:** `logic_cpu/dp_resource_allocation.py`
- **What it does:** Distributes specific resources (like shared healing or limited "moves") across units to maximize global utility.
- **Why DP?** Solves the **Unbounded Knapsack** / Resource Allocation problem, ensuring optimal team economy.

---

## 5. Integration: The Advanced CPU Logic
All these components come together in `logic_cpu/advanced_cpu.py`.

1. **Turn Start**: The status system processes DOT/HOT effects.
2. **Phase 1 (Aggression)**: The **Backtracking Kill Confirm** runs. If a kill is detected, the CPU skips complex planning and executes the kill immediately.
3. **Phase 2 (Survival)**: Strategies are weighted by the **DP Survival Probability**. If the CPU detects high risk, it switches to defensive positioning.
4. **Phase 3 (Optimization)**: If no kill is imminent, it uses **Divide & Conquer** (existing) and **Greedy** heuristics (existing) refined by the new status effects (e.g., favoring Vulnerable targets).

This multi-layered AI architecture makes Marve-Strike a premier example of applied algorithmic game theory.
