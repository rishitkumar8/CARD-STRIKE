# card_strike_added_cpu_move_and_movement.py
# Run: python card_strike_added_cpu_move_and_movement.py
# Uses design doc: /mnt/data/Card_Strike.pdf. :contentReference[oaicite:1]{index=1}

import pygame
import os
import random
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

pygame.init()
FONT = pygame.font.SysFont(None, 20)
BIGFONT = pygame.font.SysFont(None, 28)

# --- Config ---
GRID_COLS, GRID_ROWS = 9, 5
TILE_SIZE = 96
WIDTH, HEIGHT = GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE + 100
FPS = 60

# Colors
WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
GRAY = (200, 200, 200)
PLAYER_COLOR = (50, 160, 60)
ENEMY_COLOR = (200, 60, 60)
SELECT_COLOR = (255, 215, 0)
HIGHLIGHT_COLOR = (120, 170, 250)
DAMAGE_COLOR = (255, 80, 80)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Card Strike — Movement + CPU 'M' Move")
clock = pygame.time.Clock()

ASSET_DIR = "assets"
PLAYER_ASSETS = [os.path.join(ASSET_DIR, f"player{i+1}.png") for i in range(3)]
ENEMY_ASSETS  = [os.path.join(ASSET_DIR, f"enemy{i+1}.png") for i in range(3)]

# --- Data models ---
@dataclass
class Attack:
    name: str
    dmg: int

@dataclass
class Card:
    owner: str  # 'player' or 'enemy'
    name: str
    hp: int
    max_hp: int
    attacks: List[Attack]
    move_range: int = 2
    img: Optional[pygame.Surface] = None
    index: int = 0  # 0..2 mapping to its slot (player slot or enemy slot)

@dataclass
class Tile:
    col: int
    row: int
    card: Optional[Card] = None
    walkable: bool = True

class Grid:
    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.tiles = [[Tile(c, r) for r in range(rows)] for c in range(cols)]

    def in_bounds(self, c, r):
        return 0 <= c < self.cols and 0 <= r < self.rows

grid = Grid(GRID_COLS, GRID_ROWS)

# --- Helpers ---
def pixel_to_cell(x, y):
    return x // TILE_SIZE, y // TILE_SIZE

def cell_center(c, r):
    return c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2

def load_image(path, size):
    try:
        surf = pygame.image.load(path).convert_alpha()
        surf = pygame.transform.smoothscale(surf, size)
        return surf
    except Exception:
        return None

# Floating damage text
@dataclass
class FloatingText:
    text: str
    pos: Tuple[int,int]
    life: float = 1.0

floating_texts: List[FloatingText] = []

def push_floating(text, pos):
    floating_texts.append(FloatingText(text, pos, 1.0))

# --- Card creation ---
def create_player_card(slot_index: int) -> Card:
    attacks = [
        Attack("Q-Strike", dmg=12 + slot_index*2),
        Attack("W-Blow",   dmg=9  + slot_index*2),
        Attack("E-Burst",  dmg=16 + slot_index*1),
    ]
    name = f"P{slot_index+1}"
    hp = 80 + slot_index*8
    img = None
    if os.path.exists(PLAYER_ASSETS[slot_index]):
        img = load_image(PLAYER_ASSETS[slot_index], (TILE_SIZE-12, TILE_SIZE-12))
    return Card(owner="player", name=name, hp=hp, max_hp=hp, attacks=attacks, move_range=3, img=img, index=slot_index)

def create_enemy_card(slot_index: int) -> Card:
    attacks = [
        Attack("A-Claw", dmg=10 + slot_index*2),
        Attack("S-Bite", dmg=13 + slot_index*1),
        Attack("D-Sting", dmg=9 + slot_index*3),
    ]
    name = f"E{slot_index+1}"
    hp = 70 + slot_index*6
    img = None
    if os.path.exists(ENEMY_ASSETS[slot_index]):
        img = load_image(ENEMY_ASSETS[slot_index], (TILE_SIZE-12, TILE_SIZE-12))
    return Card(owner="enemy", name=name, hp=hp, max_hp=hp, attacks=attacks, move_range=2, img=img, index=slot_index)

