# Refactoring Plan for Card Strike Game

## Steps to Complete Refactoring

1. **Create config.py**: Extract configuration constants (GRID_COLS, GRID_ROWS, TILE_SIZE, WIDTH, HEIGHT, FPS).
2. **Create colors.py**: Extract color definitions (C_BG, C_GRID, etc., and elemental colors E_FIRE, etc.).
3. **Create fonts.py**: Extract font definitions (FONT_MAIN, FONT_BIG, FONT_DMG) and pygame.init() for fonts.
4. **Create attack.py**: Extract Attack dataclass.
5. **Create card.py**: Extract Card and Tile dataclasses.
6. **Create grid.py**: Extract Grid class and cell_center helper function.
7. **Create animations.py**: Extract Particle and AnimationManager classes.
8. **Create effects.py**: Extract global effect lists (flame_tiles, regen_effects, burn_effects) and processing functions (process_flame_tiles, process_regen, process_burn).
9. **Create logic_attack.py**: Extract perform_attack_logic and initiate_player_attack functions.
10. **Create logic_cpu.py**: Extract cpu_turn function.
11. **Create ui_draw.py**: Extract draw_ui function and draw_card_shape helper.
12. **Create main.py**: Extract the main loop, setup variables (grid, anim_mgr, selected_pos, etc.), event handling, and effect processing. Add imports from all modules. Move pygame.init() and screen setup here.
13. **Test the refactored game**: Run main.py and verify functionality.

## Progress Tracking
- [x] Step 1: config.py
- [x] Step 2: colors.py
- [x] Step 3: fonts.py
- [x] Step 4: attack.py
- [x] Step 5: card.py
- [x] Step 6: grid.py
- [x] Step 7: animations.py
- [x] Step 8: effects.py
- [x] Step 9: logic_attack.py
- [x] Step 10: logic_cpu.py
- [x] Step 11: ui_draw.py
- [x] Step 12: main.py
- [x] Step 13: Testing
