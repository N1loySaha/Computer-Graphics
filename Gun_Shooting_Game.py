# -*- coding: utf-8 -*-

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# --- Global Game Variables ---

# Camera Settings
camera_coords = (0, 410, 500)
camera_rotation = 0
first_person_mode = False
follow_gun_mode = False
field_of_view = 120

# Player Settings
player_pos = [0, 0, 0]
player_angle = 90       # Direction the player is facing
move_angle = 90         # Direction the player moves
player_speed = 5
player_lives = 5

# Cheat/Super Mode Variables
is_super_mode = False
spin_speed = 3
auto_shoot_timer = 0
auto_shoot_delay = 15

# Enemy Settings
enemy_list = []
enemy_sizes = []
enemy_speed = 0.1
enemy_count = 5
spawn_safe_distance = 250   # How far enemies must spawn from player

# Enemy Scaling Animation
min_scale = 0.5
max_scale = 1
scale_step_size = 0.025
scale_direction = 1         # 1 for growing, -1 for shrinking
scale_counter = 0
scale_speed = 100

# Score and Game State
score = 0
missed_shots = 0
max_missed_shots = 10
is_game_over = False

# Bullet Settings
bullet_list = []
bullet_radius = 10
bullet_velocity = 15

# Initialize Enemies
for i in range(enemy_count):
    while True:
        # Generate random spawn point
        rand_x = random.randint(-550, 550)
        rand_y = random.randint(-550, 550)
        spawn_point = [rand_x, rand_y, 0]

        # Calculate distance to player manually
        dist = math.sqrt((rand_x - player_pos[0])**2 + (rand_y - player_pos[1])**2)

        if dist >= spawn_safe_distance:
            enemy_list.append(spawn_point)
            enemy_sizes.append(1.0)
            break

# --- Helper Functions ---

def get_distance(point1, point2):
    """Calculates distance between two 3D points"""
    x_diff = point1[0] - point2[0]
    y_diff = point1[1] - point2[1]
    z_diff = point1[2] - point2[2]
    return math.sqrt(x_diff**2 + y_diff**2 + z_diff**2)

def show_text(x, y, text_string):
    """Displays text on screen"""
    glColor3f(1, 1, 1) # White text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for char in text_string:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def check_aim(enemy_location):
    """Checks if the player is aiming at a specific enemy"""
    # Gun direction
    rad_angle = math.radians(player_angle)
    gun_x = -math.cos(rad_angle)
    gun_y = -math.sin(rad_angle)

    # Vector to enemy
    vec_x = enemy_location[0] - player_pos[0]
    vec_y = enemy_location[1] - player_pos[1]

    dist = math.sqrt(vec_x**2 + vec_y**2)
    if dist < 1: return False

    # Normalize
    vec_x /= dist
    vec_y /= dist

    # Dot product for similarity
    aim_accuracy = gun_x * vec_x + gun_y * vec_y
    return aim_accuracy > 0.95

# --- Input Handling Functions ---

def handle_keyboard(key, x, y):
    global player_angle, player_pos, player_speed, is_game_over, is_super_mode, move_angle, follow_gun_mode

    if is_game_over:
        if key == b'r':
            restart_game()
        return

    # 'c' for Cheat/Super Mode
    if key == b'c':
        is_super_mode = not is_super_mode
        move_angle = player_angle

    # 'v' for Camera follow in Super Mode
    if key == b'v' and first_person_mode and is_super_mode:
        follow_gun_mode = not follow_gun_mode

    # Manual Rotation (only if not in super mode)
    if not is_super_mode:
        if key == b'a':
            player_angle += 5
            move_angle = player_angle
            if player_angle >= 360:
                player_angle -= 360
                move_angle = player_angle

        if key == b'd':
            player_angle -= 5
            move_angle = player_angle
            if player_angle < 0:
                player_angle += 360
                move_angle = player_angle

    # Determine movement direction
    direction = move_angle if is_super_mode else player_angle

    # Movement W/S
    if key == b'w':
        rads = math.radians(direction)
        next_x = player_pos[0] - player_speed * math.cos(rads)
        next_y = player_pos[1] - player_speed * math.sin(rads)
        if -560 <= next_x <= 560 and -560 <= next_y <= 560:
            player_pos[0] = next_x
            player_pos[1] = next_y

    if key == b's':
        rads = math.radians(direction)
        next_x = player_pos[0] + player_speed * math.cos(rads)
        next_y = player_pos[1] + player_speed * math.sin(rads)
        if -560 <= next_x <= 560 and -560 <= next_y <= 560:
            player_pos[0] = next_x
            player_pos[1] = next_y

    if key == b'r':
        restart_game()

    glutPostRedisplay()

