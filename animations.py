import random
import math
import pygame
import json
import os
from colors import E_NULL, E_FIRE, E_WATER, E_LEAF, E_AIR, C_WHITE
from config import WIDTH, HEIGHT
from fonts import FONT_DMG

# Load animation data from JSON
def load_animation_data():
    json_path = os.path.join(os.path.dirname(__file__), "cards.json")
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data.get("animation_types", {})
    except:
        return {}

ANIMATION_TYPES = load_animation_data()

class Particle:
    def __init__(self, x, y, color, size, velocity, life):
        self.x, self.y = x, y
        self.color = color
        self.size = size
        self.vx, self.vy = velocity
        self.life = life
        self.max_life = life
        self.gravity = 0
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy + self.gravity
        self.life -= 1
        self.size *= 0.96
        self.rotation += self.rot_speed

    def draw(self, surf):
        if self.life > 0 and self.size > 0.5:
            alpha = int((self.life / self.max_life) * 255)
            pygame.draw.circle(surf, (*self.color, alpha), (int(self.x), int(self.y)), int(self.size))

class SlashEffect:
    """Arc slash animation for wind attacks"""
    def __init__(self, x, y, target_x, target_y, color, arc_angle=120):
        self.x, self.y = x, y
        self.target_x, self.target_y = target_x, target_y
        self.color = color
        self.arc_angle = arc_angle
        self.progress = 0
        self.life = 20
        self.angle = math.atan2(target_y - y, target_x - x)
        
    def update(self):
        self.progress += 0.1
        self.life -= 1
        
    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 20) * 255)
        
        # Draw arc
        radius = 40 + self.progress * 60
        start_angle = self.angle - math.radians(self.arc_angle / 2)
        end_angle = self.angle + math.radians(self.arc_angle / 2)
        
        # Draw directly to surf
        rect = pygame.Rect(self.x + ox - radius, self.y + oy - radius, radius * 2, radius * 2)
        for i in range(3):
            pygame.draw.arc(surf, (*self.color, alpha), rect, start_angle, end_angle, 4 - i)
class BeamEffect:
    """Beam animation for null attacks"""
    def __init__(self, start_x, start_y, end_x, end_y, color, glitch_color, width=8):
        self.start_x, self.start_y = start_x, start_y
        self.end_x, self.end_y = end_x, end_y
        self.color = color
        self.glitch_color = glitch_color
        self.width = width
        self.progress = 0
        self.life = 30
        self.glitch_offset = 0
        
    def update(self):
        self.progress += 0.05
        self.life -= 1
        self.glitch_offset = random.randint(-5, 5)
        
    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 30) * 255)
        
        # Calculate current beam end
        curr_x = self.start_x + (self.end_x - self.start_x) * min(1, self.progress * 2)
        curr_y = self.start_y + (self.end_y - self.start_y) * min(1, self.progress * 2)
        
        # Draw glitch lines
        for i in range(-2, 3):
            offset = i * 3 + self.glitch_offset
            pygame.draw.line(surf, (*self.glitch_color, alpha // 2), 
                           (self.start_x + offset + ox, self.start_y + oy),
                           (curr_x + offset + ox, curr_y + oy), 2)
        
        # Main beam
        pygame.draw.line(surf, (*self.color, alpha), 
                        (self.start_x + ox, self.start_y + oy),
                        (curr_x + ox, curr_y + oy), self.width)

class AOEEffect:
    """Area of effect expanding ring"""
    def __init__(self, x, y, color, ring_color, max_radius=60):
        self.x, self.y = x, y
        self.color = color
        self.ring_color = ring_color
        self.max_radius = max_radius
        self.radius = 0
        self.life = 40
        
    def update(self):
        self.radius += 3
        self.life -= 1
        
    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 40) * 180)
        
        # Draw directly to surf using draw calls
        pygame.draw.circle(surf, (*self.color, alpha // 3), (int(self.x + ox), int(self.y + oy)), int(self.radius))
        if self.radius > 2:
            pygame.draw.circle(surf, (*self.ring_color, alpha), (int(self.x + ox), int(self.y + oy)), int(self.radius), 4)

class VineEffect:
    """Vine whip animation"""
    def __init__(self, start_x, start_y, end_x, end_y, color, segments=5):
        self.start_x, self.start_y = start_x, start_y
        self.end_x, self.end_y = end_x, end_y
        self.color = color
        self.segments = segments
        self.progress = 0
        self.life = 25
        self.wave_offset = 0
        
    def update(self):
        self.progress += 0.08
        self.life -= 1
        self.wave_offset += 0.3
        
    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 25) * 255)
        
        points = []
        for i in range(self.segments + 1):
            t = i / self.segments * min(1, self.progress)
            x = self.start_x + (self.end_x - self.start_x) * t
            y = self.start_y + (self.end_y - self.start_y) * t
            
            # Add wave motion
            wave = math.sin(t * math.pi * 3 + self.wave_offset) * 15 * (1 - t)
            perp_angle = math.atan2(self.end_y - self.start_y, self.end_x - self.start_x) + math.pi/2
            x += math.cos(perp_angle) * wave
            y += math.sin(perp_angle) * wave
            
            points.append((int(x + ox), int(y + oy)))
        
        if len(points) > 1:
            pygame.draw.lines(surf, (*self.color, alpha), False, points, 6)
            # Thorns
            for i, (px, py) in enumerate(points[1:-1]):
                if i % 2 == 0:
                    pygame.draw.circle(surf, (50, 150, 50), (px, py), 4)

