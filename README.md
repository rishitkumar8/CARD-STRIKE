# Marve-Strike: AI Card Game — Algorithm Documentation

## 1. Project Overview
**Marve-Strike** is a strategic card battler where players draft a deck of elemental heroes and battle on a grid. The core highlight of this project is its **Advanced AI (CPU)**, which uses fundamental algorithm design strategies—**Divide & Conquer**, **Greedy Algorithms**, and **Graph Traversal (BFS)**—to make intelligent, efficient decisions in real-time.

---

## 2. Game Phases & Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  STEALING PHASE  │────▶│  PLACEMENT PHASE  │────▶│   COMBAT PHASE   │
│  (Draft 3 cards) │     │  (Place on grid)  │     │  (Move OR Attack)│
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

### Stealing Phase
Each player starts with 5 random cards. Players take turns choosing to **STEAL** a card from the opponent's hand OR **RETAIN** a card from their own hand. This continues until both players have a deck of exactly 3 cards.

### Placement Phase
Player clicks on grid cells to place their 3 cards. CPU cards are placed randomly on available tiles.

### Combat Phase
Turn-based tactical combat. Each turn, a unit can **MOVE *or* ATTACK** (not both). The CPU uses advanced algorithms (described below) to decide the optimal action each turn.

---

## 3. Complete Algorithm Catalog

### Summary Table

| # | Algorithm | Type | File | Function | Time Complexity | Space Complexity |
|---|-----------|------|------|----------|----------------|------------------|
| 1 | Steal Target Selection | Divide & Conquer | `logic_cpu/dc_steal.py` | `select_steal_target()` | O(N) | O(N) |
| 2 | DAC-MAX (Recursive Maximum) | Divide & Conquer | `logic_cpu/dc_steal.py` | `dac_max()` | O(N) | O(log N) |
| 3 | Retain Card Selection | Divide & Conquer | `logic_cpu/dc_retain.py` | `select_best_retain()` | O(N) | O(log N) |
| 4 | CPU Turn Action Selection | Divide & Conquer | `stealing_phase.py` | `cpu_turn()` | O(N) | O(1) |
| 5 | Attack Target Selection | Divide & Conquer | `logic_cpu/dc_combat.py` | `select_attack_target()` | O(P) | O(log P) |
| 6 | Position Selection (Movement) | Divide & Conquer | `logic_cpu/dc_combat.py` | `select_position()` | O(R) | O(log R) |
| 7 | Attack Placement (Best Attack) | Divide & Conquer | `logic_cpu/dc_combat.py` | `select_attack_placement()` | O(A) | O(log A) |
| 8 | Greedy Target Selection | Greedy | `logic_cpu/greedy_target_weakest.py` | `greedy_best_target()` | O(P) | O(1) |
| 9 | Greedy Movement | Greedy | `logic_cpu/greedy_move.py` | `greedy_nearest_move()` | O(R × P) | O(R) |
| 10 | BFS Reachability | Graph Traversal (BFS) | `game_grid.py` | `bfs_reachable()` | O(V + E) | O(V) |
| 11 | CPU Combat Orchestrator | Greedy (Best-of-All) | `logic_cpu/advanced_cpu.py` | `advanced_cpu_turn()` | O(E × (P + R + A)) | O(P + R) |

> **N** = cards in hand (~5), **P** = player units (~3), **R** = reachable tiles (~12), **A** = attacks per card (~3), **E** = enemy units (~3), **V** = grid vertices, **E(graph)** = grid edges

---

## 4. Detailed Algorithm Descriptions

---

### 4.1 Divide & Conquer Algorithms

---

#### 4.1.1 Steal Target Selection — `select_steal_target()`

**File:** `logic_cpu/dc_steal.py`
**Called From:** `stealing_phase.py` → `StealingPhase.cpu_turn()` (line 452)

**Problem:** During the Stealing Phase, the CPU must choose the single best card to steal from the player's hand, considering card strength AND element diversity in its own deck.