def handle_arrow_keys(key, x, y):
    global camera_coords, camera_rotation, first_person_mode

    if not first_person_mode:
        cam_x, cam_y, cam_z = camera_coords

        if key == GLUT_KEY_UP and cam_z < 800:
            cam_z += 20
        elif key == GLUT_KEY_DOWN and cam_z > 200:
            cam_z -= 20
        elif key == GLUT_KEY_LEFT:
            camera_rotation += 5
            if camera_rotation >= 360: camera_rotation -= 360
        elif key == GLUT_KEY_RIGHT:
            camera_rotation -= 5
            if camera_rotation < 0: camera_rotation += 360

        camera_coords = (cam_x, cam_y, cam_z)

    glutPostRedisplay()

def handle_mouse(button, state, x, y):
    global is_game_over, first_person_mode

    if is_game_over: return

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        shoot_bullet()
        glutPostRedisplay()

    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_mode = not first_person_mode
        glutPostRedisplay()

# --- Game Logic Functions ---

def shoot_bullet():
    global bullet_list, player_angle, player_pos, is_super_mode, enemy_list

    rads = math.radians(player_angle)
    gun_len = 80

    # Starting position (Tip of the gun)
    start_x = player_pos[0] + (-math.cos(rads) * gun_len)
    start_y = player_pos[1] + (-math.sin(rads) * gun_len)
    start_z = player_pos[2] + 100

    # Velocity Vector
    vel_x = -math.cos(rads) * bullet_velocity
    vel_y = -math.sin(rads) * bullet_velocity

    # Auto-aim logic
    target_idx = -1
    if is_super_mode:
        for idx, enemy in enumerate(enemy_list):
            if check_aim(enemy):
                target_idx = idx
                break

    new_bullet = {
        'pos': [start_x, start_y, start_z],
        'vel': [vel_x, vel_y, 0],
        'is_active': True,
        'is_homing': is_super_mode,
        'target_id': target_idx
    }
    bullet_list.append(new_bullet)

def update_camera():
    global first_person_mode, player_pos, player_angle, camera_coords, camera_rotation

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    if first_person_mode:
        gluPerspective(100, 1.25, 0.1, 1500)
    else:
        gluPerspective(field_of_view, 1.25, 0.1, 1500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person_mode:
        eye_x, eye_y = player_pos[0], player_pos[1]
        eye_z = player_pos[2] + 150

        # Look direction
        if is_super_mode and not follow_gun_mode:
            look_rads = math.radians(90) # Fixed view
        else:
            look_rads = math.radians(player_angle)

        look_x = eye_x - math.cos(look_rads) * 100
        look_y = eye_y - math.sin(look_rads) * 100

        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, eye_z, 0, 0, 1)
    else:
        cam_x, cam_y, cam_z = camera_coords
        cam_rads = math.radians(camera_rotation)
        radius = 600
        cam_x = radius * math.cos(cam_rads)
        cam_y = radius * math.sin(cam_rads)

        gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)

