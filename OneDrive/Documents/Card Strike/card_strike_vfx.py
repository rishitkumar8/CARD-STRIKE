import pygame
import os
import random
import math
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

# --- 1. CONFIGURATION & AESTHETICS ---
GRID_COLS, GRID_ROWS = 9, 5
TILE_SIZE = 96
WIDTH, HEIGHT = GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE + 150
FPS = 60

# Modern Color Palette (High Contrast)
C_BG = (20, 22, 30)            # Dark Navy Background
C_GRID = (40, 44, 60)          # Subtle Grid Lines
C_PANEL = (30, 34, 45)         # UI Panel
C_WHITE = (240, 240, 255)
C_HIGHLIGHT = (100, 200, 255)  # Cyan Highlight
C_SELECT = (255, 220, 50)      # Gold Selection
C_PLAYER = (80, 220, 100)      # Neon Green
C_ENEMY = (255, 80, 80)        # Neon Red

# Elemental Colors
E_FIRE = (255, 100, 50)
E_WATER = (50, 150, 255)
E_LEAF = (100, 255, 100)
E_AIR = (200, 255, 255)
E_NULL = (180, 100, 255)

pygame.init()
pygame.display.set_caption("Card Strike: Elemental GUI")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Fonts (Using system fonts for portability, but styled)
FONT_MAIN = pygame.font.SysFont("Arial", 16, bold=True)
FONT_BIG = pygame.font.SysFont("Arial", 24, bold=True)
FONT_DMG = pygame.font.SysFont("Impact", 32)

# --- 2. LOGIC MODELS (Kept mostly same, added Element type) ---
@dataclass
class Attack:
    name: str
    dmg: int
    element: str = "null" # fire, water, leaf, air, null

@dataclass
class Card:
    owner: str
    name: str
    hp: int
    max_hp: int
    attacks: List[Attack]
    move_range: int = 2
    element: str = "null" # Base element of the card
    index: int = 0

@dataclass
class Tile:
    col: int
    row: int
    card: Optional[Card] = None

class Grid:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.tiles = [[Tile(c, r) for r in range(rows)] for c in range(cols)]
    
    def in_bounds(self, c, r):
        return 0 <= c < self.cols and 0 <= r < self.rows

grid = Grid(GRID_COLS, GRID_ROWS)

# Global Effect Lists
flame_tiles = []      # (c, r, time_left)
regen_effects = []    # [card, heal_per_tick, time_left, (c,r)]
burn_effects = []     # [card, dmg_per_tick, time_left, (c,r)]

# --- 3. VFX ENGINE (The New Stuff) ---

class Particle:
    def __init__(self, x, y, color, size, velocity, life):
        self.x, self.y = x, y
        self.color = color
        self.size = size
        self.vx, self.vy = velocity
        self.life = life
        self.max_life = life
        self.gravity = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy + self.gravity
        self.life -= 1
        self.size *= 0.95 # Shrink over time

    def draw(self, surf):
        if self.life > 0 and self.size > 0.5:
            alpha = int((self.life / self.max_life) * 255)
            # Create a surface for transparency
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            surf.blit(s, (self.x - self.size, self.y - self.size))