**Algorithm: Grouped Divide & Conquer (DAC-MAX)**

```
DIVIDE:   Partition candidate cards by ELEMENT (semantic grouping)
          e.g., {fire: [card1, card5], water: [card2], leaf: [card3, card4]}

CONQUER:  Within each element group, recursively find the strongest card
          using dac_max() (Tournament-style pairwise comparison)

COMBINE:  Compare group winners using CONTEXT-AWARE utility scoring
          (accounts for element redundancy in CPU's existing deck)
```

**Scoring Heuristic (`evaluate_card`):**
```
score = HP + Σ(damage + range×2 − cooldown×3) + healing_bonus + life_drain_bonus
```

**Context-Aware Utility (`compute_utility`):**
```
utility = evaluate_card(card) − (same_element_count_in_deck × 6)
```
This penalizes picking cards of elements the CPU already has, promoting deck diversity.

**Time Complexity:** **O(N)** — Each card is evaluated exactly once across all groups.
**Space Complexity:** **O(N)** — For the element groups dictionary.

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **Grouped D&C (Used)** | **O(N)** | ✅ Best for "Best-in-Class" logic with element-aware comparison |
| Linear Scan | O(N) | Faster constant factor, but lacks element grouping insight |
| Sorting | O(N log N) | Overkill; we only need the top 1 card |

**Verdict:** ✅ **Optimal.** Grouped D&C is ideal because it naturally handles the two-level decision (best within element, then best overall with context).

---

#### 4.1.2 DAC-MAX — `dac_max()`

**File:** `logic_cpu/dc_steal.py`
**Called From:** `logic_cpu/dc_steal.py` → `select_steal_target()` (line 110) — used to find the best card within each element group.
Also used inline in `stealing_phase.py` → `StealingPhase.cpu_turn()` (line 499) — to compare STEAL vs SWAP vs RETAIN actions.

**Algorithm: Recursive Maximum Selection**
```
BASE CASE:  If list has 1 element → return it
DIVIDE:     Split list into left and right halves
CONQUER:    Recursively find max of each half
COMBINE:    Return the one with higher evaluate_card() score
```

**Recurrence:** T(N) = 2T(N/2) + O(1)
**Time Complexity:** **O(N)** (Master Theorem Case 1: a=2, b=2, f(n)=O(1), so O(n^log₂2) = O(n))
**Space Complexity:** **O(log N)** — recursion stack depth

---

#### 4.1.3 Retain Card Selection — `select_best_retain()`

**File:** `logic_cpu/dc_retain.py`
**Called From:** `stealing_phase.py` → `StealingPhase.cpu_turn()` (line 480)

**Problem:** Select the best card to RETAIN (keep) from the CPU's current hand.

**Algorithm: Recursive Divide & Conquer**
```
BASE CASE:  0 cards → None; 1 card → return it
DIVIDE:     Split hand indices into two halves
CONQUER:    Recursively find best retain candidate in each half
COMBINE:    Compare candidates using evaluate_retain_value()
```

**Retention Scoring (`evaluate_retain_value`):**
```
score = HP × 0.5
      + max(damage − cooldown×2) × 2   ← reliability-weighted attack strength
      + healing_bonus(15) + status_bonus(10)
      + fire/combined_bonus(5)
```
Key difference from steal scoring: **penalizes high cooldowns more heavily** (reliability is crucial for cards you keep).

**Recurrence:** T(N) = 2T(N/2) + O(1)
**Time Complexity:** **O(N)**
**Space Complexity:** **O(log N)** — recursion stack

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **Recursive D&C (Used)** | **O(N)** | ✅ Matches combat D&C structure; easy to extend scoring |
| Linear Scan (Greedy) | O(N) | Same complexity, simpler but less modular |
| Sorting | O(N log N) | Overkill for finding 1 best card |