def game_loop():
    """Main game update loop (formerly idle)"""
    global enemy_list, bullet_list, score, missed_shots, player_lives, enemy_sizes, is_game_over
    global scale_direction, scale_counter, player_angle, is_super_mode, auto_shoot_timer

    if is_game_over:
        glutPostRedisplay()
        return

    # Super Mode: Auto Rotate and Fire
    if is_super_mode:
        player_angle += spin_speed
        if player_angle >= 360: player_angle -= 360

        auto_shoot_timer += 1
        if auto_shoot_timer >= auto_shoot_delay:
            for idx, enemy in enumerate(enemy_list):
                if check_aim(enemy):
                    # Snap aim to enemy
                    dx = enemy[0] - player_pos[0]
                    dy = enemy[1] - player_pos[1]
                    exact_angle = math.degrees(math.atan2(dy, dx)) + 180
                    player_angle = exact_angle if exact_angle < 360 else exact_angle - 360

                    shoot_bullet()
                    auto_shoot_timer = 0
                    break

    # Pulse Animation for Enemies
    scale_counter += 1
    if scale_counter >= scale_speed // 20:
        scale_counter = 0
        for i in range(len(enemy_sizes)):
            enemy_sizes[i] += (scale_step_size * scale_direction)
            if enemy_sizes[i] >= max_scale:
                enemy_sizes[i] = max_scale
                scale_direction = -1
            elif enemy_sizes[i] <= min_scale:
                enemy_sizes[i] = min_scale
                scale_direction = 1

    # Enemy Logic: Movement and Collision with Player
    for i in range(len(enemy_list)):
        dx = player_pos[0] - enemy_list[i][0]
        dy = player_pos[1] - enemy_list[i][1]

        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            dx /= dist
            dy /= dist

        enemy_list[i][0] += dx * enemy_speed
        enemy_list[i][1] += dy * enemy_speed

        # Check collision with player
        enemy_radius = 60 * enemy_sizes[i]
        player_radius = 30

        if get_distance(player_pos, enemy_list[i]) < enemy_radius + player_radius:
            player_lives -= 1

            # Respawn this enemy
            while True:
                new_pt = [random.randint(-550, 550), random.randint(-550, 550), 0]
                if get_distance(player_pos, new_pt) >= spawn_safe_distance:
                    enemy_list[i] = new_pt
                    break

            if player_lives <= 0: is_game_over = True

    # Bullet Logic: Movement and Collision with Enemies
    remove_indices = []

    for i, b in enumerate(bullet_list):
        if not b['is_active']:
            remove_indices.append(i)
            continue

        # Homing Logic
        if b['is_homing'] and is_super_mode:
            target_id = b['target_id']
            if 0 <= target_id < len(enemy_list):
                target = enemy_list[target_id]
                bx, by, bz = b['pos']

                # Vector to target
                tx, ty, tz = target[0] - bx, target[1] - by, 30 - bz
                tdist = math.sqrt(tx*tx + ty*ty + tz*tz)

                if tdist > 0:
                    b['vel'] = [(tx/tdist)*bullet_velocity*1.5,
                                (ty/tdist)*bullet_velocity*1.5,
                                (tz/tdist)*bullet_velocity]
            else:
                # Retarget
                for j in range(len(enemy_list)):
                    b['target_id'] = j
                    break

        # Move Bullet
        b['pos'][0] += b['vel'][0]
        b['pos'][1] += b['vel'][1]
        b['pos'][2] += b['vel'][2]

        # Out of bounds check
        bx, by = b['pos'][0], b['pos'][1]
        if bx < -600 or bx > 600 or by < -600 or by > 600:
            if not is_super_mode:
                missed_shots += 1
            b['is_active'] = False
            remove_indices.append(i)

            if missed_shots >= max_missed_shots: is_game_over = True
            continue

        # Hit detection
        has_hit = False
        for j, enemy in enumerate(enemy_list):
            rad = 60 * enemy_sizes[j]
            dist_xy = math.sqrt((bx - enemy[0])**2 + (by - enemy[1])**2)
            dist_z = abs(b['pos'][2] - 30)

            if dist_xy < rad and dist_z < 100:
                score += 1
                b['is_active'] = False
                remove_indices.append(i)
                has_hit = True

                # Respawn Enemy
                while True:
                    new_pt = [random.randint(-550, 550), random.randint(-550, 550), 0]
                    if get_distance(player_pos, new_pt) >= spawn_safe_distance:
                        enemy_list[j] = new_pt
                        break
                break

        if has_hit: continue

    # Clean up bullets
    for index in sorted(remove_indices, reverse=True):
        if index < len(bullet_list):
            bullet_list.pop(index)

    glutPostRedisplay()