class AnimationManager:
    def __init__(self):
        self.particles = []
        self.screenshake = 0
        self.projectiles = [] # (x, y, target_x, target_y, element, progress, callback)
        self.floating_texts = [] # (text, x, y, life, color)
        self.blocking = False # If true, stop input

    def add_particle(self, x, y, element):
        # Procedural particle generation based on element
        vx = random.uniform(-2, 2)
        vy = random.uniform(-2, 2)
        size = random.uniform(3, 6)
        life = random.randint(20, 40)
        
        color = E_NULL
        if element == 'fire': 
            color = (255, random.randint(50, 150), 0)
            vy -= 1 # Fire rises
        elif element == 'water': 
            color = (50, 100, random.randint(200, 255))
            vy += 0.5 # Water falls (drips)
        elif element == 'leaf':
            color = (50, 255, 50)
        elif element == 'air':
            color = (220, 255, 255)
            vx *= 2 # Air moves fast

        p = Particle(x, y, color, size, (vx, vy), life)
        if element == 'water': p.gravity = 0.1
        self.particles.append(p)

    def trigger_attack_anim(self, start_pos, end_pos, element, on_hit_callback):
        # Create a projectile
        sx, sy = start_pos
        ex, ey = end_pos
        # Store animation data
        self.projectiles.append({
            'start': (sx, sy),
            'curr': [sx, sy],
            'end': (ex, ey),
            'element': element,
            'progress': 0.0,
            'callback': on_hit_callback
        })
        self.blocking = True

    def add_floating_text(self, text, x, y, color=C_WHITE):
        self.floating_texts.append({'text': text, 'x': x, 'y': y, 'life': 60, 'color': color})

    def update(self):
        # Shake decay
        if self.screenshake > 0:
            self.screenshake -= 1

        # Update Particles
        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

        # Update Projectiles
        for proj in self.projectiles[:]:
            proj['progress'] += 0.05 # Speed of projectile
            t = proj['progress']
            
            # Linear interpolation
            start_x, start_y = proj['start']
            end_x, end_y = proj['end']
            
            curr_x = start_x + (end_x - start_x) * t
            curr_y = start_y + (end_y - start_y) * t
            proj['curr'] = [curr_x, curr_y]

            # Trail particles
            for _ in range(2):
                self.add_particle(curr_x, curr_y, proj['element'])

            if t >= 1.0:
                # HIT!
                self.screenshake = 10
                # Explosion particles
                for _ in range(20):
                    self.add_particle(end_x, end_y, proj['element'])
                
                # Execute logic callback (deal damage)
                proj['callback']()
                self.projectiles.remove(proj)
                if not self.projectiles:
                    self.blocking = False

        # Update Floating Text
        for ft in self.floating_texts[:]:
            ft['life'] -= 1
            ft['y'] -= 0.5
            if ft['life'] <= 0:
                self.floating_texts.remove(ft)

    def draw(self, surf):
        shake_x = random.randint(-self.screenshake, self.screenshake)
        shake_y = random.randint(-self.screenshake, self.screenshake)
        
        # We draw onto a temporary surface to handle shake, then blit to screen
        temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Draw Particles
        for p in self.particles:
            p.draw(temp_surf)
            
        # Draw Projectiles
        for proj in self.projectiles:
            cx, cy = proj['curr']
            color = E_NULL
            if proj['element'] == 'fire': color = E_FIRE
            elif proj['element'] == 'water': color = E_WATER
            elif proj['element'] == 'leaf': color = E_LEAF
            pygame.draw.circle(temp_surf, color, (int(cx), int(cy)), 10)
            pygame.draw.circle(temp_surf, C_WHITE, (int(cx), int(cy)), 5)

        # Draw Floating Text
        for ft in self.floating_texts:
            alpha = min(255, ft['life'] * 5)
            txt = FONT_DMG.render(ft['text'], True, ft['color'])
            txt.set_alpha(alpha)
            # Outline
            outline = FONT_DMG.render(ft['text'], True, (0,0,0))
            outline.set_alpha(alpha)
            temp_surf.blit(outline, (ft['x'] - txt.get_width()//2 + 2, ft['y'] - txt.get_height()//2 + 2))
            temp_surf.blit(txt, (ft['x'] - txt.get_width()//2, ft['y'] - txt.get_height()//2))

        surf.blit(temp_surf, (shake_x, shake_y))

anim_mgr = AnimationManager()

# --- 4. GAME HELPERS ---
def cell_center(c, r):
    return c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2

def create_player_card(slot_index: int) -> Card:
    # FIRE/LEAF MIXED CARD — ALL PLAYERS USE SAME ABILITIES
    attacks = [
        Attack("Burning Trail", dmg=12, element="fire"),
        Attack("Nature's Embrace", dmg=12, element="leaf"),
        Attack("Burning-Embrace Fusion", dmg=12, element="fire_leaf")
    ]

    return Card(
        owner="player",
        name=f"Hero {slot_index+1}",
        hp=80,
        max_hp=80,
        attacks=attacks,
        move_range=3,
        element="fire_leaf",
        index=slot_index
    )

def create_enemy_card(slot_index: int) -> Card:
    e = random.choice(['fire', 'water', 'leaf', 'null'])
    attacks = [
        Attack("Bite", dmg=10, element=e),
        Attack("Claw", dmg=14, element='null'),
    ]
    return Card(owner="enemy", name=f"Beast {slot_index+1}", hp=70, max_hp=70, attacks=attacks, move_range=2, element=e, index=slot_index)

# --- 5. LOGIC INTEGRATION (Connecting Logic to Animation) ---

def perform_attack_logic(ac, ar, tc, tr, atk):
    attacker = grid.tiles[ac][ar].card
    target = grid.tiles[tc][tr].card

    # ===========================================================
    # ABILITY 1 — Burning Trail (FIRE)
    # ===========================================================
    if atk.name == "Burning Trail":
        # Create 5 flame tiles in front direction
        dx = 1 if tc > ac else -1
        for i in range(1, 6):
            nc = ac + dx * i
            if 0 <= nc < GRID_COLS:
                flame_tiles.append([nc, ar, FPS * 3])  # 3 seconds flame
        anim_mgr.add_floating_text("🔥 TRAIL", *cell_center(ac, ar), E_FIRE)
        return

    # ===========================================================
    # ABILITY 2 — Nature’s Embrace (LEAF)
    # ===========================================================
    if atk.name == "Nature's Embrace":
        # Heal allies in plus pattern
        plus = [(tc, tr), (tc+1, tr), (tc-1, tr), (tc, tr+1), (tc, tr-1)]
        for (x, y) in plus:
            if grid.in_bounds(x,y) and grid.tiles[x][y].card:
                c = grid.tiles[x][y].card
                if c.owner == attacker.owner:
                    regen_effects.append([c, 5, FPS*3, (x,y)])  # heal over time
                    anim_mgr.add_floating_text("+HEAL", *cell_center(x,y), E_LEAF)
                else:
                    burn_effects.append([c, 10, FPS*2, (x,y)])  # thorn dmg
                    anim_mgr.add_floating_text("-THORN", *cell_center(x,y), (0,255,0))
        return

    # ===========================================================
    # ABILITY 3 — Fusion Attack
    # ===========================================================
    if atk.name == "Burning-Embrace Fusion":
        around = [
            (tc+1,tr), (tc-1,tr), (tc,tr+1), (tc,tr-1),
            (tc+1,tr+1), (tc-1,tr-1), (tc+1,tr-1), (tc-1,tr+1)
        ]

        for (x,y) in around:
            if grid.in_bounds(x,y) and grid.tiles[x][y].card:
                c = grid.tiles[x][y].card
                if c.owner == attacker.owner:
                    regen_effects.append([c, 5, FPS*2, (x,y)])
                    anim_mgr.add_floating_text("+FUSION HEAL", *cell_center(x,y), E_LEAF)
                else:
                    burn_effects.append([c, 10, FPS*2, (x,y)])
                    anim_mgr.add_floating_text("-FUSION FIRE", *cell_center(x,y), E_FIRE)
        return

    # ===========================================================
    # NORMAL ATTACK (Existing)
    # ===========================================================
    if target:
        dmg = atk.dmg + random.randint(-2,2)
        target.hp -= dmg
        anim_mgr.add_floating_text(f"-{dmg}", *cell_center(tc,tr))
        if target.hp <= 0:
            grid.tiles[tc][tr].card = None

def initiate_player_attack(player_idx, attack_idx, enemy_idx):
    global cpu_pending  # <<< ADDED
    if anim_mgr.blocking: return # Don't allow action during animation

    # Find Player
    pc_pos = None
    for c in range(grid.cols):
        for r in range(grid.rows):
            if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "player" and grid.tiles[c][r].card.index == player_idx:
                pc_pos = (c,r)
                break
    
    # Find Enemy
    ec_pos = None
    for c in range(grid.cols):
        for r in range(grid.rows):
            if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "enemy" and grid.tiles[c][r].card.index == enemy_idx:
                ec_pos = (c,r)
                break
    
    if pc_pos and ec_pos:
        card = grid.tiles[pc_pos[0]][pc_pos[1]].card
        if attack_idx < len(card.attacks):
            atk = card.attacks[attack_idx]
            
            # START ANIMATION
            start_pix = cell_center(*pc_pos)
            end_pix = cell_center(*ec_pos)
            
            # Lambda acts as the callback when animation finishes
            anim_mgr.trigger_attack_anim(start_pix, end_pix, atk.element, 
                                         lambda: perform_attack_logic(pc_pos[0], pc_pos[1], ec_pos[0], ec_pos[1], atk))
            cpu_pending = True  # <<< ADDED: schedule CPU to act after this player's attack

def cpu_turn():
    if anim_mgr.blocking: return

    enemies = []
    for c in range(grid.cols):
        for r in range(grid.rows):
            if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "enemy":
                enemies.append((c,r))
    
    players = []
    for c in range(grid.cols):
        for r in range(grid.rows):
            if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "player":
                players.append((c,r))
    
    if not players: return

    for e_pos in enemies:
        # Move Logic (Simple random move)
        e_card = grid.tiles[e_pos[0]][e_pos[1]].card
        
        # 1. Move
        possible_moves = []
        for c in range(max(0, e_pos[0]-2), min(GRID_COLS, e_pos[0]+3)):
            for r in range(max(0, e_pos[1]-2), min(GRID_ROWS, e_pos[1]+3)):
                if grid.tiles[c][r].card is None:
                    possible_moves.append((c,r))
        
        new_pos = e_pos
        if possible_moves and random.random() > 0.3:
            dest = random.choice(possible_moves)
            grid.tiles[dest[0]][dest[1]].card = e_card
            grid.tiles[e_pos[0]][e_pos[1]].card = None
            new_pos = dest
        
        # 2. Attack
        target_pos = random.choice(players)
        atk = random.choice(e_card.attacks)
        
        start_pix = cell_center(*new_pos)
        end_pix = cell_center(*target_pos)
        
        # Delay CPU attacks slightly for visual clarity in a real queue, 
        # but here we just trigger one.
        anim_mgr.trigger_attack_anim(start_pix, end_pix, atk.element,
                                     lambda: perform_attack_logic(new_pos[0], new_pos[1], target_pos[0], target_pos[1], atk))
        break # One enemy attacks per button press for clarity

# --- 6. DRAWING GUI ---

def draw_card_shape(surf, x, y, size, color, is_circle=False):
    # Cute shape drawing
    rect = pygame.Rect(x - size//2, y - size//2, size, size)
    if is_circle:
        pygame.draw.circle(surf, color, (x, y), size//2)
        # Shine
        pygame.draw.circle(surf, (255,255,255), (x - size//6, y - size//6), size//8)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=12)

def draw_ui():
    screen.fill(C_BG)

    # 1. Draw Grid
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, C_GRID, rect, 1)

            # Draw Flame Tiles
            for ft in flame_tiles:
                if ft[0] == c and ft[1] == r:
                    # Pulsing flame effect
                    alpha = int((ft[2] / (FPS * 3)) * 255)  # Fade over time
                    flame_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(flame_surf, (*E_FIRE, alpha), (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3)
                    screen.blit(flame_surf, (c*TILE_SIZE, r*TILE_SIZE))
                    break

            # Hover effect
            if (c,r) == hovered_cell:
                s = pygame.Surface((TILE_SIZE, TILE_SIZE))
                s.set_alpha(30)
                s.fill(C_HIGHLIGHT)
                screen.blit(s, (c*TILE_SIZE, r*TILE_SIZE))

    # 2. Draw Cards
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            card = grid.tiles[c][r].card
            if card:
                cx, cy = cell_center(c, r)
                color = C_PLAYER if card.owner == "player" else C_ENEMY
                
                # Draw Card Body
                draw_card_shape(screen, cx, cy, TILE_SIZE-10, color, is_circle=(card.owner=="enemy"))
                
                # Draw Element Indicator
                ec = E_NULL
                if card.element == 'fire': ec = E_FIRE
                elif card.element == 'water': ec = E_WATER
                elif card.element == 'leaf': ec = E_LEAF
                elif card.element == 'air': ec = E_AIR
                pygame.draw.circle(screen, ec, (cx + 25, cy - 25), 8)
                
                # HP Bar
                bar_w = 60
                bar_h = 6
                pct = card.hp / card.max_hp
                pygame.draw.rect(screen, (0,0,0), (cx-bar_w//2, cy+20, bar_w, bar_h))
                pygame.draw.rect(screen, (0,255,0) if card.owner=="player" else (255,0,0), (cx-bar_w//2, cy+20, int(bar_w*pct), bar_h))

                # ===============================
                #  CARD LABEL (PLAYER/ENEMY)
                # ===============================
                if card.owner == "player":
                    label = f"P{card.index + 1}"
                    label_color = C_PLAYER
                else:
                    label = f"E{card.index + 1}"
                    label_color = C_ENEMY

                label_surface = FONT_BIG.render(label, True, label_color)

                # Draw label ABOVE card (10 pixels above)
                screen.blit(
                    label_surface,
                    (cx - label_surface.get_width() // 2, cy - TILE_SIZE // 2 - 10)
                )

                # Selection Ring
                if selected_pos == (c,r):
                    pygame.draw.circle(screen, C_SELECT, (cx, cy), TILE_SIZE//2 - 2, 3)

    # 3. VFX Layer
    anim_mgr.draw(screen)

    # 4. HUD Layer (Bottom Panel)
    panel_y = GRID_ROWS * TILE_SIZE
    pygame.draw.rect(screen, C_PANEL, (0, panel_y, WIDTH, HEIGHT-panel_y))
    
    # Instructions
    info_text = "Controls: Click to Select/Move | 'M' for CPU | Keys 1-3 + (Q/W/E) for Attacks"
    screen.blit(FONT_MAIN.render(info_text, True, C_HIGHLIGHT), (20, panel_y + 10))
    
    # Player Stats
    x_offset = 20
    for i in range(3):
        # Find player
        found = False
        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                card = grid.tiles[c][r].card
                if card and card.owner == "player" and card.index == i:
                    found = True
                    txt = f"P{i+1}: {card.hp}HP [{card.element.upper()}]"
                    col = C_PLAYER
                    screen.blit(FONT_BIG.render(txt, True, col), (x_offset, panel_y + 40))
                    
                    # Attack hints
                    atk_txt = f"Q:{card.attacks[0].name}  W:{card.attacks[1].name}  E:{card.attacks[2].name}"
                    screen.blit(FONT_MAIN.render(atk_txt, True, (150,150,150)), (x_offset, panel_y + 70))
        
        if not found:
            screen.blit(FONT_MAIN.render(f"P{i+1}: --", True, (100,100,100)), (x_offset, panel_y + 40))
            
        x_offset += 250

# --- 7. MAIN LOOP ---

# Setup
selected_pos = None
hovered_cell = (0,0)
placing_phase = True
placed_count = 0

cpu_pending = False  # <<< ADDED: schedule CPU to act after player's action

running = True
while running:
    # Logic Update
    anim_mgr.update()

    # PROCESS FLAME TILES
    for ft in flame_tiles[:]:
        c, r, t = ft
        t -= 1
        ft[2] = t

        if t <= 0:
            flame_tiles.remove(ft)
            continue

        card = grid.tiles[c][r].card
        if card and card.owner == "enemy":
            card.hp -= 10
            anim_mgr.add_floating_text("-10🔥", *cell_center(c,r), E_FIRE)

    # PROCESS REGEN
    for eff in regen_effects[:]:
        card, heal, t, pos = eff
        t -= 1
        eff[2] = t
        card.hp = min(card.max_hp, card.hp + heal)
        anim_mgr.add_floating_text(f"+{heal}", *cell_center(*pos), E_LEAF)
        if t <= 0:
            regen_effects.remove(eff)

    # PROCESS BURN DOT
    for eff in burn_effects[:]:
        card, dmg, t, pos = eff
        t -= 1
        eff[2] = t
        card.hp -= dmg
        anim_mgr.add_floating_text(f"-{dmg}", *cell_center(*pos), E_FIRE)
        if card.hp <= 0:
            grid.tiles[pos[0]][pos[1]].card = None
        if t <= 0:
            burn_effects.remove(eff)

    # If CPU is pending and no animations are blocking, perform cpu_turn automatically
    if cpu_pending and not anim_mgr.blocking and not placing_phase:
        cpu_pending = False
        cpu_turn()

    mx, my = pygame.mouse.get_pos()
    hovered_cell = (mx // TILE_SIZE, my // TILE_SIZE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and not anim_mgr.blocking:
            c, r = hovered_cell
            if grid.in_bounds(c, r):
                if placing_phase:
                    if grid.tiles[c][r].card is None:
                        grid.tiles[c][r].card = create_player_card(placed_count)
                        placed_count += 1
                        anim_mgr.add_particle(*(cell_center(c,r)), 'leaf') # Spawn puff
                        if placed_count >= 3:
                            placing_phase = False
                            # Spawn enemies
                            empties = [(xx, yy) for xx in range(GRID_COLS) for yy in range(GRID_ROWS) if not grid.tiles[xx][yy].card]
                            for i in range(3):
                                ex, ey = random.choice(empties)
                                grid.tiles[ex][ey].card = create_enemy_card(i)
                                empties.remove((ex,ey))
                else:
                    # Gameplay clicks
                    clicked = grid.tiles[c][r].card
                    if clicked and clicked.owner == "player":
                        selected_pos = (c,r)
                    elif selected_pos:
                        # Move
                        sc, sr = selected_pos
                        mover = grid.tiles[sc][sr].card
                        dist = abs(c-sc) + abs(r-sr)
                        if mover and dist <= mover.move_range and not clicked:
                            grid.tiles[c][r].card = mover
                            grid.tiles[sc][sr].card = None
                            selected_pos = None
                            anim_mgr.add_particle(*(cell_center(c,r)), 'air') # Dash effect
                            cpu_pending = True  # <<< ADDED: schedule CPU to act after this player's move

        if event.type == pygame.KEYDOWN and not placing_phase and not anim_mgr.blocking:
            if event.key == pygame.K_m:
                cpu_turn()
            
            # Key Mapping for attacks
            # Structure: Key -> (PlayerIndex, AttackIndex)
            controls = {
                pygame.K_q: (0,0), pygame.K_w: (0,1), pygame.K_e: (0,2),
                pygame.K_a: (1,0), pygame.K_s: (1,1), pygame.K_d: (1,2),
                pygame.K_z: (2,0), pygame.K_x: (2,1), pygame.K_c: (2,2),
            }
            
            if event.key in controls:
                pid, aid = controls[event.key]
                # Check if we are holding a number key for targeting
                keys = pygame.key.get_pressed()
                target_idx = -1
                if keys[pygame.K_1]: target_idx = 0
                elif keys[pygame.K_2]: target_idx = 1
                elif keys[pygame.K_3]: target_idx = 2
                
                if target_idx != -1:
                    initiate_player_attack(pid, aid, target_idx)
                    cpu_pending = True  # <<< ADDED: schedule CPU to act after this player's attack
                else:
                    anim_mgr.add_floating_text("Hold 1/2/3!", mx, my, (255, 255, 0))

    draw_ui()
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