**Verdict:** ✅ **Optimal** for this problem size and extensibility requirements.

---

#### 4.1.4 CPU Turn Action Selection (Stealing Phase) — `cpu_turn()`

**File:** `stealing_phase.py`
**Called From:** `main.py` (via `pygame.USEREVENT + 1` timer event, line 197)

**Problem:** Each CPU turn in the stealing phase must decide between 3 independent actions: STEAL, SWAP, or RETAIN.

**Algorithm: Meta-Level Divide & Conquer**
```
DIVIDE:     Define 3 independent subproblems:
            ├── Subproblem 1: STEAL  → uses select_steal_target() [D&C]
            ├── Subproblem 2: SWAP   → compare best player card vs worst CPU card
            └── Subproblem 3: RETAIN → uses select_best_retain() [D&C]

CONQUER:    Solve each subproblem independently (compute score for each action)

COMBINE:    Use inline dac_max() to find the action with the highest score
```

**Time Complexity:** **O(N)** — dominated by card evaluation across all 3 subproblems.

---

#### 4.1.5 Attack Target Selection — `select_attack_target()`

**File:** `logic_cpu/dc_combat.py`
**Called From:** `logic_cpu/advanced_cpu.py` → `advanced_cpu_turn()`:
  - Line 74: `select_attack_target(..., prioritize_range=True)` — for ATTACK evaluation (only targets within attack range)
  - Line 108: `select_attack_target(...)` — for MOVE evaluation (all targets, to decide move direction)

**Problem:** Select the single best enemy to target, considering HP, distance, and threat.

**Algorithm: Recursive Divide & Conquer with Optional Range Pre-filter**
```
PRE-FILTER: If prioritize_range=True, filter candidates to only those
            within the attacker's maximum attack range (Chebyshev distance).

BASE CASE:  0 targets → None; 1 target → return it
DIVIDE:     Split candidate list into two halves
CONQUER:    Recursively find best target in each half
COMBINE:    Compare using get_target_score() heuristic
```

**Target Scoring (`get_target_score`):**
```
score = hp_factor × 10        ← prefer LOW HP targets (kill potential)
      + dist_factor × 5       ← prefer CLOSER targets (1/distance)
      + threat × 0.3          ← prefer HIGH DAMAGE enemies (eliminate threats)

where:
  hp_factor = 1 − (current_hp / max_hp)    // 0.0 (full) to 1.0 (nearly dead)
  dist_factor = 1 / max(manhattan_dist, 1)  // closer = higher
  threat = max attack damage of the target
```

**Time Complexity:** **O(P)** where P = number of player units
**Space Complexity:** **O(log P)** — recursion depth

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **Recursive D&C (Used)** | **O(P)** | ✅ Tournament-style; modular comparison in `compare_targets()` |
| Brute Force (Nested Loop) | O(P²) | Too slow and unnecessary |
| Priority Queue (Heap) | O(P) build | Good for ranked lists, overkill for single best |

**Verdict:** ✅ **Optimal.** The tournament-tree approach cleanly separates scoring logic from search logic.

---

#### 4.1.6 Position Selection — `select_position()`

**File:** `logic_cpu/dc_combat.py`
**Called From:** `logic_cpu/advanced_cpu.py` → `advanced_cpu_turn()` (line 109) — for MOVE evaluation

**Problem:** Find the best tile to move to from all reachable, **unoccupied** tiles.

**Algorithm: Recursive Divide & Conquer on Filtered BFS Results**
```
STEP 1:     BFS to find all reachable tiles within move_range
STEP 2:     Filter to EMPTY tiles only (or current position)
            — prevents moving onto occupied tiles

BASE CASE:  0 tiles → None; 1 tile → return it
DIVIDE:     Split reachable tile list into two halves
CONQUER:    Recursively find best tile in each half
COMBINE:    Compare using Manhattan distance to target position
            (closer to target = better)
```