# --- Game state & flow ---
placing_players = True
players_placed = 0  # 0..3
MAX_PLAYERS = 3

selected_player_pos: Optional[Tuple[int,int]] = None  # selected tile coordinates for moving
hovered_cell: Optional[Tuple[int,int]] = None

def spawn_random_enemies():
    empty_cells = [(c, r) for c in range(grid.cols) for r in range(grid.rows) if grid.tiles[c][r].card is None]
    random.shuffle(empty_cells)
    chosen = empty_cells[:3]
    for i, (c, r) in enumerate(chosen):
        grid.tiles[c][r].card = create_enemy_card(i)

def get_enemy_pos_by_index(idx: int) -> Optional[Tuple[int,int]]:
    for c in range(grid.cols):
        for r in range(grid.rows):
            t = grid.tiles[c][r]
            if t.card and t.card.owner == "enemy" and t.card.index == idx:
                return (c, r)
    return None

def get_player_pos_by_index(idx: int) -> Optional[Tuple[int,int]]:
    for c in range(grid.cols):
        for r in range(grid.rows):
            t = grid.tiles[c][r]
            if t.card and t.card.owner == "player" and t.card.index == idx:
                return (c, r)
    return None

def count_players_on_board() -> int:
    return sum(1 for c in range(grid.cols) for r in range(grid.rows) if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "player")

# --- Key mappings for attack keys to card index and attack index ---
attack_key_map: Dict[int, Tuple[int,int]] = {
    pygame.K_q: (0, 0), pygame.K_w: (0, 1), pygame.K_e: (0, 2),
    pygame.K_a: (1, 0), pygame.K_s: (1, 1), pygame.K_d: (1, 2),
    pygame.K_z: (2, 0), pygame.K_x: (2, 1), pygame.K_c: (2, 2),
}

number_key_map = {
    pygame.K_1: 0,
    pygame.K_2: 1,
    pygame.K_3: 2,
}

# --- Movement helpers (BFS distance for range check) ---
def tiles_in_range(start: Tuple[int,int], rng: int):
    visited = set()
    q = [(start[0], start[1], 0)]
    while q:
        cc, rr, d = q.pop(0)
        if (cc, rr) in visited:
            continue
        visited.add((cc, rr))
        if d >= rng:
            continue
        for dc, dr in ((1,0),(-1,0),(0,1),(0,-1)):
            nc, nr = cc + dc, rr + dr
            if grid.in_bounds(nc, nr) and (nc, nr) not in visited:
                q.append((nc, nr, d+1))
    return visited

# --- Attack resolution: perform attack from player_card_idx using attack_idx onto enemy with enemy_idx ---
def perform_player_attack_on_enemy(player_idx: int, attack_idx: int, enemy_idx: int):
    ppos = get_player_pos_by_index(player_idx)
    if not ppos:
        print(f"Player card {player_idx+1} not placed (or dead).")
        return
    enemy_pos = get_enemy_pos_by_index(enemy_idx)
    if not enemy_pos:
        print(f"Enemy {enemy_idx+1} not found (dead or not spawned).")
        return
    pc = grid.tiles[ppos[0]][ppos[1]].card
    ec = grid.tiles[enemy_pos[0]][enemy_pos[1]].card
    if not pc or not ec:
        return
    if attack_idx < 0 or attack_idx >= len(pc.attacks):
        return
    attack = pc.attacks[attack_idx]
    damage = attack.dmg + random.randint(-2,2)
    ec.hp -= damage
    push_floating(f"-{damage}", cell_center(enemy_pos[0], enemy_pos[1]))
    print(f"{pc.name} -> {attack.name} -> {ec.name} for {damage} dmg.")
    if ec.hp <= 0:
        push_floating("DEFEATED", cell_center(enemy_pos[0], enemy_pos[1]))
        grid.tiles[enemy_pos[0]][enemy_pos[1]].card = None

