"""
Tank Assault 3D - Enhanced Edition
A 3D tank combat game with dynamic weather, day/night cycles, and enemy AI.

Features (26 total):
- Player movement and turret control
- Enemy AI with shooting capabilities
- Dynamic day/night cycle with weather system
- Shield power-ups and health system
- Multiple difficulty levels
- Pause menu and game state management
- Camera modes and effects
- Collision detection and physics
"""

# ============ IMPORTS ============
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24
import math
import random
import time


# ============ CONFIGURATION ============
class GameSettings:
    """Centralized game configuration and constants."""
    
    # Display settings
    DISPLAY_DIM = (1000, 800)
    ARENA_RADIUS = 1250
    CAM_FOV = 110
    
    # Player settings
    PLAYER_MAX_HP = 100
    PLAYER_SIZE = 28.0
    MOVE_RATE = 14.5
    TURN_RATE = 3.8
    
    # Weapon settings
    BULLET_VELOCITY = 20.0
    BULLET_SIZE = 6.0
    
    # Enemy settings
    ENEMY_MAX = 5
    ENEMY_SIZE = 28.0
    ENEMY_VELOCITY = 3.2
    ENEMY_BULLET_VELOCITY = 18.0
    ENEMY_BULLET_DAMAGE = 2.5
    
    # Environment settings
    RAIN_DENSITY = 600
    RAIN_RANGE = 400
    RAIN_SPEED = 45.0
    DAY_DURATION = 60.0
    
    # Difficulty configurations
    DIFFICULTY_SETTINGS = {
        'Easy': {'enemy_count': 2, 'scaling_rate': 0.5},
        'Medium': {'enemy_count': 3, 'scaling_rate': 1.0},
        'Hard': {'enemy_count': 5, 'scaling_rate': 1.5}
    }
    
    # Power-up settings
    SHIELD_SPAWN_INTERVAL = 15.0
    SHIELD_DURATION_MIN = 5.0
    SHIELD_DURATION_MAX = 15.0
    SHIELD_RADIUS = 20.0


# ============ GAME STATE ENUM ============
class GameState:
    """Enumeration of possible game states."""
    MENU = "menu"
    DIFFICULTY_SELECT = "difficulty_select"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


# ============ UTILITY CLASSES ============
class Vec:
    """3D vector class for position and movement."""
    
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z
    
    def move(self, dx, dy, dz=0):
        """Return a new Vec moved by the given deltas."""
        return Vec(self.x + dx, self.y + dy, self.z + dz)
    
    def distance(self, other):
        """Calculate 2D distance to another Vec."""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
    
    def constrain(self, limit):
        """Return a new Vec constrained within +/- limit."""
        return Vec(
            max(-limit, min(limit, self.x)),
            max(-limit, min(limit, self.y)),
            self.z
        )