**Time Complexity:** **O(R)** where R = number of reachable tiles (bounded by move_range²)
**Space Complexity:** **O(log R)** — recursion depth

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **Recursive D&C (Used)** | **O(R)** | ✅ Good for small R (move_range ≤ 3 → R ≤ ~12) |
| BFS (for actual pathfinding) | O(V+E) | Better for navigating around obstacles; already used upstream |
| A* Search | O(E log V) | Industry standard for long-range; overkill for short-range tactics |
| Linear Scan | O(R) | Same complexity, simpler constant factor |

**Verdict:** ✅ **Acceptable.** For small R values (tactical movement of 2-3 tiles), D&C performs well. For production-scale 100×100 grids, A* would be strictly better.

---

#### 4.1.7 Attack Placement (Element-Aware) — `select_attack_placement()`

**File:** `logic_cpu/dc_combat.py`
**Called From:** `logic_cpu/advanced_cpu.py` → `advanced_cpu_turn()` (line 80) — for ATTACK evaluation

**Problem:** Choose the strongest available attack that can hit the target, **factoring in elemental advantage** against the target's element.

**Elemental Advantage Table** (defined in `logic_attack.py`):
```
Attacker ↓ / Defender →  | fire  | water | leaf  | wind  | null  | combined
─────────────────────────┼───────┼───────┼───────┼───────┼───────┼─────────
fire                     │ 1.0   │ 0.75  │ 1.5   │ 1.0   │ 1.0   │ 1.0
water                    │ 1.5   │ 1.0   │ 0.75  │ 1.0   │ 1.0   │ 1.0
leaf                     │ 0.75  │ 1.5   │ 1.0   │ 0.75  │ 1.0   │ 1.0
wind                     │ 1.0   │ 1.0   │ 1.3   │ 1.0   │ 0.75  │ 1.0
null                     │ 1.0   │ 1.0   │ 1.0   │ 1.3   │ 1.0   │ 1.0
combined                 │ 1.1   │ 1.1   │ 1.1   │ 1.1   │ 1.1   │ 1.0
```

**Algorithm: Filter + Recursive D&C with Element-Aware Scoring**
```
STEP 0:     Look up the target card's element from the grid

FILTER:     Remove attacks that are:
            − On cooldown (current_cooldown > 0)
            − Out of range (Chebyshev distance > attack_range)
            − Healing abilities (CPU should not waste heal slots offensively)

BASE CASE:  0 attacks → None; 1 attack → return it
DIVIDE:     Split valid attacks into two halves
CONQUER:    Recursively find strongest in each half
COMBINE:    Compare using get_attack_score() (element-aware)
```

**Attack Scoring (`get_attack_score`):**
```
score = attack.dmg × ELEMENT_ADVANTAGE[attack.element][target.element]

Example: CPU has fire attack (dmg=20) and water attack (dmg=25)
         Target is a LEAF element unit
         
         fire vs leaf:  20 × 1.5  = 30.0   ← CPU picks this (SUPER EFFECTIVE)
         water vs leaf: 25 × 0.75 = 18.75
```

**Time Complexity:** **O(A)** where A = number of attacks per card (~3)
**Space Complexity:** **O(log A)** — recursion depth

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **Recursive D&C (Used)** | **O(A)** | ✅ Reusable framework; element-aware comparison in `get_attack_score()` |
| Decision Tree (Rule-based) | O(1) | Faster but rigid and hard to maintain |
| Monte Carlo Tree Search | Exponential | Simulates future turns; too slow for this scope |

**Verdict:** ✅ **Optimal for extensibility.** A=3 makes any algorithm trivial, but D&C provides a clean framework for future expansion. The element-aware scoring makes the CPU significantly smarter.

---

### 4.2 Greedy Algorithms

---

#### 4.2.1 Greedy Target Selection — `greedy_best_target()`

