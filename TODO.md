# TODO: Implement Full Health Bar Above Cards

## Step 1: Update Card Dataclass ✅
- Add new fields to Card dataclass in card.py: flash_timer: int = 0, shield: int = 0, display_hp: int = None, rarity: str = "normal"

## Step 2: Update Card Creation in main.py ✅
- Set display_hp = card.hp in create_player_card and create_enemy_card functions

## Step 3: Add HP Animation Update in main.py ✅
- Add smooth HP animation loop for all cards before draw_ui call in main loop

## Step 4: Add Flash on Damage in logic_attack.py ✅
- After target.hp -= dmg in perform_attack_logic, add target.flash_timer = 10

## Step 5: Implement Advanced HP Bar in ui_draw.py ✅
- Replace old HP bar with advanced one: gradient, glow for low HP, shield overlay, HP text
- Add rarity borders after card drawing

## Step 6: Test Implementation
- Run the game to verify HP bars display above cards, animate smoothly, flash on damage, show gradients/shields, and rarity borders