def restart_game():
    global player_pos, player_angle, score, missed_shots, player_lives, bullet_list, is_game_over
    global enemy_list, enemy_sizes, scale_direction, first_person_mode, camera_coords
    global camera_rotation, is_super_mode, move_angle, follow_gun_mode

    player_pos = [0, 0, 0]
    player_angle = 90
    move_angle = 90
    score = 0
    missed_shots = 0
    player_lives = 5
    bullet_list.clear()
    is_game_over = False
    scale_direction = 1
    first_person_mode = False
    camera_coords = (0, 410, 500)
    camera_rotation = 0
    is_super_mode = False
    follow_gun_mode = False

    enemy_list.clear()
    enemy_sizes.clear()

    for i in range(enemy_count):
        while True:
            pt = [random.randint(-550, 550), random.randint(-550, 550), 0]
            if get_distance(player_pos, pt) >= spawn_safe_distance:
                enemy_list.append(pt)
                enemy_sizes.append(1.0)
                break

# --- Drawing Functions ---

def draw_grid():
    """Draws the checkerboard floor"""
    glBegin(GL_QUADS)
    x_start = 600
    y_start = -600
    is_purple = False

    for row in range(12):
        x_start = 600
        for col in range(12):
            if is_purple:
                glColor3f(0.776, 0.4, 1) # Purple
                is_purple = False
            else:
                glColor3f(1, 1, 1) # White
                is_purple = True

            glVertex3f(x_start-100, y_start+100, 0)
            glVertex3f(x_start, y_start+100, 0)
            glVertex3f(x_start, y_start, 0)
            glVertex3f(x_start-100, y_start, 0)
            x_start -= 100

        is_purple = not is_purple
        y_start += 100
    glEnd()