# ============ BUTTON CLASS ============
class Button:
    """Interactive button for menu system."""
    
    def __init__(self, x, y, width, height, text, callback=None):
        """
        Initialize a button.
        
        Args:
            x, y: Bottom-left position in screen coordinates
            width, height: Button dimensions
            text: Display text
            callback: Optional function to call on click
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.callback = callback
        self.hovered = False
    
    def is_clicked(self, mouse_x, mouse_y):
        """Check if mouse click is within button bounds."""
        gl_y = GameSettings.DISPLAY_DIM[1] - mouse_y
        return (self.x <= mouse_x <= self.x + self.width and
                self.y <= gl_y <= self.y + self.height)
    
    def is_hovered(self, mouse_x, mouse_y):
        """Check if mouse is hovering over button."""
        gl_y = GameSettings.DISPLAY_DIM[1] - mouse_y
        return (self.x <= mouse_x <= self.x + self.width and
                self.y <= gl_y <= self.y + self.height)
    
    def draw(self, mouse_x=None, mouse_y=None):
        """Draw the button with hover effect."""
        if mouse_x is not None and mouse_y is not None:
            self.hovered = self.is_hovered(mouse_x, mouse_y)
        
        # Draw button background
        color = (0.3, 0.5, 0.8) if self.hovered else (0.2, 0.4, 0.7)
        glColor3f(*color)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()
        
        # Draw button border
        glColor3f(1, 1, 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()


# ============ MATH UTILITIES ============
def lerp_color(c1, c2, t):
    """Linear interpolation between two RGB colors."""
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t
    )


def check_aabb_collision(pos1, size1, pos2, size2):
    """
    Axis-Aligned Bounding Box collision detection.
    
    Args:
        pos1, pos2: Vec objects representing positions
        size1, size2: Half-sizes of the bounding boxes
    
    Returns:
        bool: True if collision detected
    """
    dx = abs(pos1.x - pos2.x)
    dy = abs(pos1.y - pos2.y)
    return (dx < (size1 + size2)) and (dy < (size1 + size2))


# ============ BASE GAME OBJECT ============
class GameObject:
    """Base class for all game entities."""
    
    def __init__(self, pos):
        self.pos = pos
        self.alive = True
    
    def tick(self, dt):
        """Update object state (override in subclasses)."""
        pass
    
    def draw(self):
        """Render object (override in subclasses)."""
        pass


# ============ ENVIRONMENT SYSTEMS ============
class DayNightCycle:
    """Manages dynamic day/night cycle with color transitions."""
    
    def __init__(self):
        self.game_time = 12.0  # Start at noon
        self.sky_color = (0.4, 0.6, 0.9)
        self.ground_brightness = 1.0
        
        # Key time points and their sky colors
        self.colors = {
            0: (0.05, 0.05, 0.1),      # Midnight
            6: (0.8, 0.5, 0.2),         # Dawn
            12: (0.4, 0.6, 0.9),        # Noon
            18: (0.7, 0.3, 0.4),        # Dusk
            24: (0.05, 0.05, 0.1)       # Midnight
        }
    
    def update(self, dt):
        """Advance time and update colors."""
        hours_per_sec = 24.0 / GameSettings.DAY_DURATION
        self.game_time = (self.game_time + dt * hours_per_sec) % 24
        self.calculate_sky_color()
    
    def calculate_sky_color(self):
        """Interpolate sky color based on current time."""
        times = sorted(self.colors.keys())
        t1, t2 = 0, 24
        
        # Find the two key times we're between
        for i in range(len(times) - 1):
            if times[i] <= self.game_time < times[i + 1]:
                t1 = times[i]
                t2 = times[i + 1]
                break
        
        # Interpolate colors
        fraction = (self.game_time - t1) / (t2 - t1)
        c1 = self.colors[t1]
        c2 = self.colors[t2]
        self.sky_color = lerp_color(c1, c2, fraction)
        
        # Calculate ground brightness (brightest at noon)
        dist_from_noon = abs(12 - self.game_time)
        self.ground_brightness = max(0.3, 1.0 - (dist_from_noon / 12.0) * 0.7)
    
    def get_display_color(self, is_raining):
        """Get current sky color, adjusted for weather."""
        base = self.sky_color
        if is_raining:
            rain_gray = (0.3, 0.35, 0.45)
            rain_factor = self.ground_brightness
            adjusted_rain = (
                rain_gray[0] * rain_factor,
                rain_gray[1] * rain_factor,
                rain_gray[2] * rain_factor
            )
            return lerp_color(base, adjusted_rain, 0.7)
        return base
    
    def get_time_string(self):
        """Format current time as HH:MM string."""
        hours = int(self.game_time)
        minutes = int((self.game_time - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"


class WeatherSystem:
    """Manages dynamic weather with animated rain."""
    
    def __init__(self):
        self.raining = False
        self.next_change = time.time() + random.uniform(5, 10)
        self.drops = []
        
        # Pre-create rain drop objects
        for _ in range(GameSettings.RAIN_DENSITY):
            self.drops.append({
                'x': 0,
                'y': 0,
                'z': random.uniform(0, 300),
                'speed': random.uniform(
                    GameSettings.RAIN_SPEED * 0.8,
                    GameSettings.RAIN_SPEED * 1.2
                ),
                'active': False
            })
    
    def update(self, player_pos):
        """Update weather state and rain drop positions."""
        now = time.time()
        
        # Toggle rain state randomly
        if now > self.next_change:
            self.raining = not self.raining
            duration = (random.uniform(15, 25) if self.raining 
                       else random.uniform(20, 40))
            self.next_change = now + duration
        
        # Update active rain drops
        if self.raining:
            for drop in self.drops:
                if not drop['active']:
                    # Activate and position drop around player
                    drop['active'] = True
                    drop['x'] = player_pos.x + random.uniform(
                        -GameSettings.RAIN_RANGE, GameSettings.RAIN_RANGE
                    )
                    drop['y'] = player_pos.y + random.uniform(
                        -GameSettings.RAIN_RANGE, GameSettings.RAIN_RANGE
                    )
                    drop['z'] = random.uniform(200, 300)
                
                drop['z'] -= drop['speed']
                
                # Reset drop when it hits ground
                if drop['z'] < 0:
                    drop['z'] = random.uniform(200, 300)
                    drop['x'] = player_pos.x + random.uniform(
                        -GameSettings.RAIN_RANGE, GameSettings.RAIN_RANGE
                    )
                    drop['y'] = player_pos.y + random.uniform(
                        -GameSettings.RAIN_RANGE, GameSettings.RAIN_RANGE
                    )
        else:
            # Deactivate drops that fall below ground
            for drop in self.drops:
                if drop['active']:
                    drop['z'] -= drop['speed']
                    if drop['z'] < 0:
                        drop['active'] = False
    
    def draw(self):
        """Render active rain drops."""
        if not any(d['active'] for d in self.drops):
            return
        
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_LINES)
        glColor4f(0.6, 0.7, 1.0, 0.6)
        
        for drop in self.drops:
            if drop['active']:
                glVertex3f(drop['x'], drop['y'], drop['z'])
                glVertex3f(drop['x'], drop['y'], drop['z'] + 15)
        
        glEnd()
        glPopAttrib()


# ============ PROJECTILES ============
class Bullet(GameObject):
    """Player bullet projectile."""
    
    def __init__(self, origin, angle):
        super().__init__(origin)
        self.angle = angle
        self.speed = GameSettings.BULLET_VELOCITY
    
    def tick(self, dt):
        """Update bullet position."""
        rad = math.radians(self.angle)
        self.pos = self.pos.move(
            self.speed * math.cos(rad) * dt,
            self.speed * math.sin(rad) * dt
        )
        
        # Deactivate if out of bounds
        if (abs(self.pos.x) > GameSettings.ARENA_RADIUS or
            abs(self.pos.y) > GameSettings.ARENA_RADIUS):
            self.alive = False
    
    def draw(self):
        """Render bullet as orange sphere."""
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, 24)
        glColor3f(1, 0.6, 0.1)
        glutSolidSphere(6, 10, 10)
        glPopMatrix()


class EnemyBullet(GameObject):
    """Enemy bullet projectile."""
    
    def __init__(self, origin, angle):
        super().__init__(origin)
        self.angle = angle
        self.speed = GameSettings.ENEMY_BULLET_VELOCITY
    
    def tick(self, dt):
        """Update bullet position."""
        rad = math.radians(self.angle)
        self.pos = self.pos.move(
            self.speed * math.cos(rad) * dt,
            self.speed * math.sin(rad) * dt
        )
        
        # Deactivate if out of bounds
        if (abs(self.pos.x) > GameSettings.ARENA_RADIUS or
            abs(self.pos.y) > GameSettings.ARENA_RADIUS):
            self.alive = False
    
    def draw(self):
        """Render bullet as red sphere."""
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, 24)
        glColor3f(0.8, 0.2, 0.2)
        glutSolidSphere(5, 10, 10)
        glPopMatrix()


# ============ ENEMIES ============
class Enemy(GameObject):
    """Enemy tank with AI behavior and shooting capability."""
    
    def __init__(self, spawn):
        super().__init__(spawn)
        self.tint = self._pick_color()
        self.dir = random.uniform(0, 360)
        self.touched = False
        self.fleeing = False
        self.flee_time = 0
        self.wobble_offset = random.uniform(0, 100)
        self.last_shot_time = time.time()
        self.shot_cooldown = random.uniform(1.5, 3.0)
        self.is_stuck = False
        self.stuck_timer = 0
    
    def _pick_color(self):
        """Select random color tint for enemy."""
        colors = [
            (0.8, 0.2, 0.2), (0.2, 0.2, 0.8), (0.8, 0.8, 0.2),
            (0.6, 0.2, 0.6), (0.2, 0.8, 0.8), (0.8, 0.6, 0.2),
            (0.4, 0.4, 0.4), (0.9, 0.3, 0.6), (0.3, 0.6, 0.3)
        ]
        return random.choice(colors)
    
    def pursue(self, target, dt):
        """
        AI behavior: pursue target with wobble movement.
        
        Args:
            target: Vec position to pursue
            dt: Delta time for frame-independent movement
        """
        # Add wobble to target position
        wobble = math.sin(time.time() * 5 + self.wobble_offset) * 30
        target_x = target.x + wobble
        target_y = target.y + wobble
        
        # Calculate direction to target
        dx = target_x - self.pos.x
        dy = target_y - self.pos.y
        dist = (dx**2 + dy**2)**0.5
        
        if dist > 0:
            # Smoothly turn toward target
            target_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = (target_angle - self.dir + 180) % 360 - 180
            self.dir += angle_diff * 0.15
            
            # Flee briefly after collision, otherwise pursue
            if self.fleeing and (time.time() - self.flee_time < 0.5):
                move_dir = self.dir + 180
            else:
                self.fleeing = False
                move_dir = self.dir
            
            # Move in calculated direction
            rad = math.radians(move_dir)
            step = GameSettings.ENEMY_VELOCITY * dt
            self.pos = self.pos.move(
                step * math.cos(rad),
                step * math.sin(rad)
            ).constrain(GameSettings.ARENA_RADIUS - 25)
    
    def check_hit(self, target):
        """
        Check collision with player and trigger flee behavior.
        
        Returns:
            bool: True if collision occurred
        """
        if check_aabb_collision(
            self.pos, GameSettings.ENEMY_SIZE,
            target, GameSettings.PLAYER_SIZE
        ):
            if not self.touched:
                self.touched = True
                self.fleeing = True
                self.flee_time = time.time()
                return True
        else:
            self.touched = False
        return False
    
    def should_shoot(self):
        """Check if enough time has passed to shoot again."""
        return time.time() - self.last_shot_time >= self.shot_cooldown
    
    def shoot(self, target_pos):
        """
        Calculate shooting angle toward target and reset cooldown.
        
        Returns:
            float: Angle in degrees to shoot toward target
        """
        dx = target_pos.x - self.pos.x
        dy = target_pos.y - self.pos.y
        angle = math.degrees(math.atan2(dy, dx))
        self.last_shot_time = time.time()
        return angle
    
    def draw(self):
        """Render enemy tank."""
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, 14)
        glRotatef(self.dir, 0, 0, 1)
        render_tank(self.tint, True, 0, 0)
        glPopMatrix()


# ============ VISUAL EFFECTS ============
class Explosion(GameObject):
    """Animated explosion effect."""
    
    def __init__(self, center, size):
        super().__init__(center)
        self.size = size
        self.start = time.time()
        self.duration = 1.2
    
    def tick(self, dt):
        """Deactivate explosion after duration."""
        if time.time() - self.start >= self.duration:
            self.alive = False
    
    def draw(self):
        """Render expanding, fading explosion sphere."""
        elapsed = time.time() - self.start
        if elapsed >= self.duration:
            return
        
        progress = elapsed / self.duration
        alpha = max(0, 1 - progress * 1.5)
        
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        glColor4f(1, 0.9, 0.1, alpha * 0.7)
        glutSolidSphere(self.size * (1 + progress * 1.5), 16, 16)
        glPopMatrix()
        
        glPopAttrib()


# ============ ENVIRONMENT OBJECTS ============
class Obstacle(GameObject):
    """Static environment obstacle (tree or building)."""
    
    def __init__(self, loc, scale, kind):
        super().__init__(loc)
        self.scale = scale
        self.kind = kind
        
        # Set collision size based on obstacle type
        if self.kind == "flora":
            self.collision_size = 5.0 * self.scale
        else:
            self.collision_size = 1.0 * self.scale
    
    def draw(self):
        """Render obstacle based on type."""
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        glScalef(self.scale, self.scale, self.scale)
        
        if self.kind == "flora":
            draw_tree()
        elif self.kind == "structure":
            glRotatef(90, 1, 0, 0)
            draw_building()
        
        glPopMatrix()


# ============ POWER-UPS ============
class ShieldPowerUp(GameObject):
    """Collectible shield power-up that grants temporary invulnerability."""
    
    def __init__(self, center):
        super().__init__(center)
        self.size = GameSettings.SHIELD_RADIUS
        self.spawn_time = time.time()
        self.duration = 10.0  # Despawn after 10 seconds
        self.rotation = 0
    
    def tick(self, dt):
        """Update rotation and check despawn time."""
        self.rotation += 5
        if time.time() - self.spawn_time > self.duration:
            self.alive = False
    
    def draw(self):
        """Render rotating cyan sphere."""
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, 20)
        glRotatef(self.rotation, 0, 0, 1)
        glColor4f(0.2, 0.8, 1.0, 0.7)
        glutSolidSphere(self.size, 16, 16)
        glPopMatrix()


class HealthPowerUp(GameObject):
    """Collectible health power-up that restores player health."""

    def __init__(self, center):
        super().__init__(center)
        self.size = 15.0
        self.spawn_time = time.time()
        self.duration = 12.0
        self.rotation = 0

    def tick(self, dt):
        """Update rotation and check despawn time."""
        self.rotation = (self.rotation + 90 * dt) % 360
        if time.time() - self.spawn_time > self.duration:
            self.alive = False

    def draw(self):
        """Render rotating red cross."""
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, 20)
        glRotatef(self.rotation, 0, 0, 1)
        glColor3f(1.0, 0.1, 0.1)
        glBegin(GL_QUADS)
        # Vertical bar
        glVertex3f(-5, -15, 0)
        glVertex3f(5, -15, 0)
        glVertex3f(5, 15, 0)
        glVertex3f(-5, 15, 0)
        # Horizontal bar
        glVertex3f(-15, -5, 0)
        glVertex3f(15, -5, 0)
        glVertex3f(15, 5, 0)
        glVertex3f(-15, 5, 0)
        glEnd()
        glPopMatrix()


# ============ PLAYER ============
class PlayerTank:
    """Player-controlled tank with health and shield systems."""
    
    def __init__(self):
        self.pos = Vec()
        self.body_angle = 0
        self.turret_angle = 0
        self.health = GameSettings.PLAYER_MAX_HP
        self.heat = 0
        self.overdrive = False
        self.shield_active = False
        self.shield_start_time = 0
        self.shield_duration = 0
    
    def gun_angle(self):
        """Calculate absolute gun angle (body + turret)."""
        return (self.body_angle + self.turret_angle) % 360
    
    def muzzle_pos(self):
        """Calculate position of gun muzzle for bullet spawning."""
        a = math.radians(self.gun_angle())
        return self.pos.move(50 * math.cos(a), 50 * math.sin(a))
    
    def try_move(self, forward, obstacles, ignore_collisions=False):
        """
        Attempt to move player, checking obstacle collisions.
        
        Args:
            forward: True to move forward, False for backward
            obstacles: List of Obstacle objects to check
            ignore_collisions: If True, ignore obstacle collisions (overdrive mode)
        """
        sign = 1 if forward else -1
        a = math.radians(self.body_angle)
        
        new_pos = self.pos.move(
            GameSettings.MOVE_RATE * sign * math.cos(a),
            GameSettings.MOVE_RATE * sign * math.sin(a)
        )
        
        blocked = False
        if not ignore_collisions:
            for o in obstacles:
                if check_aabb_collision(new_pos, 25.0, o.pos, o.collision_size):
                    blocked = True
                    break
        
        if not blocked:
            self.pos = new_pos.constrain(GameSettings.ARENA_RADIUS - 25)
    
    def turn_body(self, right):
        """Rotate tank body."""
        self.body_angle = (
            self.body_angle + (1 if right else -1) * GameSettings.TURN_RATE
        ) % 360
    
    def turn_turret(self, right):
        """Rotate turret relative to body."""
        self.turret_angle = (
            self.turret_angle + (1 if right else -1) * GameSettings.TURN_RATE
        ) % 360
    
    def cool(self):
        """Gradually reduce barrel heat."""
        self.heat = max(0, self.heat - 0.01)
    
    def update_shield(self):
        """Update shield state and deactivate if expired."""
        if self.shield_active:
            elapsed = time.time() - self.shield_start_time
            if elapsed >= self.shield_duration:
                self.shield_active = False
    
    def activate_shield(self, duration=None):
        """
        Activate shield with random or specified duration.
        
        Args:
            duration: Shield duration in seconds (random if None)
        """
        if duration is None:
            duration = random.uniform(
                GameSettings.SHIELD_DURATION_MIN,
                GameSettings.SHIELD_DURATION_MAX
            )
        self.shield_active = True
        self.shield_start_time = time.time()
        self.shield_duration = duration
    
    def get_shield_time_remaining(self):
        """Calculate remaining shield time in seconds."""
        if self.shield_active:
            elapsed = time.time() - self.shield_start_time
            return max(0, self.shield_duration - elapsed)
        return 0
    
    def draw_body(self, visible):
        """
        Render player tank.
        
        Args:
            visible: If False, don't render (for first-person view)
        """
        if not visible:
            return
        
        # Draw tank
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, 14)
        glRotatef(self.body_angle, 0, 0, 1)
        render_tank(None, False, self.heat, self.turret_angle)
        glPopMatrix()

    def draw_shield(self):
        """Render shield effect if active."""
        if self.shield_active:
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, 20)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(0.2, 0.8, 1.0, 0.3)
            glutSolidSphere(45, 16, 16)
            glDisable(GL_BLEND)
            glPopMatrix()


# ============ WORLD STATE ============
class World:
    """Main game world containing all entities and game logic."""
    
    def __init__(self):
        # Core entities
        self.player = PlayerTank()
        self.weather = WeatherSystem()
        self.day_night = DayNightCycle()
        
        # Entity lists
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.obstacles = []
        self.power_ups = []
        
        # Game state
        self.kills = 0
        self.ammo_reserve = 15
        self.finished = False
        self.last_time = time.time()
        
        # Camera settings
        self.cam_mode = 3
        self.cam_range = 110
        self.cam_height = 80
        self.shake = {'on': False, 'time': 0, 'dur': 0.3, 'mag': 2}
        
        # Difficulty and power-ups
        self.difficulty = 'Medium'
        self.last_shield_spawn = time.time()
        self.last_health_spawn = time.time()
        self.difficulty_timer = 0
        
        # Initialize world
        self.spawn_obstacles()
        self.spawn_enemies()
    
    def spawn_obstacles(self):
        """Populate world with trees and buildings."""
        # Spawn trees
        for _ in range(40):
            p = Vec(
                random.uniform(-GameSettings.ARENA_RADIUS + 100, 
                              GameSettings.ARENA_RADIUS - 100),
                random.uniform(-GameSettings.ARENA_RADIUS + 100, 
                              GameSettings.ARENA_RADIUS - 100)
            )
            
            # Don't spawn near center
            if abs(p.x) < 80 and abs(p.y) < 80:
                continue
            
            self.obstacles.append(
                Obstacle(p, random.uniform(0.8, 1.6), "flora")
            )
            # Spawn buildings
        for _ in range(10):
            p = Vec(
                random.uniform(-GameSettings.ARENA_RADIUS + 150, 
                              GameSettings.ARENA_RADIUS - 150),
                random.uniform(-GameSettings.ARENA_RADIUS + 150, 
                              GameSettings.ARENA_RADIUS - 150)
            )
            
            # Don't spawn near center
            if abs(p.x) < 120 and abs(p.y) < 120:
                continue
            
            self.obstacles.append(
                Obstacle(p, random.uniform(35, 55), "structure")
            )
    
    def find_spawn(self):
        """Find valid spawn location away from existing enemies."""
        for _ in range(10):
            p = Vec(
                random.uniform(-GameSettings.ARENA_RADIUS + 100, 
                              GameSettings.ARENA_RADIUS - 100),
                random.uniform(-GameSettings.ARENA_RADIUS + 100, 
                              GameSettings.ARENA_RADIUS - 100)
            )
            if all(p.distance(e.pos) >= 60 for e in self.enemies):
                return p
        return Vec(random.uniform(-500, 500), random.uniform(-500, 500))
    
    def spawn_enemies(self):
        """Spawn enemies based on difficulty setting."""
        enemy_count = GameSettings.DIFFICULTY_SETTINGS[self.difficulty]['enemy_count']
        for _ in range(enemy_count):
            self.enemies.append(Enemy(self.find_spawn()))
    
    def fire(self):
        """Fire bullet(s) from player tank."""
        if self.player.overdrive:
            # Overdrive: fire 3-bullet spread
            base_angle = self.player.gun_angle()
            for angle_offset in [-10, 0, 10]:
                self.bullets.append(
                    Bullet(self.player.muzzle_pos(), base_angle + angle_offset)
                )
                self.player.heat += 0.5
        else:
            # Normal: single bullet
            self.bullets.append(
                Bullet(self.player.muzzle_pos(), self.player.gun_angle())
            )
            self.player.heat += 1
        
        # Trigger camera shake
        self.shake['on'] = True
        self.shake['time'] = time.time()
    
    def spawn_shield(self):
        """Periodically spawn shield power-up."""
        if time.time() - self.last_shield_spawn >= GameSettings.SHIELD_SPAWN_INTERVAL:
            # Spawn away from player
            angle = random.uniform(0, 360)
            distance = random.uniform(300, 600)
            rad = math.radians(angle)
            p = Vec(
                self.player.pos.x + distance * math.cos(rad),
                self.player.pos.y + distance * math.sin(rad),
                0
            )
            p = p.constrain(GameSettings.ARENA_RADIUS - 100)
            self.power_ups.append(ShieldPowerUp(p))
            self.last_shield_spawn = time.time()
    
    def check_shield_pickup(self):
        """Check if player collected any shield power-ups."""
        for shield in self.power_ups[:]:
            if isinstance(shield, ShieldPowerUp) and check_aabb_collision(
                self.player.pos, GameSettings.PLAYER_SIZE,
                shield.pos, GameSettings.SHIELD_RADIUS
            ):
                self.player.activate_shield()
                self.power_ups.remove(shield)
    
    def spawn_health_pack(self):
        """Periodically spawn health power-up."""
        if time.time() - self.last_health_spawn >= 20.0:
            angle = random.uniform(0, 360)
            distance = random.uniform(200, 700)
            rad = math.radians(angle)
            p = Vec(
                self.player.pos.x + distance * math.cos(rad),
                self.player.pos.y + distance * math.sin(rad),
                0
            ).constrain(GameSettings.ARENA_RADIUS - 100)
            self.power_ups.append(HealthPowerUp(p))
            self.last_health_spawn = time.time()

    def check_health_pickup(self):
        """Check if player collected any health power-ups."""
        for p in self.power_ups[:]:
            if isinstance(p, HealthPowerUp) and check_aabb_collision(
                self.player.pos, GameSettings.PLAYER_SIZE,
                p.pos, p.size
            ):
                self.player.health = min(GameSettings.PLAYER_MAX_HP, self.player.health + 30)
                self.power_ups.remove(p)

    def update(self):
        """Main game loop update - called every frame."""
        if self.finished:
            return
        
        # Calculate delta time
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Update core systems
        self.player.cool()
        self.player.update_shield()
        self.weather.update(self.player.pos)
        self.day_night.update(dt)
        self.difficulty_timer += dt
        
        # Handle power-ups
        self.spawn_shield()
        self.check_shield_pickup()
        self.spawn_health_pack()
        self.check_health_pickup()
        
        # Update player bullets
        for b in self.bullets[:]:
            b.tick(1)
            if not b.alive:
                self.bullets.remove(b)
                self.ammo_reserve -= 1
                if self.ammo_reserve <= 0:
                    self.finished = True
                continue
            
            # Check bullet-enemy collisions
            for e in self.enemies[:]:
                if check_aabb_collision(
                    b.pos, GameSettings.BULLET_SIZE,
                    e.pos, GameSettings.ENEMY_SIZE
                ):
                    self.explosions.append(Explosion(e.pos, 45))
                    self.enemies.remove(e)
                    self.bullets.remove(b)
                    
                    self.kills += 1
                    self.ammo_reserve = min(15, self.ammo_reserve + 2)
                    
                    # Spawn replacement enemy
                    self.enemies.append(Enemy(self.find_spawn()))
                    break
            
            # Check for player bullet and enemy bullet collision
            for eb in self.enemy_bullets[:]:
                if check_aabb_collision(b.pos, GameSettings.BULLET_SIZE, eb.pos, GameSettings.BULLET_SIZE):
                    self.explosions.append(Explosion(b.pos, 15))
                    self.bullets.remove(b)
                    self.enemy_bullets.remove(eb)
                    break
        
        # Update enemy bullets
        for eb in self.enemy_bullets[:]:
            eb.tick(1)
            if not eb.alive:
                self.enemy_bullets.remove(eb)
                continue
            
            # Check collision with player
            if check_aabb_collision(
                eb.pos, GameSettings.BULLET_SIZE,
                self.player.pos, GameSettings.PLAYER_SIZE
            ):
                if not self.player.shield_active:
                    self.player.health -= GameSettings.ENEMY_BULLET_DAMAGE
                    if self.player.health <= 0:
                        self.finished = True
                self.enemy_bullets.remove(eb)
        
        # Update enemies
        for e in self.enemies:
            old_pos = e.pos
            e.pursue(self.player.pos, 1)

            # Check for obstacle collision and handle getting stuck
            collided_with_obstacle = False
            for o in self.obstacles:
                if check_aabb_collision(e.pos, GameSettings.ENEMY_SIZE, o.pos, o.collision_size):
                    collided_with_obstacle = True
                    break
            
            if collided_with_obstacle:
                e.pos = old_pos
                if not e.is_stuck:
                    e.is_stuck = True
                    e.stuck_timer = time.time()
            
            if e.is_stuck:
                if time.time() - e.stuck_timer < 0.5:
                    # Reverse and turn randomly
                    rad = math.radians(e.dir + 180)
                    step = GameSettings.ENEMY_VELOCITY * 1
                    e.pos = e.pos.move(step * math.cos(rad), step * math.sin(rad))
                    e.dir += random.uniform(-20, 20)
                else:
                    e.is_stuck = False
            
            # Enemy shooting
            if e.should_shoot() and e.pos.distance(self.player.pos) < 500:
                angle = e.shoot(self.player.pos)
                self.enemy_bullets.append(
                    EnemyBullet(e.pos.move(0, 0, 14), angle)
                )
            
            # Check collision for fleeing behavior
            e.check_hit(self.player.pos)
        
        # Prevent enemy overlap
        for i, e1 in enumerate(self.enemies):
            for e2 in self.enemies[i + 1:]:
                dist = e1.pos.distance(e2.pos)
                if dist < 85:
                    dx, dy = e1.pos.x - e2.pos.x, e1.pos.y - e2.pos.y
                    if dist < 0.1:
                        dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
                        dist = (dx**2 + dy**2)**0.5
                    
                    push = (85 - dist) / 85 * 3.0
                    e1.pos = e1.pos.move(
                        dx / dist * push, dy / dist * push
                    ).constrain(GameSettings.ARENA_RADIUS - 25)
                    e2.pos = e2.pos.move(
                        -dx / dist * push, -dy / dist * push
                    ).constrain(GameSettings.ARENA_RADIUS - 25)
        
        # Update explosions
        for ex in self.explosions[:]:
            ex.tick(1)
            if not ex.alive:
                self.explosions.remove(ex)
        
        # Update power-ups
        for p in self.power_ups[:]:
            p.tick(dt)
            if not p.alive:
                self.power_ups.remove(p)
    
    def restart(self, difficulty='Medium'):
        """Reset world to initial state with specified difficulty."""
        self.player = PlayerTank()
        self.weather = WeatherSystem()
        self.day_night = DayNightCycle()
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        self.explosions.clear()
        self.power_ups.clear()
        self.kills = 0
        self.ammo_reserve = 15
        self.finished = False
        self.difficulty = difficulty
        self.difficulty_timer = 0
        self.last_shield_spawn = time.time()
        self.last_health_spawn = time.time()
        self.spawn_enemies()
        self.last_time = time.time()


# ============ RENDERING FUNCTIONS ============
def draw_tree():
    """Render a tree (cylinder trunk + cone leaves)."""
    glColor3f(0.5, 0.3, 0.1)
    gluCylinder(gluNewQuadric(), 5, 5, 50, 32, 32)
    glColor3f(0.1, 0.5, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glutSolidCone(18, 65, 32, 32)
    glPopMatrix()


def draw_building():
    """Render a simple building with roof."""
    glColor3f(0.9, 0.9, 0.8)
    glBegin(GL_QUADS)
    for verts in [
        [(-1, 0, 1), (1, 0, 1), (1, 1, 1), (-1, 1, 1)],
        [(-1, 0, -1), (1, 0, -1), (1, 1, -1), (-1, 1, -1)],
        [(-1, 0, -1), (-1, 0, 1), (-1, 1, 1), (-1, 1, -1)],
        [(1, 0, -1), (1, 0, 1), (1, 1, 1), (1, 1, -1)],
        [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)],
        [(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1)]
    ]:
        for v in verts:
            glVertex3f(*v)
    glEnd()
    glColor3f(0.6, 0.2, 0.2)
    glBegin(GL_TRIANGLES)
    for tri in [
        [(-1, 1, 1), (1, 1, 1), (0, 1.6, 1)],
        [(-1, 1, -1), (1, 1, -1), (0, 1.6, -1)]
    ]:
        for v in tri:
            glVertex3f(*v)
    glEnd()


def render_tank(color, is_enemy, heat, turret_ang):
    """
    Render a tank with body, turret, barrel, and tracks.
    
    Args:
        color: RGB tuple for enemy tanks (None for player)
        is_enemy: True for enemy tanks
        heat: Barrel heat value (affects color)
        turret_ang: Turret rotation angle
    """
    if color:
        main, dark = color, tuple(c * 0.8 for c in color)
    else:
        main, dark = (0.25, 0.35, 0.2), (0.2, 0.3, 0.15)
    
    # Barrel color changes with heat
    if not is_enemy and not color:
        h = min(1, heat / 10)
        barrel = (0.2 + 0.8 * h, 0.2 * (1 - h), 0.2 * (1 - h))
    else:
        barrel = (0.3, 0.3, 0.3)
    
    # Draw tank body
    glColor3f(*main)
    glPushMatrix()
    glScalef(38, 28, 14)
    glutSolidCube(1)
    glPopMatrix()
    
    # Draw turret base
    glPushMatrix()
    if not is_enemy:
        glRotatef(turret_ang, 0, 0, 1)
    glColor3f(*dark)
    glTranslatef(0, 0, 10)
    glutSolidSphere(14, 16, 16)
    glPopMatrix()
    
    # Draw gun barrel
    glPushMatrix()
    if not is_enemy:
        glRotatef(turret_ang, 0, 0, 1)
    glColor3f(*barrel)
    glTranslatef(-28 if is_enemy else 18, 0, 12)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 2.0, 2.0, 35, 12, 12)
    glPopMatrix()
    
    # Draw tracks
    glColor3f(0.15, 0.15, 0.15)
    for y in [16, -16]:
        glPushMatrix()
        glTranslatef(0, y, -2)
        glScalef(38, 6, 10)
        glutSolidCube(1)
        glPopMatrix()
    
    # Draw track wheels
    glColor3f(0.05, 0.05, 0.05)
    for x in [-14, -7, 0, 7, 14]:
        for y in [17, -17]:
            glPushMatrix()
            glTranslatef(x, y, -4)
            glutSolidTorus(2.0, 4, 8, 8)
            glPopMatrix()
    
    # Draw enemy identifier stripe
    if color:
        glColor3f(*tuple(1 - c for c in color))
        glPushMatrix()
        glTranslatef(0, 0, 12)
        glRotatef(90, 0, 1, 0)
        glScalef(2, 24, 2)
        glutSolidCube(1)
        glPopMatrix()


def draw_arena(w):
    """Draw ground plane and sky box."""
    px, py = w.player.pos.x, w.player.pos.y
    r = GameSettings.ARENA_RADIUS
    
    sky_rgb = w.day_night.get_display_color(w.weather.raining)
    ground_brightness = w.day_night.ground_brightness
    ground_rgb = (
        0.25 * ground_brightness,
        0.75 * ground_brightness,
        0.25 * ground_brightness
    )
    
    # Draw ground
    glColor3f(*ground_rgb)
    glBegin(GL_QUADS)
    glVertex3f(px - r, py - r, 0)
    glVertex3f(px + r, py - r, 0)
    glVertex3f(px + r, py + r, 0)
    glVertex3f(px - r, py + r, 0)
    glEnd()
    
    # Draw sky box walls
    h = 800
    glColor3f(*sky_rgb)
    for wall in [
        [(px - r, py + r, 0), (px + r, py + r, 0), (px + r, py + r, h), (px - r, py + r, h)],
        [(px - r, py - r, 0), (px + r, py - r, 0), (px + r, py - r, h), (px - r, py - r, h)],
        [(px - r, py - r, 0), (px - r, py + r, 0), (px - r, py + r, h), (px - r, py - r, h)],
        [(px + r, py - r, 0), (px + r, py + r, 0), (px + r, py + r, h), (px + r, py - r, h)],
        [(px - r, py - r, h), (px + r, py - r, h), (px + r, py + r, h), (px - r, py + r, h)]
    ]:
        glBegin(GL_QUADS)
        for v in wall:
            glVertex3f(*v)
        glEnd()


def setup_camera(w):
    """Configure camera position and view matrix."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(
        GameSettings.CAM_FOV,
        GameSettings.DISPLAY_DIM[0] / GameSettings.DISPLAY_DIM[1],
        0.1, 1500
    )
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Camera shake effect
    sx, sy, sz = 0, 0, 0
    if w.shake['on']:
        dt = time.time() - w.shake['time']
        if dt < w.shake['dur']:
            i = w.shake['mag'] * (1 - dt / w.shake['dur'])
            sx, sy, sz = (random.uniform(-i, i), random.uniform(-i, i),
                         random.uniform(-i / 2, i / 2))
        else:
            w.shake['on'] = False
    
    px, py = w.player.pos.x, w.player.pos.y
    
    if w.cam_mode == 1:
        # First-person camera
        a = w.player.gun_angle()
        ex = px + 40 * math.cos(math.radians(a)) + sx
        ey = py + 40 * math.sin(math.radians(a)) + sy
        ez = 45 + sz
        cx = px + 100 * math.cos(math.radians(a))
        cy = py + 100 * math.sin(math.radians(a))
        cz = 45
    else:
        # Third-person camera
        ar = math.radians(w.player.body_angle + 180)
        ex = px + w.cam_range * math.cos(ar) + sx
        ey = py + w.cam_range * math.sin(ar) + sy
        ez = w.cam_height + sz
        cx, cy, cz = px, py, 35
    
    gluLookAt(ex, ey, ez, cx, cy, cz, 0, 0, 1)


