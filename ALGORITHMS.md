# Algorithms & Logic Documentation

This project implements a custom AI using a combination of **Divide & Conquer (D&C)** and **Greedy** algorithms to make strategic decisions in both the Stealing Phase and Combat Phase.

## 1. Stealing Phase (Pre-Game)

**File:** `stealing_phase.py` & `logic_cpu/dc_steal.py`

The Stealing Phase determines which cards the CPU keeps, steals, or swaps to build the strongest possible 3-card deck.

### **Algorithm: Divide & Conquer (D&C)**

The problem of "logic for the turn" is **Divided** into three independent sub-problems:
1.  **Steal Analysis**: What is the best card to steal from the player?
2.  **Swap Analysis**: Is there a card in the player's hand better than the worst card in my deck?
3.  **Retain Analysis**: What is the best card currently in my hand to keep?

**Conquer**:
Each sub-problem is solved independently to find the "Best Action" for that category.
- *Steal Target Selection* (`logic_cpu/dc_steal.py`) uses D&C to group potential targets by Element, finds the best in each group, and then combines them based on element priority.
- *Evaluation Heuristic*: Calculates a score based on HP + Damage + Healing + Range Utility.

**Combine**:
The CPU compares the scores of the best Steal, Swap, and Retain actions and picks the single **MAX** score action to execute.

---

## 2. Combat Phase (In-Game)

**File:** `logic_cpu/advanced_cpu.py` & `logic_cpu/dc_combat.py`

The CPU must decide whether to Move or Attack, and if so, where and with what ability. This uses a **Hybrid** approach.

### **A. Attack Target Selection**
**File:** `logic_cpu/dc_combat.py` -> `select_attack_target`
- **Method**: **Divide & Conquer + Greedy**
- **Logic**:
    1.  **Divide**: Group all visible Player units by Element (Fire, Water, Leaf, etc.).
    2.  **Conquer**: Find the unit with the lowest HP (Weakest) in *each* group.
    3.  **Combine**: From the list of "Weakest Candidates" (one per element), use a **Greedy** check to pick the absolute closest/easiest target.

### **B. Positioning / Movement**
**File:** `logic_cpu/dc_combat.py` -> `select_position`
- **Method**: **Spatial Divide & Conquer**
- **Logic**:
    1.  **Divide**: Split the reachable movement grid into 4 spatial quadrants (NE, NW, SE, SW) relative to the target.
    2.  **Conquer**: In each quadrant, find the tile that minimizes distance to the target (**Greedy** local best).
    3.  **Combine**: Compare the 4 "Quadrant Champions" and pick the one that offers the best strategic advantage (e.g., closest range without being blocked).

### **C. Attack Selection**
**File:** `logic_cpu/dc_combat.py` -> `select_attack_placement`
- **Method**: **Category Divide & Conquer**
- **Logic**:
    1.  **Divide**: Group the unit's available attacks into ranges: "Short" (Melee), "Medium", and "Long".
    2.  **Conquer**: Find the highest damage attack in each range category that is *not on cooldown*.
    3.  **Combine**: Select the highest damage option overall that can hit the target from the chosen position.

### **D. Final Turn Execution**
**File:** `logic_cpu/advanced_cpu.py`
- **Method**: **Greedy Score Maximization**
- **Logic**:
    - The CPU moves purely based on Score.
    - **Score = Damage Dealt + Bonuses** (e.g., +50 points for a Killing Blow).
    - It simulates the outcome of the best *Attack* vs. the best *Move*.
    - It greedily chooses whichever action yields the higher score.

---

## Summary Table

| Phase | Decision | Algorithm | File Location |
| :--- | :--- | :--- | :--- |
| **Stealing** | Turn Action (Steal/Swap/Keep) | **Divide & Conquer** | `stealing_phase.py` |
| **Stealing** | Target Selection | **Divide & Conquer** | `logic_cpu/dc_steal.py` |
| **Combat** | Target Selection | **D&C + Greedy** | `logic_cpu/dc_combat.py` |
| **Combat** | Movement Position | **Spatial D&C** | `logic_cpu/dc_combat.py` |
| **Combat** | Attack Choice | **D&C (Range Groups)** | `logic_cpu/dc_combat.py` |
| **Combat** | Final Execution | **Greedy Scoring** | `logic_cpu/advanced_cpu.py` |
