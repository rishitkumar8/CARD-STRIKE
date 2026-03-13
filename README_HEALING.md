# Healing System & Card Guide

This document outlines the healing mechanics and specific card abilities available in the game. All healing effects are capped by the unit's maximum HP (100).

## 🟢 General Healing Mechanics

1.  **Self-Healing**:
    *   Abilities with **Range 0** or specifically designated as "Self-heal" target *only* the user.
    *   They restore HP instantly.

2.  **Team Healing (Support)**:
    *   Abilities with **Range > 0** (e.g., Range 3) create a healing aura.
    *   **Effect**: Heals the user AND all allied units within the specified range (including diagonals).
    *   **Visual**: Green numbers appear above healed units.

3.  **Life Drain**:
    *   Attacks that damage an enemy and heal the user simultaneously.
    *   Calculated as: `User HP += Heal Amount` (independent of damage dealt).

---

## 🌿 Healing Cards & Abilities

### 1. **Scorched Root** (Fire / Leaf)
*   **Ability**: `Nature's Recovery`
*   **Type**: Self-Heal
*   **Effect**: Restores **20 HP** to self.
*   **Range**: 0 (Self only)
*   **Cooldown**: 3 turns

### 2. **Flame Embrace** (Fire / Leaf)
*   **Ability**: `Nature Heal`
*   **Type**: Team Support
*   **Effect**: Restores **20 HP** to self and all allies within **Range 3**.
*   **Range**: 3
*   **Cooldown**: 3 turns

### 3. **Overgrowth** (Water / Leaf)
*   **Ability**: `Growth Heal`
*   **Type**: Team Support
*   **Effect**: Restores **20 HP** to self and all allies within **Range 3**.
*   **Range**: 3
*   **Cooldown**: 3 turns

### 4. **Nature Wave** (Leaf / Water)
*   **Ability**: `Regeneration`
*   **Type**: Self-Heal
*   **Effect**: Restores **25 HP** to self.
*   **Range**: 0 (Self only)
*   **Cooldown**: 3 turns

### 5. **Nature Zone** (Leaf / Wind)
*   **Ability**: `Nature Heal`
*   **Type**: Team Support
*   **Effect**: Restores **20 HP** to self and all allies within **Range 3**.
*   **Range**: 3
*   **Cooldown**: 3 turns

### 6. **Vine Strike** (Leaf / Wind)
*   **Ability**: `Life Drain`
*   **Type**: Offensive Heal
*   **Effect**: Deals **10 DMG** to enemy, Heals user for **15 HP**.
*   **Range**: 2 (Target Enemy)
*   **Cooldown**: 3 turns

### 7. **Backstab Gust** (Wind / Leaf)
*   **Ability**: `Vine Recovery`
*   **Type**: Self-Heal
*   **Effect**: Restores **20 HP** to self. Applies **Root (1 turn)** to self.
*   **Range**: 0 (Self only)
*   **Cooldown**: 3 turns

---

## 🛠 Status Effects from Healing
Some healing cards may apply status effects:
*   **Root**: Unit cannot move for the duration (used in `Vine Recovery` as a trade-off).

## ⚠️ Notes
*   Healing cannot exceed Max HP.
*   Dead units (0 HP) are removed from the board and cannot be healed.