class WhirlwindEffect:
    """Rotating whirlwind animation"""
    def __init__(self, x, y, color, radius=50):
        self.x, self.y = x, y
        self.color = color
        self.radius = radius
        self.rotation = 0
        self.life = 35
        
    def update(self):
        self.rotation += 0.2
        self.life -= 1
        
    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 35) * 200)
        
        # Draw spiral arms
        for arm in range(4):
            angle_offset = arm * math.pi / 2
            for i in range(8):
                r = self.radius * (i / 8)
                angle = self.rotation + angle_offset + i * 0.5
                x = self.x + math.cos(angle) * r
                y = self.y + math.sin(angle) * r
                size = 5 - i * 0.5
                if size > 0:
                    pygame.draw.circle(surf, (*self.color, alpha), (int(x + ox), int(y + oy)), int(size))

class HealEffect:
    """Healing particles rising up"""
    def __init__(self, x, y, color, particle_count=20):
        self.x, self.y = x, y
        self.color = color
        self.particles = []
        self.life = 40
        
        for _ in range(particle_count):
            self.particles.append({
                'x': x + random.randint(-30, 30),
                'y': y + random.randint(-30, 30),
                'vy': random.uniform(-2, -1),
                'size': random.randint(3, 6),
                'alpha': 255
            })
    
    def update(self):
        self.life -= 1
        for p in self.particles:
            p['y'] += p['vy']
            p['alpha'] = max(0, p['alpha'] - 6)
            
    def draw(self, surf, ox=0, oy=0):
        for p in self.particles:
            if p['alpha'] > 0:
                pygame.draw.circle(surf, (*self.color, int(p['alpha'])), 
                                 (int(p['x'] + ox), int(p['y'] + oy)), p['size'])
class SteamEffect:
    """Steam burst animation"""
    def __init__(self, x, y, color, radius=40):
        self.x, self.y = x, y
        self.color = color
        self.radius = radius
        self.particles = []
        self.life = 30
        
        for _ in range(25):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 1,
                'size': random.randint(4, 10),
                'alpha': 200
            })
    
    def update(self):
        self.life -= 1
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] -= 0.05  # Rise up
            p['size'] *= 1.02  # Expand
            p['alpha'] = max(0, p['alpha'] - 7)
            
    def draw(self, surf, ox=0, oy=0):
        for p in self.particles:
            if p['alpha'] > 0:
                pygame.draw.circle(surf, (*self.color, int(p['alpha'])), 
                                 (int(p['x'] + ox), int(p['y'] + oy)), int(p['size']))

