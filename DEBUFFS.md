# ⚡ Status Effects & Debuffs Guide

This document explains the various status effects (Buffs & Debuffs) that can be applied to units during combat.

## 🔴 Debuffs (Negative Effects)

| Effect | Element | Duration | Description |
| :--- | :--- | :--- | :--- |
| **Flame (Burn)** | Fire | 2 Turns | **Damage over Time**: The unit loses **2 HP** at the start of every turn. |
| **Frost** | Water | 2 Turns | **Reduced Mobility**: The unit's **Move Range** is decreased by 1. |
| **Shock (Stun)** | Null / Water | 1 Turn | **Paralysis**: The unit is completely incapacitated and **cannot attack** for the turn. |
| **Root** | Leaf | 1 Turn | **Entangled**: The unit is stuck to its current tile. It **cannot move**, but it can still attack and heal. |
| **Weaken** | Water | 2 Turns | **Reduced Power**: The unit's attack damage is decreased by **2**. |
| **Vulnerable** | Wind | 2 Turns | **Exploited**: The unit takes **+2 extra damage** from all incoming attacks. |

---

## 🔵 Buffs (Positive Effects)

| Effect | Element | Duration | Description |
| :--- | :--- | :--- | :--- |
| **Regen** | Leaf | 3 Turns | **Healing over Time**: The unit restores **2 HP** at the start of every turn. |
| **Thorns** | Leaf | 3 Turns | **Reflective Guard**: Any enemy that hits this unit takes **1 damage** in return. |
| **Empower** | Combined | 2 Turns | **Increased Power**: The unit's attack damage is increased by **2**. |

---

## 🛠 Interaction Details

1.  **Application**: Most debuffs have a **40% chance** to trigger when hit by an attack of the corresponding element.
2.  **Stacking**: Applying the same effect again will **refresh the duration** to its maximum, but it will not stack the numerical value (e.g., getting Burned twice still deals 2 damage per turn, but resets the timer).
3.  **Visualization**:
    *   **Badges**: Active effects appear as small badges above the unit's HP bar.
    *   **Visual FX**: Certain effects have on-grid animations:
        *   **Flame**: Red-orange glow on the tile.
        *   **Root**: A ring of green nature particles around the unit's base.
        *   **Heal/Regen**: Rising green crosses/particles.

## 🌿 Special Ability: Vine Recovery
The **Vine Recovery** (on the *Backstab Gust* card) is a specialized heal that applies **Root** to yourself as a side-effect. Use it wisely when you don't need to move next turn!
