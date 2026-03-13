import sys
import os
import pygame

# Mock pygame screen and other globals needed
pygame.init()
screen = pygame.display.set_mode((10, 10))

sys.path.append(r'c:\Users\Public\Documents\4thsem\projects\marve-strike\marve-strike')

from game_grid import Grid
from logic_attack import initiate_player_attack
from card import Card
from attack import Attack

grid = Grid(10, 10)
# Add a player card
p_card = Card("player", "Hero", 100, 100, [Attack("Strike", 10, "null", 5)], index=0)
grid.tiles[0][0].card = p_card
# Add an enemy card
e_card = Card("enemy", "Beast", 100, 100, [Attack("Strike", 10, "null", 5)], index=0)
grid.tiles[1][1].card = e_card

print("Testing initiate_player_attack...")
try:
    # player_idx=0, attack_idx=0, enemy_idx=0
    result = initiate_player_attack(0, 0, 0, grid)
    print(f"Result: {result}")
except Exception as e:
    import traceback
    traceback.print_exc()