class GlitchEffect:
    """Digital glitch animation for null attacks"""
    def __init__(self, x, y, color, glitch_color, size=50):
        self.x, self.y = x, y
        self.color = color
        self.glitch_color = glitch_color
        self.size = size
        self.life = 25
        self.glitch_lines = []
        
    def update(self):
        self.life -= 1
        self.glitch_lines = [(random.randint(-self.size, self.size), 
                              random.randint(-self.size, self.size)) for _ in range(5)]
        
    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 25) * 200)
        
        # Glitch squares — directly to surf
        for gx, gy in self.glitch_lines:
            size = random.randint(5, 20)
            color = self.color if random.random() > 0.5 else self.glitch_color
            rect = pygame.Rect(self.x + ox + gx - size//2, self.y + oy + gy - size//2, size, size)
            pygame.draw.rect(surf, (*color, alpha), rect)


class StrikeEffect:
    """Quick impact flash — used for backstab, counter, dash hits"""
    def __init__(self, x, y, color, flash_color):
        self.x, self.y = x, y
        self.color = color
        self.flash_color = flash_color
        self.life = 18
        self.radius = 5

    def update(self):
        self.life -= 1
        self.radius += 5

    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 18) * 255)
        cx, cy = self.x + ox, self.y + oy
        # Expanding ring
        if self.radius > 2:
            pygame.draw.circle(surf, (*self.flash_color, alpha), (int(cx), int(cy)), self.radius, 4)
        # Cross slash lines
        length = self.radius
        for angle in [0, math.pi/4, math.pi/2, 3*math.pi/4]:
            x1 = int(cx + math.cos(angle) * length)
            y1 = int(cy + math.sin(angle) * length)
            x2 = int(cx - math.cos(angle) * length)
            y2 = int(cy - math.sin(angle) * length)
            pygame.draw.line(surf, (*self.color, alpha), (x1, y1), (x2, y2), 3)
        # Core flash
        if self.life > 10:
            pygame.draw.circle(surf, (*self.flash_color, min(255, alpha * 2)), (int(cx), int(cy)), 8)