**File:** `logic_cpu/greedy_target_weakest.py`
**Called From:** `logic_cpu/dc_combat.py` (imported at line 10; provides the scoring logic reference used in `select_attack_target`)

**Problem:** Find the single best target to attack using a simple single-pass heuristic.

**Algorithm: Greedy Linear Scan**
```
FOR each player unit:
    Calculate score =
        hp_factor × 10  +  dist_factor × 5  +  threat × 0.3
    IF score > best_score:
        Update best target
RETURN best target
```

**Time Complexity:** **O(P)** — single pass over all player units
**Space Complexity:** **O(1)** — constant extra space

**Is This Optimal?**
✅ **Yes.** For finding a single maximum with a fixed scoring function, linear scan is provably optimal (Ω(P) lower bound).

---

#### 4.2.2 Greedy Nearest Move — `greedy_nearest_move()`

**File:** `logic_cpu/greedy_move.py`
**Called From:** `logic_cpu/dc_combat.py` (imported at line 11; provides alternative movement heuristic)

**Problem:** Find the best tile to move to, optimizing for "ideal combat range" (distance 3).

**Algorithm: BFS + Greedy Scoring**
```
STEP 1:  BFS to find all reachable tiles within move_range
STEP 2:  Filter to EMPTY tiles (or current position)
STEP 3:  FOR each reachable tile:
            Compute score = Σ |distance_to_each_player − IDEAL_RANGE|
                          + edge_penalty (2 if on grid edge)
         SELECT tile with MINIMUM score (closest to ideal range from all enemies)
```

**Time Complexity:** **O(R × P)** where R = reachable tiles, P = player units
**Space Complexity:** **O(R)** — for storing reachable set

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **Greedy Scoring (Used)** | **O(R × P)** | ✅ Fast and effective for tactical positioning |
| Minimax | O(b^d) | Better strategic results but exponentially slow |
| Random | O(1) | Fast but strategically terrible |

**Verdict:** ✅ **Optimal for real-time tactics.** The greedy approach produces excellent results because "local optimal ≈ global optimal" in short-range tactical movement.

---

### 4.3 Graph Traversal (BFS)

---

#### 4.3.1 BFS Reachability — `bfs_reachable()`

**File:** `game_grid.py`
**Called From (6 call sites):**
1. `logic_cpu/dc_combat.py` → `select_position()` (line 108) — find tiles CPU can move to
2. `logic_cpu/greedy_move.py` → `greedy_nearest_move()` (line 15) — find tiles for greedy movement
3. `logic_attack.py` → `perform_attack_logic()` (line 156) — find allies within healing range
4. `logic_attack.py` → `initiate_player_attack()` (line 296) — verify attack range for player
5. `ui_draw.py` → movement range highlight (line 182) — show blue tiles on hover
6. `ui_draw.py` → attack range highlight (line 191) — show red tiles on hover

**Problem:** Find all grid tiles reachable within `max_depth` steps from a starting position.

**Algorithm: Breadth-First Search on Implicit Grid Graph**
```
The grid is treated as an IMPLICIT UNWEIGHTED GRAPH:
  − Nodes: Grid tiles (col, row)
  − Edges: Adjacent tiles (4-way for movement, 8-way for attacks)

MOVEMENT BFS (diagonal=False):
  − 4-directional neighbors (Up, Down, Left, Right)
  − BLOCKS pathing through occupied tiles (units block movement)
  − Units cannot move through other units

ATTACK BFS (diagonal=True):
  − 8-directional neighbors (includes diagonals)
  − Does NOT block through occupied tiles (attacks reach over units)
```

```
QUEUE ← {(start, depth=0)}
VISITED ← {start}

WHILE queue not empty:
    (c, r), d ← dequeue
    IF d > max_depth: CONTINUE
    ADD (c, r) to reachable set
    FOR each neighbor (nc, nr):
        IF not visited:
            MARK visited
            IF movement AND tile occupied: SKIP  ← collision blocking
            ENQUEUE (nc, nr, d+1)

RETURN reachable set
```

