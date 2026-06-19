import random
import sys
import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SHOOTER_RADIUS = 30  
PROJECTILE_RADIUS = 7  
FALLING_CIRCLE_RADIUS = 25  
PROJECTILE_SPEED = 7
FALLING_CIRCLE_SPEED = 1.5
MAX_MISSES = 3
BUTTON_SIZE = 40

WHITE = (1.0, 1.0, 1.0)
RED = (1.0, 0.0, 0.0)
CYAN = (0.0, 1.0, 1.0)
YELLOW = (1.0, 1.0, 0.0)
BLACK = (0.0, 0.0, 0.0)
COLORS = [RED, CYAN, YELLOW]


shooter_x = SCREEN_WIDTH // 2
shooter_y = SCREEN_HEIGHT - 50
projectiles = []
falling_circles = []
score = 0
missed_circles = 0 
game_over = False
game_paused = False


def draw_circle(x_center, y_center, radius):
    x = 0
    y = radius
    d = 1 - radius
    glBegin(GL_POINTS)
    def plot_circle_points(x_center, y_center, x, y):
        glVertex2f(x_center + x, y_center + y)
        glVertex2f(x_center - x, y_center + y)
        glVertex2f(x_center + x, y_center - y)
        glVertex2f(x_center - x, y_center - y)
        glVertex2f(x_center + y, y_center + x)
        glVertex2f(x_center - y, y_center + x)
        glVertex2f(x_center + y, y_center - x)
        glVertex2f(x_center - y, y_center - x)
    plot_circle_points(x_center, y_center, x, y)
    while x < y:
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1
        plot_circle_points(x_center, y_center, x, y)
    glEnd()


def draw_line(x0, y0, x1, y1):
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x1, y1)
    glEnd()


def draw_rectangle(x, y, width, height, color):
    glColor3f(*color)
    draw_line(x, y, x + width, y)
    draw_line(x, y, x, y + height)
    draw_line(x + width, y, x + width, y + height)
    draw_line(x, y + height, x + width, y + height)


def draw_shooter(x, y):
    glColor3f(*WHITE)
    draw_circle(x, y, SHOOTER_RADIUS)


def draw_projectile(x, y):
    glColor3f(*YELLOW)
    draw_circle(x, y, PROJECTILE_RADIUS)


