import random
import pygame
from colors import E_NULL, E_FIRE, E_WATER, E_LEAF, E_AIR, C_WHITE
from config import WIDTH, HEIGHT
from fonts import FONT_DMG

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