**Time Complexity:** **O(V + E)** ≈ O(grid_cells_in_range) — bounded by move_range²
  - For move_range=3: visits at most ~25 tiles
  - For attack_range=5: visits at most ~81 tiles (Chebyshev square)

**Space Complexity:** **O(V)** — visited set + queue

**Is This Optimal?**
| Method | Complexity | Verdict |
|--------|-----------|---------|
| **BFS (Used)** | **O(V + E)** | ✅ Provably optimal for unweighted shortest paths |
| DFS | O(V + E) | Same complexity but does NOT guarantee shortest paths |
| Dijkstra's | O((V+E) log V) | Overkill; all edges have weight 1 |
| A* | O(E log V) | Better for point-to-point; BFS is better for "all within range" |

**Verdict:** ✅ **Provably Optimal.** BFS is the textbook-correct algorithm for finding all nodes within distance K in an unweighted graph. No algorithm can do better than O(V + E) for this problem.

---

### 4.4 CPU Combat Orchestrator

---

#### 4.4.1 Advanced CPU Turn — `advanced_cpu_turn()`

**File:** `logic_cpu/advanced_cpu.py`
**Called From:** `main.py` → main game loop (line 218, via `cpu_turn(grid)`)

**Problem:** Execute the single best action across ALL CPU units each turn. The CPU must choose the single highest-value action: either MOVE one unit or ATTACK with one unit.

**Algorithm: Greedy Best-Action Selection (with D&C sub-routines)**
```
STEP 0:  Decrement cooldowns + process status effects (burn/stun/root)

STEP 1:  FOR each CPU unit on the grid:

         OPTION A — ATTACK:
           1. select_attack_target(prioritize_range=True)  [D&C]
           2. select_attack_placement(target)               [D&C]
           3. Score = attack.dmg + fire_bonus + kill_bonus(50)

         OPTION B — MOVE:
           1. select_attack_target()   [D&C] — find who to move towards
           2. select_position(target)  [D&C] — find best tile
           3. Score = 10 if position changed, else 0

         Track GLOBAL best action across all units

STEP 2:  Execute the single highest-scoring action (MOVE or ATTACK)
```

**Strict Rule:** **Move OR Attack — never both** in a single turn.

**Time Complexity:** **O(E × (P + R + A))** per turn
  - E = enemy units (~3), P = player units (~3), R = reachable tiles (~12), A = attacks (~3)
  - In practice: O(3 × (3 + 12 + 3)) = O(54) — effectively constant time

**Space Complexity:** **O(P + R)** — for candidate lists

---

## 5. Function Call Graph