def draw_button(x, y, size, color, shape):
    glColor3f(*color)
    if shape == "left":
        draw_line(x + size // 2, y, x, y + size // 2)
        draw_line(x, y + size // 2, x + size // 2, y + size)
        draw_line(x, y + size // 2, x + size, y + size // 2)
    elif shape == "pause":
        draw_rectangle(x, y, size // 3, size, color)
        draw_rectangle(x + 2 * size // 3, y, size // 3, size, color)
    elif shape == "play":
        draw_line(x, y, x + size, y + size // 2)
        draw_line(x + size, y + size // 2, x, y + size)
        draw_line(x, y, x, y + size)
    elif shape == "exit":
        draw_line(x, y, x + size, y + size)
        draw_line(x + size, y, x, y + size)


def draw_falling_circle(x, y):
    glColor3f(*random.choice(COLORS))
    draw_circle(x, y, FALLING_CIRCLE_RADIUS)


def mouse_input(button, state, x, y):
    global game_paused, game_over, projectiles, falling_circles, score, missed_circles, shooter_x, shooter_y, FALLING_CIRCLE_SPEED, PROJECTILE_SPEED

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if 20 < x < 20 + BUTTON_SIZE and 20 < y < 20 + BUTTON_SIZE:
            game_over = False
            score = 0
            missed_circles = 0
            projectiles = []
            falling_circles = []
            PROJECTILE_SPEED = 10
            FALLING_CIRCLE_SPEED = 3
            glClear(GL_COLOR_BUFFER_BIT)
            glFlush()

        elif SCREEN_WIDTH // 2 - BUTTON_SIZE // 2 < x < SCREEN_WIDTH // 2 + BUTTON_SIZE // 2 and 20 < y < 20 + BUTTON_SIZE:
            game_paused = not game_paused
        elif SCREEN_WIDTH - BUTTON_SIZE - 20 < x < SCREEN_WIDTH - 20 and 20 < y < 20 + BUTTON_SIZE:
            glutLeaveMainLoop()


def special_input(key, x, y):
    global shooter_x, game_over

    if not game_over:
        if key == GLUT_KEY_LEFT:
            shooter_x = max(SHOOTER_RADIUS, shooter_x - 20)
        elif key == GLUT_KEY_RIGHT:
            shooter_x = min(SCREEN_WIDTH - SHOOTER_RADIUS, shooter_x + 20)


def display():
    global score, missed_circles, lives, game_over, game_paused

    glClear(GL_COLOR_BUFFER_BIT)

    draw_shooter(shooter_x, shooter_y)
    draw_button(20, 20, BUTTON_SIZE, CYAN, "left")  
    draw_button(SCREEN_WIDTH // 2 - BUTTON_SIZE // 2, 20, BUTTON_SIZE, YELLOW, "pause" if not game_paused else "play")
    draw_button(SCREEN_WIDTH - BUTTON_SIZE - 20, 20, BUTTON_SIZE, RED, "exit")

    for projectile in projectiles:
        draw_projectile(projectile['x'], projectile['y'])

    for circle in falling_circles:
        draw_falling_circle(circle['x'], circle['y'])

    display_text(10, 10, f"Score: {score}", WHITE)
    display_text(10, 30, f"Misses: {missed_circles}/{MAX_MISSES}", WHITE)

    if game_over:
        display_text(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, "GAME OVER", RED)
    elif game_paused:
        display_text(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, "GAME PAUSED", YELLOW)

    glFlush()


def display_text(x, y, text, color):
    glColor3f(*color)  
    glRasterPos2f(x, y)  
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))  


def key_input(key, x, y):
    global shooter_x, projectiles, game_over, shooter_y

    if not game_over:
        if key == b'a':  
            shooter_x = max(SHOOTER_RADIUS, shooter_x - 20)
        elif key == b'd':  
            shooter_x = min(SCREEN_WIDTH - SHOOTER_RADIUS, shooter_x + 20)
        elif key == b' ':  
            projectiles.append({'x': shooter_x, 'y': shooter_y - SHOOTER_RADIUS})


def update(value):
    global projectiles, falling_circles, score, missed_circles, game_over, game_paused

    if not game_paused and not game_over:
        for projectile in projectiles:
            projectile['y'] -= PROJECTILE_SPEED
        projectiles = [proj for proj in projectiles if proj['y'] > 0]

        for circle in falling_circles:
            circle['y'] += FALLING_CIRCLE_SPEED

            if circle['y'] >= 575 and not circle.get('reached_shooter', False):
                circle['reached_shooter'] = True
                missed_circles += 1  
                falling_circles.remove(circle)  
                if missed_circles >= MAX_MISSES:
                    game_over = True  

        new_projectiles = []
        for projectile in projectiles:
            hit_circle = None
            for circle in falling_circles:
                dist = math.sqrt((projectile['x'] - circle['x']) ** 2 + (projectile['y'] - circle['y']) ** 2)
                if dist < FALLING_CIRCLE_RADIUS and not circle.get('reached_shooter', False):
                    hit_circle = circle
                    score += 1
                    break

            if hit_circle:
                falling_circles.remove(hit_circle)  
            else:
                new_projectiles.append(projectile)  

        projectiles = new_projectiles

        if random.random() < 0.02:
            falling_circles.append({'x': random.randint(0, SCREEN_WIDTH), 'y': 0, 'reached_shooter': False})

        for circle in falling_circles:
            dist = math.sqrt((shooter_x - circle['x']) ** 2 + (shooter_y - circle['y']) ** 2)
            if dist < SHOOTER_RADIUS + FALLING_CIRCLE_RADIUS:
                game_over = True 
                break

        glutPostRedisplay()

    glutTimerFunc(30, update, 0)




def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  
    glMatrixMode(GL_PROJECTION)  
    glLoadIdentity()  
    gluOrtho2D(0.0, SCREEN_WIDTH, SCREEN_HEIGHT, 0.0)  
    glMatrixMode(GL_MODELVIEW)  


def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(SCREEN_WIDTH, SCREEN_HEIGHT)
    glutCreateWindow(b"Circle Shooting Game")
    init()
    glutMouseFunc(mouse_input)
    glutSpecialFunc(special_input)
    glutDisplayFunc(display)
    glutKeyboardFunc(key_input)
    glutTimerFunc(30, update, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()