def draw_walls():
    """Draws the colored borders"""
    glBegin(GL_QUADS)
    # Green Wall
    glColor3f(0.18, 1, 0.204)
    glVertex3f(-600, 600, 100)
    glVertex3f(-600, 600, 0)
    glVertex3f(-600, -600, 0)
    glVertex3f(-600, -600, 100)
    # Cyan Wall
    glColor3f(0.18, 0.957, 1)
    glVertex3f(-600, -600, 0)
    glVertex3f(600, -600, 0)
    glVertex3f(600, -600, 100)
    glVertex3f(-600, -600, 100)
    # Blue Wall
    glColor3f(0, 0, 1)
    glVertex3f(600, 600, 100)
    glVertex3f(600, -600, 100)
    glVertex3f(600, -600, 0)
    glVertex3f(600, 600, 0)
    # White Wall
    glColor3f(1, 1, 1)
    glVertex3f(-600, 600, 100)
    glVertex3f(600, 600, 100)
    glVertex3f(600, 600, 0)
    glVertex3f(-600, 600, 0)
    glEnd()

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_angle, 0, 0, 1)

    if first_person_mode:
        # Just draw gun
        glColor3f(0.753, 0.753, 0.753)
        glPushMatrix()
        glTranslatef(0, 0, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
        glPopMatrix()
    else:
        # Draw Body
        glColor3f(0.333, 0.42, 0.184)
        glPushMatrix()
        glTranslatef(0, 0, 90)
        glutSolidCube(60)
        glPopMatrix()
        # Head
        glColor3f(0, 0, 0)
        glPushMatrix()
        glTranslatef(0, 0, 150)
        gluSphere(gluNewQuadric(), 25, 10, 10)
        glPopMatrix()
        # Legs
        glColor3f(0, 0, 1)
        glPushMatrix()
        glTranslatef(-20, -15, 0)
        gluCylinder(gluNewQuadric(), 7, 12, 60, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-20, 15, 0)
        gluCylinder(gluNewQuadric(), 7, 12, 60, 10, 10)
        glPopMatrix()
        # Gun
        glColor3f(0.753, 0.753, 0.753)
        glPushMatrix()
        glTranslatef(0, 0, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
        glPopMatrix()
        # Hands
        glColor3f(1, 0.878, 0.741)
        glPushMatrix()
        glTranslatef(-20, -15, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 10, 6, 30, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-20, 15, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 10, 6, 30, 10, 10)
        glPopMatrix()

    glPopMatrix()

def draw_dead_player():
    """Draws player lying flat"""
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])

    # Body (Rotated flat)
    glColor3f(0.333, 0.42, 0.184)
    glPushMatrix()
    glTranslatef(0, 0, 30)
    glRotatef(90, 1, 0, 0)
    glutSolidCube(60)
    glPopMatrix()

    # Head
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, -50, 30)
    gluSphere(gluNewQuadric(), 25, 10, 10)
    glPopMatrix()

    # Legs
    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(-20, 30, 15)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 7, 60, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(20, 30, 15)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 7, 60, 10, 10)
    glPopMatrix()

    # Gun (Pointing up)
    glColor3f(0.753, 0.753, 0.753)
    glPushMatrix()
    glTranslatef(0, 0, 30)
    gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
    glPopMatrix()

    glPopMatrix()

def draw_projectiles():
    for b in bullet_list:
        if b['is_active']:
            glPushMatrix()
            glTranslatef(b['pos'][0], b['pos'][1], b['pos'][2])
            glColor3f(1, 0, 0) # Red bullets
            glutSolidCube(bullet_radius)
            glPopMatrix()

def draw_enemies():
    for i, pos in enumerate(enemy_list):
        scale = enemy_sizes[i]
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glScalef(scale, scale, scale)

        # Body
        glColor3f(1, 0, 0)
        gluSphere(gluNewQuadric(), 60, 10, 10)
        # Head
        glColor3f(0, 0, 0)
        glTranslatef(0, 0, 70)
        gluSphere(gluNewQuadric(), 30, 10, 10)
        glPopMatrix()

def render_scene():
    """Main display function (formerly showScreen)"""
    global score, missed_shots, player_lives, is_game_over

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    update_camera()
    draw_grid()
    draw_walls()

    if not is_game_over:
        draw_player()
    else:
        draw_dead_player()

    draw_projectiles()
    draw_enemies()

    # HUD / Text
    if not is_game_over:
        show_text(10, 770, f"Score: {score}")
        show_text(10, 740, f"Misses: {missed_shots}/{max_missed_shots}")
        show_text(10, 710, f"Life: {player_lives}/5")

        state_text = "ON" if is_super_mode else "OFF"
        show_text(10, 680, f"SUPER MODE: {state_text} (Press C)")

        view_text = "ON" if first_person_mode else "OFF"
        show_text(10, 650, f"FIRST PERSON: {view_text} (Right Click)")

    else:
        show_text(400, 400, "GAME OVER")
        show_text(350, 370, "Press 'R' to Restart")
        show_text(10, 770, f"Final Score: {score}")

    glutSwapBuffers()

def initialize_opengl():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy Remastered")

    initialize_opengl()

    glutDisplayFunc(render_scene)
    glutKeyboardFunc(handle_keyboard)
    glutSpecialFunc(handle_arrow_keys)
    glutMouseFunc(handle_mouse)
    glutIdleFunc(game_loop)

    glutMainLoop()

if __name__ == "__main__":
    main()