```
main.py
├── StealingPhase.cpu_turn()                    [stealing_phase.py]
│   ├── select_steal_target()                   [logic_cpu/dc_steal.py]     ← D&C
│   │   ├── divide_by_element()                 [logic_cpu/dc_steal.py]     ← Partition
│   │   ├── dac_max()                           [logic_cpu/dc_steal.py]     ← D&C MAX
│   │   │   └── evaluate_card()                 [logic_cpu/dc_steal.py]     ← Heuristic
│   │   └── compute_utility()                   [logic_cpu/dc_steal.py]     ← Context Score
│   ├── select_best_retain()                    [logic_cpu/dc_retain.py]    ← D&C
│   │   ├── select_card_recursive()             [logic_cpu/dc_retain.py]    ← D&C
│   │   │   └── compare_cards()                 [logic_cpu/dc_retain.py]    ← Compare
│   │   │       └── evaluate_retain_value()     [logic_cpu/dc_retain.py]    ← Heuristic
│   │   └── (base case returns)
│   └── dac_max() [inline]                       [stealing_phase.py]        ← D&C Combine
│
├── advanced_cpu_turn()                         [logic_cpu/advanced_cpu.py]
│   ├── decrement_cooldowns()                   [logic_attack.py]
│   ├── process_turn_start_statuses()           [logic_attack.py]
│   ├── select_attack_target(prioritize_range)  [logic_cpu/dc_combat.py]    ← D&C
│   │   └── get_target_score()                  [logic_cpu/dc_combat.py]    ← Heuristic
│   ├── select_attack_placement()               [logic_cpu/dc_combat.py]    ← D&C
│   │   └── get_attack_score()                  [logic_cpu/dc_combat.py]    ← Heuristic
│   ├── select_attack_target()                  [logic_cpu/dc_combat.py]    ← D&C (for move)
│   ├── select_position()                       [logic_cpu/dc_combat.py]    ← D&C
│   │   └── bfs_reachable()                     [game_grid.py]             ← BFS
│   │       └── get_neighbors()                 [game_grid.py]             ← Graph Adj
│   ├── perform_attack_logic()                  [logic_attack.py]          ← Damage Calc
│   └── move_grid_card()                        [logic_cpu/advanced_cpu.py] ← Grid Update
│
├── initiate_player_attack()                    [logic_attack.py]
│   ├── bfs_reachable()                         [game_grid.py]             ← BFS
│   └── perform_attack_logic()                  [logic_attack.py]          ← Damage Calc
│
└── process_flame_tiles()                       [effects.py]               ← Fire DoT
    process_regen()                             [effects.py]               ← Heal over Time
    process_burn()                              [effects.py]               ← Burn DoT
```

---

## 6. Method Comparison & Optimality Analysis

### A. Stealing Phase: Deck Optimization
*Problem: Select 1 best card from N candidates (N=5)*

| Method | Complexity | Pros | Cons | Used? |
|--------|-----------|------|------|-------|
| **Grouped D&C** | **O(N)** | Element-aware "Best-in-Class" logic; context-aware combine | Slightly more code for grouping | ✅ Steal |
| **Recursive D&C** | **O(N)** | Flexible `compare_cards()`; matches combat logic structure | Moderate recursion overhead for small N | ✅ Retain |
| Linear Scan | O(N) | Fastest; minimal code | Harder to add multi-criteria logic | ❌ |
| Sorting | O(N log N) | Gives full ranking | Overkill; only need top 1 | ❌ |

### B. Combat: Target Selection
*Problem: Find best target among P enemies*

| Method | Complexity | Analysis | Used? |
|--------|-----------|----------|-------|
| **Recursive D&C** | **O(P)** | Tournament tree; modular `compare_targets()` | ✅ |
| Brute Force (Nested) | O(P²) | Too slow and unnecessary | ❌ |
| Priority Queue | O(P) build | Good for ranked lists; overkill for single best | ❌ |

### C. Combat: Positioning
*Problem: Find best tile among R reachable tiles*

| Method | Complexity | Analysis | Used? |
|--------|-----------|----------|-------|
| **Recursive D&C** | **O(R)** | Good for small R; demonstrates concept | ✅ |
| BFS | O(V+E) | Required for pathfinding (used upstream) | ✅ Upstream |
| A* Search | O(E log V) | Industry standard; overkill for move_range ≤ 3 | ❌ |

### D. Grid Reachability
*Problem: Find all tiles within distance K*

| Method | Complexity | Analysis | Used? |
|--------|-----------|----------|-------|
| **BFS** | **O(V+E)** | Provably optimal for unweighted graphs | ✅ |
| DFS | O(V+E) | Does NOT guarantee shortest paths | ❌ |
| Dijkstra's | O((V+E) log V) | Overkill for unweighted edges | ❌ |
| A* | O(E log V) | Better for point-to-point; not "all within range" | ❌ |

---

## 7. Recent Bug Fixes (v2.1)