class SplashEffect:
    """Water splash with droplets arcing outward"""
    def __init__(self, x, y, color, droplet_color, radius=50, droplet_count=12):
        self.x, self.y = x, y
        self.color = color
        self.droplet_color = droplet_color
        self.radius = radius
        self.life = 30
        self.droplets = []
        for _ in range(droplet_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self.droplets.append({
                'x': float(x), 'y': float(y),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 2,
                'size': random.randint(3, 7),
                'alpha': 255
            })

    def update(self):
        self.life -= 1
        for d in self.droplets:
            d['x'] += d['vx']
            d['y'] += d['vy']
            d['vy'] += 0.15
            d['alpha'] = max(0, d['alpha'] - 8)
            d['size'] = max(0.5, d['size'] * 0.97)

    def draw(self, surf, ox=0, oy=0):
        for d in self.droplets:
            if d['alpha'] > 0 and d['size'] > 0.5:
                pygame.draw.circle(surf, (*self.droplet_color, int(d['alpha'])), 
                                 (int(d['x'] + ox), int(d['y'] + oy)), int(d['size']))
        # Central ring
        if self.life > 10:
            ring_a = int((self.life - 10) / 20 * 200)
            ring_r = max(1, (30 - self.life) * 3)
            pygame.draw.circle(surf, (*self.color, ring_a), (int(self.x + ox), int(self.y + oy)), ring_r, 3)


class TrapEffect:
    """Grid-pattern trap — digital trap for null attacks"""
    def __init__(self, x, y, color, grid_color, size=50):
        self.x, self.y = x, y
        self.color = color
        self.grid_color = grid_color
        self.size = size
        self.life = 30
        self.progress = 0.0

    def update(self):
        self.life -= 1
        self.progress = min(1.0, self.progress + 0.08)

    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 30) * 200)
        cx, cy = self.x + ox, self.y + oy
        step = 12
        extent = int(self.size * self.progress)
        for i in range(-extent, extent + 1, step):
            pygame.draw.line(surf, (*self.grid_color, alpha // 2), (cx + i, cy - extent), (cx + i, cy + extent), 1)
            pygame.draw.line(surf, (*self.grid_color, alpha // 2), (cx - extent, cy + i), (cx + extent, cy + i), 1)
        # Diamond border
        pts = [(cx, cy - extent), (cx + extent, cy), (cx, cy + extent), (cx - extent, cy)]
        if extent > 4:
            pygame.draw.polygon(surf, (*self.color, alpha), pts, 3)
        # Pulsing core
        core_a = int(alpha * (0.5 + 0.5 * math.sin(self.progress * 10)))
        pygame.draw.circle(surf, (*self.color, core_a), (int(cx), int(cy)), 6)


class WaveEffect:
    """Expanding wave sweep"""
    def __init__(self, sx, sy, ex, ey, color, width=60):
        self.sx, self.sy = sx, sy
        self.ex, self.ey = ex, ey
        self.color = color
        self.width = width
        self.life = 25
        self.progress = 0.0

    def update(self):
        self.life -= 1
        self.progress = min(1.0, self.progress + 0.06)

    def draw(self, surf, ox=0, oy=0):
        if self.life <= 0:
            return
        alpha = int((self.life / 25) * 200)
        # Current wave front position
        fx = self.sx + (self.ex - self.sx) * self.progress
        fy = self.sy + (self.ey - self.sy) * self.progress
        # Perpendicular direction
        angle = math.atan2(self.ey - self.sy, self.ex - self.sx) + math.pi / 2
        hw = self.width * self.progress
        x1 = int(fx + math.cos(angle) * hw + ox)
        y1 = int(fy + math.sin(angle) * hw + oy)
        x2 = int(fx - math.cos(angle) * hw + ox)
        y2 = int(fy - math.sin(angle) * hw + oy)
        pygame.draw.line(surf, (*self.color, alpha), (x1, y1), (x2, y2), 6)
        # Trailing arcs
        for i in range(3):
            t = max(0, self.progress - i * 0.12)
            bx = self.sx + (self.ex - self.sx) * t
            by = self.sy + (self.ey - self.sy) * t
            ba = max(0, alpha - i * 60)
            bw = self.width * t * 0.6
            bx1 = int(bx + math.cos(angle) * bw + ox)
            by1 = int(by + math.sin(angle) * bw + oy)
            bx2 = int(bx - math.cos(angle) * bw + ox)
            by2 = int(by - math.sin(angle) * bw + oy)
            pygame.draw.line(surf, (*self.color, ba), (bx1, by1), (bx2, by2), 3)

class AnimationManager:
    def __init__(self):
        self.particles = []
        self.screenshake = 0
        self.projectiles = []
        self.floating_texts = []
        self.special_effects = []  # New: for complex effects
        self.blocking = False

    def add_particle(self, x, y, element):
        vx = random.uniform(-2, 2)
        vy = random.uniform(-2, 2)
        size = random.uniform(3, 6)
        life = random.randint(20, 40)
        
        color = E_NULL
        if element == 'fire': 
            color = (255, random.randint(50, 150), 0)
            vy -= 1
        elif element == 'water': 
            color = (50, 100, random.randint(200, 255))
            vy += 0.5
        elif element == 'leaf':
            color = (50, 255, 50)
        elif element == 'air' or element == 'wind':
            color = (220, 255, 255)
            vx *= 2
        elif element == 'null':
            color = (180, 100, random.randint(200, 255))
        elif element == 'combined':
            color = (255, random.randint(150, 200), 100)

        p = Particle(x, y, color, size, (vx, vy), life)
        if element == 'water': p.gravity = 0.1
        self.particles.append(p)

    def trigger_attack_anim(self, start_pos, end_pos, element, on_hit_callback, anim_type=None):
        sx, sy = start_pos
        ex, ey = end_pos
        
        # Get animation config if available
        anim_config = ANIMATION_TYPES.get(anim_type, {})
        anim_category = anim_config.get('type', 'projectile')
        
        # Create special effects based on animation type
        if anim_category == 'slash':
            color = tuple(anim_config.get('color', [200, 220, 255]))
            self.special_effects.append(SlashEffect(sx, sy, ex, ey, color))
        elif anim_category == 'beam':
            color = tuple(anim_config.get('color', [180, 100, 220]))
            glitch_color = tuple(anim_config.get('glitch_color', [100, 255, 200]))
            self.special_effects.append(BeamEffect(sx, sy, ex, ey, color, glitch_color))
        elif anim_category in ('aoe', 'aura', 'burst'):
            color = tuple(anim_config.get('color', [255, 80, 30]))
            ring_color = tuple(anim_config.get('ring_color', anim_config.get('splash_color', [255, 200, 50])))
            self.special_effects.append(AOEEffect(ex, ey, color, ring_color))
        elif anim_category == 'vine':
            color = tuple(anim_config.get('color', [80, 200, 80]))
            self.special_effects.append(VineEffect(sx, sy, ex, ey, color))
        elif anim_category == 'whirl':
            color = tuple(anim_config.get('color', [200, 220, 255]))
            self.special_effects.append(WhirlwindEffect(ex, ey, color))
        elif anim_category == 'heal':
            color = tuple(anim_config.get('color', [100, 255, 100]))
            self.special_effects.append(HealEffect(ex, ey, color))
        elif anim_category == 'steam':
            color = tuple(anim_config.get('color', [200, 200, 220]))
            self.special_effects.append(SteamEffect(ex, ey, color))
        elif anim_category == 'glitch':
            color = tuple(anim_config.get('color', [180, 100, 220]))
            glitch_color = tuple(anim_config.get('glitch_color', [100, 255, 200]))
            self.special_effects.append(GlitchEffect(ex, ey, color, glitch_color))
        elif anim_category in ('splash',):
            color = tuple(anim_config.get('color', [50, 150, 255]))
            droplet_color = tuple(anim_config.get('droplet_color', [150, 220, 255]))
            self.special_effects.append(SplashEffect(ex, ey, color, droplet_color))
        elif anim_category in ('strike', 'counter', 'dash'):
            color = tuple(anim_config.get('color', [255, 255, 255]))
            flash_color = tuple(anim_config.get('flash_color', anim_config.get('trail_color', [255, 255, 200])))
            self.special_effects.append(StrikeEffect(ex, ey, color, flash_color))
        elif anim_category == 'wave':
            color = tuple(anim_config.get('color', anim_config.get('wave_color', [50, 150, 255])))
            self.special_effects.append(WaveEffect(sx, sy, ex, ey, color))
        elif anim_category == 'trap':
            color = tuple(anim_config.get('color', [180, 100, 220]))
            grid_color = tuple(anim_config.get('grid_color', [100, 255, 200]))
            self.special_effects.append(TrapEffect(ex, ey, color, grid_color))
        elif anim_category == 'trail':
            color = tuple(anim_config.get('color', [255, 100, 30]))
            flame_color = tuple(anim_config.get('flame_color', [255, 200, 50]))
            self.special_effects.append(AOEEffect(ex, ey, color, flame_color))
        elif anim_category in ('heal_whirl', 'vine_whirl'):
            # Combined effects
            color = tuple(anim_config.get('color', [100, 255, 100]))
            self.special_effects.append(HealEffect(ex, ey, color) if 'heal' in anim_category else VineEffect(sx, sy, ex, ey, color))
            spiral_color = tuple(anim_config.get('spiral_color', [200, 255, 200]))
            self.special_effects.append(WhirlwindEffect(ex, ey, spiral_color))
        else:
            # Fallback: projectile burst at target
            elem_colors = {'fire': [255,100,30], 'water': [50,150,255], 'leaf': [80,200,80],
                           'wind': [200,220,255], 'air': [200,220,255], 'null': [180,100,220]}
            fb_color = tuple(elem_colors.get(element, [200, 200, 200]))
            self.special_effects.append(AOEEffect(ex, ey, fb_color, fb_color))
        
        # Also create projectile for visual travel
        speed = anim_config.get('speed', 0.05)
        self.projectiles.append({
            'start': (sx, sy),
            'curr': [sx, sy],
            'end': (ex, ey),
            'element': element,
            'progress': 0.0,
            'speed': speed,
            'callback': on_hit_callback,
            'anim_type': anim_type
        })
        self.blocking = True

    def trigger_move_anim(self, start_pos, end_pos, on_arrive_callback):
        sx, sy = start_pos
        ex, ey = end_pos
        self.projectiles.append({
            'start': (sx, sy),
            'curr': [sx, sy],
            'end': (ex, ey),
            'element': 'move',
            'progress': 0.0,
            'speed': 0.08,
            'callback': on_arrive_callback,
            'anim_type': None
        })
        self.blocking = True

    def add_floating_text(self, text, x, y, color=C_WHITE):
        self.floating_texts.append({'text': text, 'x': x, 'y': y, 'life': 60, 'color': color})

    def update(self):
        if self.screenshake > 0:
            self.screenshake -= 1

        # Update Particles
        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

        # Update Special Effects
        for effect in self.special_effects[:]:
            effect.update()
            if effect.life <= 0:
                self.special_effects.remove(effect)

        # Update Projectiles
        for proj in self.projectiles[:]:
            proj['progress'] += proj.get('speed', 0.05)
            t = proj['progress']
            
            start_x, start_y = proj['start']
            end_x, end_y = proj['end']
            
            curr_x = start_x + (end_x - start_x) * t
            curr_y = start_y + (end_y - start_y) * t
            proj['curr'] = [curr_x, curr_y]

            # Trail particles
            for _ in range(2):
                self.add_particle(curr_x, curr_y, proj['element'])

            if t >= 1.0:
                self.screenshake = 10
                for _ in range(20):
                    self.add_particle(end_x, end_y, proj['element'])
                
                try:
                    proj['callback']()
                except Exception as e:
                    import logging
                    logging.error(f"Animation callback crashed: {e}", exc_info=True)
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
        shake_x = random.randint(-self.screenshake, self.screenshake) if self.screenshake > 0 else 0
        shake_y = random.randint(-self.screenshake, self.screenshake) if self.screenshake > 0 else 0
        
        # Draw everything directly onto surf with shake offset
        # Draw Particles
        for p in self.particles:
            p.draw(surf) # Particles already draw directly, could add shake if needed
        
        # Draw Special Effects
        for effect in self.special_effects:
            effect.draw(surf, ox=shake_x, oy=shake_y)
            
        # Draw Projectiles
        for proj in self.projectiles:
            cx, cy = proj['curr']
            cx += shake_x
            cy += shake_y
            color = E_NULL
            elem = proj['element']
            if elem == 'fire': color = E_FIRE
            elif elem == 'water': color = E_WATER
            elif elem == 'leaf': color = E_LEAF
            elif elem == 'wind' or elem == 'air': color = (200, 220, 255)
            elif elem == 'null': color = (180, 100, 220)
            elif elem == 'combined': color = (255, 200, 100)

            # Outer glow — draw directly
            pygame.draw.circle(surf, (*color, 60), (int(cx), int(cy)), 18)
            # Main orb
            pygame.draw.circle(surf, color, (int(cx), int(cy)), 10)
            # Core
            pygame.draw.circle(surf, C_WHITE, (int(cx), int(cy)), 5)
            # Streak tail
            prog = proj.get('progress', 0)
            if prog > 0.1:
                sx2, sy2 = proj['start']
                tail_t = max(0, prog - 0.15)
                tx = sx2 + (proj['end'][0] - sx2) * tail_t + shake_x
                ty = sy2 + (proj['end'][1] - sy2) * tail_t + shake_y
                pygame.draw.line(surf, (*color, 120), (int(tx), int(ty)), (int(cx), int(cy)), 4)

        # Draw Floating Text
        for ft in self.floating_texts:
            alpha = min(255, ft['life'] * 5)
            txt = FONT_DMG.render(ft['text'], True, ft['color'])
            txt.set_alpha(alpha)
            # No outline for speed unless requested, or use simple 1px offset
            surf.blit(txt, (ft['x'] - txt.get_width()//2 + shake_x, ft['y'] - txt.get_height()//2 + shake_y))

anim_mgr = AnimationManager()
