import sys

# Configuration constants - desktop first, reduced for browser builds
IS_WEB = sys.platform == "emscripten"

GRID_COLS = 23
GRID_ROWS = 11
TILE_SIZE = 48 if IS_WEB else 64
BOTTOM_PANEL_HEIGHT = 220 if IS_WEB else 260
WIDTH = GRID_COLS * TILE_SIZE
HEIGHT = GRID_ROWS * TILE_SIZE + BOTTOM_PANEL_HEIGHT
FPS = 60

# 8px grid system
GRID_UNIT = 8 if not IS_WEB else 6
PADDING_SM = GRID_UNIT * 2
PADDING_MD = GRID_UNIT * 3
PADDING_LG = GRID_UNIT * 4
PADDING_XL = GRID_UNIT * 6

# Border radius
RADIUS_SM = 8
RADIUS_MD = 16
RADIUS_LG = 24