### A. Damage Calculation Fix
**Bug:** Standard attacks and Life Drain used raw `atk.dmg` instead of the capped `base_dmg`, completely ignoring distance penalties and the 25% MaxHP damage cap.
**Fix:** Changed to use `base_dmg` which includes:
- Distance penalty: `base_dmg = atk.dmg − chebyshev_distance`
- Damage cap: `max(1, min(base_dmg, target.max_hp × 0.25))`
**File:** `logic_attack.py` → `perform_attack_logic()`

### B. CPU Moving onto Occupied Tiles
**Bug:** `select_position()` in `dc_combat.py` returned tiles that were occupied by other cards. The CPU could move onto a player's tile (appearing to "take their place").
**Fix:** Added empty-tile filter after BFS: only tiles with `card is None` or the attacker's current tile are valid move candidates.
**File:** `logic_cpu/dc_combat.py` → `select_position()`

### C. BFS Pathing Through Units
**Bug:** `bfs_reachable()` allowed movement BFS to path through occupied tiles, letting units reach tiles behind other units.
**Fix:** For movement BFS (`diagonal=False`), tiles occupied by cards now block further expansion. Attack BFS (`diagonal=True`) still reaches over units.
**File:** `game_grid.py` → `bfs_reachable()`

### D. Fire Trail Per-Frame Damage
**Bug:** `process_flame_tiles()` was called every frame (~60 FPS), dealing 5 damage per frame = 300 damage/second instead of once per turn.
**Fix:** Added a tick counter so fire trail damage triggers once per second (every FPS frames).
**File:** `effects.py` → `process_flame_tiles()`

### E. Rooted Unit Movement Scoring
**Bug:** `move_score = 0` was calculated outside the rooted-check `else` block, overwriting the `-1` set for rooted units, allowing rooted units to be selected for movement.
**Fix:** Moved `move_score` calculation inside the `else` block.
**File:** `logic_cpu/advanced_cpu.py` → `advanced_cpu_turn()`

---

## 8. File Structure

```
marve-strike/
├── main.py                         # Game loop, event handling, rendering
├── config.py                       # Constants (grid size, FPS, UI dimensions)
├── game_grid.py                    # Grid class, BFS reachability, distance functions
├── card.py                         # Card and Tile dataclasses
├── attack.py                       # Attack dataclass
├── cards.json                      # Card pool data (stats, attacks, animations)
├── logic_attack.py                 # Attack execution, healing, damage calculation
├── effects.py                      # Fire trail, regen, burn (DoT effects)
├── animations.py                   # Visual effects, projectiles, particles
├── ui_draw.py                      # Grid rendering, HUD, highlights
├── stealing_phase.py               # Stealing Phase UI + CPU turn logic
├── colors.py                       # Color constants
├── fonts.py                        # Font definitions
├── README.md                       # ← This file
├── README_HEALING.md               # Healing mechanics documentation
├── assets/                         # Card images
└── logic_cpu/                      # CPU AI modules
    ├── advanced_cpu.py             # Combat orchestrator (Move OR Attack)
    ├── dc_combat.py                # D&C: Target, Position, Attack selection
    ├── dc_steal.py                 # D&C: Steal target selection
    ├── dc_retain.py                # D&C: Retain card selection
    ├── greedy_target_weakest.py    # Greedy: Target scoring heuristic
    └── greedy_move.py              # Greedy: Movement heuristic
```

---

## 9. Controls

| Key | Action |
|-----|--------|
| **Click** (Placement) | Place card on grid tile |
| **Click** (Combat) | Select player unit / Move to tile |
| **1, 2, 3** (Placement) | Select element: Fire, Water, Leaf |
| **Q/W/E** | Attack with Player 1 (Ability 1/2/3) |
| **A/S/D** | Attack with Player 2 (Ability 1/2/3) |
| **Z/X/C** | Attack with Player 3 (Ability 1/2/3) |
| Hold **1/2/3** + Attack | Target specific enemy unit |
| **H** | Toggle help overlay |
| **M** | Force CPU turn (debug) |
| **SPACE** | Continue after Stealing Phase |