def show_text(x, y, s, f=GLUT_BITMAP_HELVETICA_18):
    """Render 2D text on screen."""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, GameSettings.DISPLAY_DIM[0], 0, GameSettings.DISPLAY_DIM[1])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for c in s:
        glutBitmapCharacter(f, ord(c))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_health_bar(x, y, width, height, current_hp, max_hp):
    """Draw a graphical health bar."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, GameSettings.DISPLAY_DIM[0], 0, GameSettings.DISPLAY_DIM[1])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    hp_ratio = max(0, min(1, current_hp / max_hp))

    glColor3f(0.5, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    bar_color = lerp_color((1.0, 0.0, 0.0), (0.1, 1.0, 0.1), hp_ratio)
    glColor3f(*bar_color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + (width * hp_ratio), y)
    glVertex2f(x + (width * hp_ratio), y + height)
    glVertex2f(x, y + height)
    glEnd()

    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    show_text(x + 5, y + 5, f"HP: {int(current_hp)}/{max_hp}")

    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ============ MENU SYSTEM ============
class MenuSystem:
    """Handles menu screens and button interactions."""
    
    def __init__(self):
        self.state = GameState.MENU
        self.selected_difficulty = 'Medium'
        self.buttons = {}
        self.mouse_x = 0
        self.mouse_y = 0
        self.setup_buttons()
    
    def setup_buttons(self):
        """Create all menu buttons."""
        center_x = GameSettings.DISPLAY_DIM[0] / 2
        
        # Main menu
        button_width = 250
        self.buttons['start'] = Button(center_x - button_width / 2, 500, button_width, 50, "Start Game")
        self.buttons['close_main'] = Button(center_x - button_width / 2, 400, button_width, 50, "Exit Game")
        
        # Difficulty selection
        self.buttons['easy'] = Button(200, 450, 200, 60, "Easy (2 tanks)")
        self.buttons['medium'] = Button(400, 450, 200, 60, "Medium (3 tanks)")
        self.buttons['hard'] = Button(600, 450, 200, 60, "Hard (5 tanks)")
        
        # Pause menu
        self.buttons['resume'] = Button(300, 500, 400, 60, "Resume Game")
        self.buttons['main_menu'] = Button(300, 380, 400, 60, "Exit to Main Menu")
    
    def handle_click(self, button_name):
        """Process button click and return action result."""
        if button_name == 'start':
            self.state = GameState.DIFFICULTY_SELECT
        elif button_name == 'easy':
            self.selected_difficulty = 'Easy'
            self.state = GameState.PLAYING
            return True
        elif button_name == 'medium':
            self.selected_difficulty = 'Medium'
            self.state = GameState.PLAYING
            return True
        elif button_name == 'hard':
            self.selected_difficulty = 'Hard'
            self.state = GameState.PLAYING
            return True
        elif button_name == 'resume':
            self.state = GameState.PLAYING
        elif button_name == 'main_menu':
            self.state = GameState.MENU
            return 'menu'
        elif button_name == 'close_main' or button_name == 'close_pause':
            return 'exit'
        return False
    
    def draw(self):
        """Render menu screens."""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, GameSettings.DISPLAY_DIM[0], 0, GameSettings.DISPLAY_DIM[1])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        center_x = GameSettings.DISPLAY_DIM[0] / 2
        
        if self.state == GameState.MENU:
            title_width = len("TANK ASSAULT 3D") * 15
            show_text(center_x - title_width / 2, 700, "TANK ASSAULT 3D", GLUT_BITMAP_TIMES_ROMAN_24)
            
            self.buttons['start'].draw(self.mouse_x, self.mouse_y)
            self.buttons['close_main'].draw(self.mouse_x, self.mouse_y)

            start_text_width = len("Start Game") * 10
            exit_text_width = len("Exit Game") * 10
            show_text(center_x - start_text_width / 2, 515, "Start Game")
            show_text(center_x - exit_text_width / 2, 415, "Exit Game")
        
        elif self.state == GameState.DIFFICULTY_SELECT:
            show_text(250, 700, "SELECT DIFFICULTY", GLUT_BITMAP_TIMES_ROMAN_24)
            self.buttons['easy'].draw(self.mouse_x, self.mouse_y)
            self.buttons['medium'].draw(self.mouse_x, self.mouse_y)
            self.buttons['hard'].draw(self.mouse_x, self.mouse_y)
            show_text(220, 485, "Easy (2 tanks)")
            show_text(420, 485, "Medium (3 tanks)")
            show_text(620, 485, "Hard (5 tanks)")
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
    
    def draw_pause_menu(self):
        """Render pause menu overlay."""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, GameSettings.DISPLAY_DIM[0], 0, GameSettings.DISPLAY_DIM[1])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Semi-transparent overlay
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(GameSettings.DISPLAY_DIM[0], 0)
        glVertex2f(GameSettings.DISPLAY_DIM[0], GameSettings.DISPLAY_DIM[1])
        glVertex2f(0, GameSettings.DISPLAY_DIM[1])
        glEnd()
        glDisable(GL_BLEND)
        
        # Draw pause menu
        show_text(350, 650, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
        self.buttons['resume'].draw(self.mouse_x, self.mouse_y)
        self.buttons['main_menu'].draw(self.mouse_x, self.mouse_y)
        show_text(425, 525, "Resume Game")
        show_text(375, 405, "Exit to Main Menu")
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


# ============ GLOBAL STATE ============
world = None
menu_system = None
game_state = GameState.MENU


# ============ GLUT CALLBACKS ============
def display():
    """Main display callback."""
    global game_state
    
    if game_state == GameState.MENU or game_state == GameState.DIFFICULTY_SELECT:
        menu_system.draw()
    else:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glViewport(0, 0, *GameSettings.DISPLAY_DIM)
        
        setup_camera(world)
        draw_arena(world)
        
        for o in world.obstacles:
            o.draw()
        
        world.player.draw_body(world.cam_mode == 3 or world.finished)
        for e in world.enemies:
            e.draw()
        for ex in world.explosions:
            ex.draw()
        for b in world.bullets:
            b.draw()
        for eb in world.enemy_bullets:
            eb.draw()
        for p in world.power_ups:
            p.draw()
        world.weather.draw()
        
        world.player.draw_shield()
        
        # Draw UI
        draw_health_bar(10, 760, 200, 25, world.player.health, GameSettings.PLAYER_MAX_HP)
        show_text(10, 730, f"Score: {world.kills}")
        show_text(10, 700, f"Missiles: {world.ammo_reserve}")
        show_text(10, 680, f"View: {'First person' if world.cam_mode == 1 else 'Third person'}")
        
        clock = world.day_night.get_time_string()
        weather_state = "RAIN" if world.weather.raining else "CLEAR"
        show_text(10, 650, f"Time: {clock} | {weather_state}")
        
        show_text(10, 620, f"Difficulty: {world.difficulty}")
        if world.player.shield_active:
            shield_time = world.player.get_shield_time_remaining()
            show_text(10, 590, f"Shield: {shield_time:.1f}s")
        
        if world.player.overdrive:
            show_text(10, 560, "OVERDRIVE ON")
        
        show_text(800, 750, "Press P to Pause")
        
        if world.finished:
            show_text(380, 400, "MISSION FAILED - R to Reset", GLUT_BITMAP_TIMES_ROMAN_24)
        
        if game_state == GameState.PAUSED:
            menu_system.draw_pause_menu()
    
    glutSwapBuffers()


def idle():
    """Idle callback for continuous updates."""
    if game_state == GameState.PLAYING:
        world.update()
    glutPostRedisplay()


def keyboard(k, x, y):
    """Keyboard input callback."""
    global game_state, world
    
    key = k.lower()
    
    if game_state == GameState.MENU or game_state == GameState.DIFFICULTY_SELECT:
        return
    
    # Pause toggle
    if key == b'p':
        if game_state == GameState.PLAYING:
            game_state = GameState.PAUSED
        elif game_state == GameState.PAUSED:
            game_state = GameState.PLAYING
        return
    
    if game_state == GameState.PAUSED:
        return
    
    if world.finished and key != b'r':
        return
    
    # Movement controls
    if key == b'w':
        world.player.try_move(True, world.obstacles, world.player.overdrive)
    elif key == b's':
        world.player.try_move(False, world.obstacles, world.player.overdrive)
    elif key == b'a':
        world.player.turn_body(True)
    elif key == b'd':
        world.player.turn_body(False)
    elif key == b'e':
        world.player.turn_turret(True)
    elif key == b'q':
        world.player.turn_turret(False)
    elif key == b'c':
        world.player.overdrive = not world.player.overdrive
    elif key == b'v':
        world.cam_mode = 3 if world.cam_mode == 1 else 1
    elif key == b'r':
        world.restart(menu_system.selected_difficulty)


def mouse(btn, state, x, y):
    """Mouse input callback."""
    global game_state, world, menu_system
    
    menu_system.mouse_x = x
    menu_system.mouse_y = y
    
    if game_state == GameState.MENU or game_state == GameState.DIFFICULTY_SELECT:
        if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            if game_state == GameState.MENU:
                if menu_system.buttons['start'].is_clicked(x, y):
                    menu_system.handle_click('start')
                    game_state = GameState.DIFFICULTY_SELECT
                elif menu_system.buttons['close_main'].is_clicked(x, y):
                    result = menu_system.handle_click('close_main')
                    if result == 'exit':
                        if bool(glutLeaveMainLoop):
                            glutLeaveMainLoop()
            elif game_state == GameState.DIFFICULTY_SELECT:
                if menu_system.buttons['easy'].is_clicked(x, y):
                    menu_system.handle_click('easy')
                    game_state = GameState.PLAYING
                    world.restart('Easy')
                elif menu_system.buttons['medium'].is_clicked(x, y):
                    menu_system.handle_click('medium')
                    game_state = GameState.PLAYING
                    world.restart('Medium')
                elif menu_system.buttons['hard'].is_clicked(x, y):
                    menu_system.handle_click('hard')
                    game_state = GameState.PLAYING
                    world.restart('Hard')
    
    elif game_state == GameState.PAUSED:
        if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            if menu_system.buttons['resume'].is_clicked(x, y):
                game_state = GameState.PLAYING
            elif menu_system.buttons['main_menu'].is_clicked(x, y):
                game_state = GameState.MENU
                world.restart(menu_system.selected_difficulty)
    
    elif game_state == GameState.PLAYING:
        if world.finished:
            return
        if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            world.fire()
        if btn == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            world.cam_mode = 3 if world.cam_mode == 1 else 1


def special(k, x, y):
    """Special key input callback (arrow keys)."""
    if game_state != GameState.PLAYING:
        return
    
    if k == GLUT_KEY_LEFT:
        world.cam_range = max(50, world.cam_range - 10)
    elif k == GLUT_KEY_RIGHT:
        world.cam_range = min(1000, world.cam_range + 10)
    elif k == GLUT_KEY_UP:
        world.cam_height = min(500, world.cam_height + 10)
    elif k == GLUT_KEY_DOWN:
        world.cam_height = max(50, world.cam_height - 10)


# ============ MAIN ENTRY POINT ============
def main():
    """Initialize and run the game."""
    global world, menu_system, game_state
    
    world = World()
    menu_system = MenuSystem()
    game_state = GameState.MENU
    
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(*GameSettings.DISPLAY_DIM)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Tank Assault 3D")
    glEnable(GL_DEPTH_TEST)
    
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutSpecialFunc(special)
    glutMainLoop()


if __name__ == "__main__":
    main()