# --- CPU move+attack ('M' key) ---
def cpu_move_and_attack_random():
    # For each enemy on board: try to move randomly up to move_range, then attack a random alive player
    enemies_positions = [(c,r) for c in range(grid.cols) for r in range(grid.rows) if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "enemy"]
    players_positions = [(c,r) for c in range(grid.cols) for r in range(grid.rows) if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "player"]
    if not enemies_positions:
        print("No enemies to act.")
        return
    if not players_positions:
        print("No players to be attacked.")
        return

    for epos in enemies_positions:
        # ensure still an enemy (might be removed earlier this loop)
        if not grid.tiles[epos[0]][epos[1]].card or grid.tiles[epos[0]][epos[1]].card.owner != "enemy":
            continue
        enemy_card = grid.tiles[epos[0]][epos[1]].card

        # collect all empty tiles and include staying in place
        empty_tiles = [(c,r) for c in range(grid.cols) for r in range(grid.rows) if grid.tiles[c][r].card is None]
        # filter to those within move_range (Manhattan)
        def manhattan(a,b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
        possible_moves = [pos for pos in empty_tiles if manhattan(pos, epos) <= enemy_card.move_range]
        # include staying
        possible_moves.append(epos)
        if possible_moves:
            dest = random.choice(possible_moves)
            if dest != epos:
                # move
                grid.tiles[dest[0]][dest[1]].card = enemy_card
                grid.tiles[epos[0]][epos[1]].card = None
                print(f"{enemy_card.name} moved from {epos} to {dest}.")
                epos = dest  # update epos for attack target coordinates

        # attack a random alive player (if any)
        alive_players = [(c,r) for c in range(grid.cols) for r in range(grid.rows) if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "player"]
        if not alive_players:
            print("All players dead; CPU ends.")
            return
        target_pos = random.choice(alive_players)
        target_card = grid.tiles[target_pos[0]][target_pos[1]].card
        if not target_card:
            continue
        attack = random.choice(enemy_card.attacks)
        damage = attack.dmg + random.randint(-2,2)
        target_card.hp -= damage
        push_floating(f"-{damage}", cell_center(target_pos[0], target_pos[1]))
        print(f"{enemy_card.name} used {attack.name} on {target_card.name} for {damage} dmg.")
        if target_card.hp <= 0:
            push_floating("DEFEATED", cell_center(target_pos[0], target_pos[1]))
            grid.tiles[target_pos[0]][target_pos[1]].card = None

# --- Drawing & UI ---
def draw_grid():
    screen.fill(WHITE)
    # tiles
    for c in range(grid.cols):
        for r in range(grid.rows):
            rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, GRAY, rect, 1)

    # highlight selected player's reachable tiles
    if selected_player_pos:
        sc = selected_player_pos
        sc_card = grid.tiles[sc[0]][sc[1]].card if grid.in_bounds(sc[0], sc[1]) else None
        if sc_card:
            reachable = tiles_in_range(sc, sc_card.move_range)
            for (rc, rr) in reachable:
                # do not highlight the selected tile itself with the blue highlight
                if (rc, rr) == sc:
                    continue
                rect = pygame.Rect(rc*TILE_SIZE+3, rr*TILE_SIZE+3, TILE_SIZE-6, TILE_SIZE-6)
                pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect)

    # draw cards
    for c in range(grid.cols):
        for r in range(grid.rows):
            t = grid.tiles[c][r]
            if t.card:
                x = c * TILE_SIZE + 6
                y = r * TILE_SIZE + 6
                if t.card.img:
                    screen.blit(t.card.img, (x, y))
                else:
                    cx, cy = cell_center(c, r)
                    color = PLAYER_COLOR if t.card.owner == "player" else ENEMY_COLOR
                    pygame.draw.circle(screen, color, (cx, cy), TILE_SIZE//3)
                    txt = FONT.render(t.card.name, True, BLACK)
                    screen.blit(txt, (cx - txt.get_width()//2, cy - txt.get_height()//2))
                # hp bar
                hp_ratio = max(0, t.card.hp) / t.card.max_hp
                bar_w = TILE_SIZE - 16
                bar_h = 8
                bar_x = c * TILE_SIZE + 8
                bar_y = r * TILE_SIZE + TILE_SIZE - 14
                pygame.draw.rect(screen, (50,50,50), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(screen, (180,30,30), (bar_x+1, bar_y+1, int((bar_w-2)*hp_ratio), bar_h-2))

    # selection outline
    if selected_player_pos:
        sc = selected_player_pos
        if grid.in_bounds(sc[0], sc[1]):
            rect = pygame.Rect(sc[0]*TILE_SIZE+2, sc[1]*TILE_SIZE+2, TILE_SIZE-4, TILE_SIZE-4)
            pygame.draw.rect(screen, SELECT_COLOR, rect, 3)

    # hovered cell preview (outline)
    if hovered_cell and grid.in_bounds(hovered_cell[0], hovered_cell[1]):
        rect = pygame.Rect(hovered_cell[0]*TILE_SIZE+2, hovered_cell[1]*TILE_SIZE+2, TILE_SIZE-4, TILE_SIZE-4)
        pygame.draw.rect(screen, (120,120,120), rect, 2)

    # floating texts
    for ft in floating_texts:
        txt = BIGFONT.render(ft.text, True, DAMAGE_COLOR)
        screen.blit(txt, (ft.pos[0] - txt.get_width()//2, ft.pos[1] - txt.get_height()//2))

    # HUD / instructions
    hud_y = GRID_ROWS * TILE_SIZE + 6
    lines = []
    if placing_players:
        lines.append("Placing players: Click empty tiles to place your 3 player cards (P1,P2,P3).")
        lines.append(f"Placed: {players_placed}/{MAX_PLAYERS}")
    else:
        lines.append("Players placed. Enemies spawned randomly.")
        lines.append("Attack: HOLD number key (1/2/3) and press attack key (q,w,e / a,s,d / z,x,c).")
        lines.append("Move selected player: Click to select -> move mouse to tile -> press SPACE to move (within range).")
        lines.append("Press M to have CPU move+attack randomly (for each enemy). Press R to reset.")
    for i, line in enumerate(lines):
        screen.blit(FONT.render(line, True, BLACK), (8, hud_y + i*18))

    # show players' attacks summary at bottom-right
    info_x = WIDTH - 360
    info_y = GRID_ROWS * TILE_SIZE + 8
    screen.blit(FONT.render("Player cards & attacks:", True, BLACK), (info_x, info_y))
    offset = 18
    for idx in range(3):
        ppos = get_player_pos_by_index(idx)
        if ppos:
            pc = grid.tiles[ppos[0]][ppos[1]].card
            attacks_str = ", ".join(f"{k.name}:{k.dmg}" for k in pc.attacks)
            screen.blit(FONT.render(f"P{idx+1} ({pc.hp}HP): {attacks_str}", True, BLACK), (info_x, info_y+offset))
        else:
            screen.blit(FONT.render(f"P{idx+1}: (not placed)", True, BLACK), (info_x, info_y+offset))
        offset += 16

    # show enemies & their indices
    offset += 4
    screen.blit(FONT.render("Enemies (indices):", True, BLACK), (info_x, info_y+offset))
    offset += 16
    for idx in range(3):
        epos = get_enemy_pos_by_index(idx)
        if epos:
            ec = grid.tiles[epos[0]][epos[1]].card
            screen.blit(FONT.render(f"E{idx+1} at {epos} HP:{ec.hp}", True, BLACK), (info_x, info_y+offset))
        else:
            screen.blit(FONT.render(f"E{idx+1}: (dead or not spawned)", True, BLACK), (info_x, info_y+offset))
        offset += 16

# --- Main loop & setup ---
running = True
players_placed = 0
placing_players = True
floating_texts = []

def reset_all():
    global placing_players, players_placed, floating_texts, selected_player_pos
    for c in range(grid.cols):
        for r in range(grid.rows):
            grid.tiles[c][r].card = None
    placing_players = True
    players_placed = 0
    floating_texts = []
    selected_player_pos = None

reset_all()

while running:
    dt = clock.tick(FPS) / 1000.0
    mx, my = pygame.mouse.get_pos()
    hovered_cell = pixel_to_cell(mx, my)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_all()

            elif event.key == pygame.K_m:
                # CPU move + attack randomly for each enemy (inclusion request)
                if not placing_players:
                    cpu_move_and_attack_random()
                else:
                    print("Place players first before triggering CPU moves.")

            else:
                # attack keys when not in placing mode
                if not placing_players and event.key in attack_key_map:
                    pressed = pygame.key.get_pressed()
                    targeted_enemy_idx = None
                    for num_key, eidx in number_key_map.items():
                        if pressed[num_key]:
                            targeted_enemy_idx = eidx
                            break
                    if targeted_enemy_idx is None:
                        print("Hold number key 1/2/3 while pressing an attack key to target that enemy.")
                    else:
                        player_idx, attack_idx = attack_key_map[event.key]
                        perform_player_attack_on_enemy(player_idx, attack_idx, targeted_enemy_idx)

                # movement: SPACE to move selected player to hovered_cell if valid
                if event.key == pygame.K_SPACE and not placing_players and selected_player_pos:
                    dest = hovered_cell
                    if not grid.in_bounds(dest[0], dest[1]):
                        continue
                    # ensure destination empty (or it's the same tile)
                    if grid.tiles[dest[0]][dest[1]].card is not None and dest != selected_player_pos:
                        print("Destination occupied.")
                    else:
                        sc_card = grid.tiles[selected_player_pos[0]][selected_player_pos[1]].card
                        if not sc_card:
                            selected_player_pos = None
                            continue
                        # check within move range (Manhattan)
                        dist = abs(dest[0] - selected_player_pos[0]) + abs(dest[1] - selected_player_pos[1])
                        if dist <= sc_card.move_range:
                            # perform move
                            grid.tiles[dest[0]][dest[1]].card = sc_card
                            grid.tiles[selected_player_pos[0]][selected_player_pos[1]].card = None
                            print(f"{sc_card.name} moved from {selected_player_pos} to {dest}.")
                            selected_player_pos = None
                        else:
                            print("Target out of range (move_range {}).".format(sc_card.move_range))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if my >= GRID_ROWS * TILE_SIZE:
                continue
            c, r = pixel_to_cell(mx, my)
            if not grid.in_bounds(c, r):
                continue
            t = grid.tiles[c][r]
            if placing_players:
                if t.card is None:
                    if players_placed < MAX_PLAYERS:
                        card = create_player_card(players_placed)
                        grid.tiles[c][r].card = card
                        players_placed += 1
                        print(f"Placed {card.name} at {(c,r)}")
                        if players_placed >= MAX_PLAYERS:
                            placing_players = False
                            spawn_random_enemies()
                            print("Players placed. Enemies spawned randomly.")
                else:
                    print("Tile occupied. Choose another tile.")
            else:
                # after placement, clicking behavior:
                # - If clicking on a player card: select/deselect it for movement
                # - Otherwise just print tile info
                if t.card and t.card.owner == "player":
                    # toggle selection
                    if selected_player_pos == (c, r):
                        selected_player_pos = None
                        print(f"Deselected {t.card.name}.")
                    else:
                        selected_player_pos = (c, r)
                        print(f"Selected {t.card.name} at {(c,r)} for movement (range {t.card.move_range}).")
                else:
                    print(f"Clicked tile {(c,r)} -> {t.card}")

    # update floating texts
    for ft in floating_texts[:]:
        ft.life -= dt
        ft.pos = (ft.pos[0], ft.pos[1] - dt * 30)
        if ft.life <= 0:
            floating_texts.remove(ft)

    draw_grid()
    pygame.display.flip()

pygame.quit()
