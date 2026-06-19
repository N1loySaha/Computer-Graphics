import random
import sys
import threading
import tkinter as tk
from OpenGL.GL import *
from OpenGL.GLUT import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CATCHER_WIDTH = 120
CATCHER_HEIGHT = 25
DIAMOND_SIZE = 30
BUTTON_SIZE = 40


WHITE = (1.0, 1.0, 1.0)
RED = (1.0, 0.0, 0.0)
CYAN = (0.0, 1.0, 1.0)
YELLOW = (1.0, 1.0, 0.0)
BLACK = (0.0, 0.0, 0.0)
COLORS = [RED, CYAN, YELLOW]


catcher_x = (SCREEN_WIDTH - CATCHER_WIDTH) // 2
catcher_y = SCREEN_HEIGHT - 50
diamond_x = random.randint(0, SCREEN_WIDTH - DIAMOND_SIZE)
diamond_y = 0
score = 0
diamond_speed = 3
game_over = False
game_paused = False
current_diamond_color = random.choice(COLORS)

# Eight-way Symmetry Functions
def findZone(x, y):
    if x >= 0 and y >= 0:
        if x >= y:
            return 0
        else:
            return 1
    elif x < 0 and y >= 0:
        if abs(x) >= y:
            return 3
        else:
            return 2
    elif x < 0 and y < 0:
        if abs(x) >= abs(y):
            return 4
        else:
            return 5
    elif x >= 0 and y < 0:
        if x >= abs(y):
            return 7
        else:
            return 6

def convertToZone0(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return y, -x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return -y, x
    elif zone == 7:
        return x, -y

def convertFromZone0(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return y, -x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return -y, x
    elif zone == 7:
        return x, -y

def draw_line(x0, y0, x1, y1):
    zone = findZone(x1 - x0, y1 - y0)
    x0, y0 = convertToZone0(x0, y0, zone)
    x1, y1 = convertToZone0(x1, y1, zone)
    dx = x1 - x0
    dy = y1 - y0
    d = 2 * dy - dx
    incrE = 2 * dy
    incrNE = 2 * (dy - dx)
    x, y = x0, y0

    glBegin(GL_POINTS)
    while x <= x1:
        px, py = convertFromZone0(x, y, zone)
        glVertex2f(px, py)
        if d > 0:
            y += 1
            d += incrNE
        else:
            d += incrE
        x += 1
    glEnd()


def draw_trapezium(x, y, width, height, color):
    glColor3f(*color)
    half_width = width // 2
    half_height = height // 2

    # Upper horizontal edge
    draw_line(x - half_width, y - half_height, x + half_width, y - half_height)

    # Lower horizontal edge
    draw_line(x - width // 4, y + half_height, x + width // 4, y + half_height)

    # Left diagonal edge
    draw_line(x - half_width, y - half_height, x - width // 4, y + half_height)

    # Right diagonal edge
    draw_line(x + half_width, y - half_height, x + width // 4, y + half_height)

def draw_rectangle(x, y, width, height, color):
    glColor3f(*color)
    draw_line(x, y, x + width, y)
    draw_line(x, y, x, y + height)
    draw_line(x + width, y, x + width, y + height)
    draw_line(x, y + height, x + width, y + height)

def draw_diamond(x, y, size, color):
    glColor3f(*color)
    half_size = size // 2
    draw_line(x + half_size, y, x, y + half_size)
    draw_line(x, y + half_size, x + half_size, y + size)
    draw_line(x + half_size, y + size, x + size, y + half_size)
    draw_line(x + size, y + half_size, x + half_size, y)

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
        draw_line(x,y,x,y+size)
    elif shape == "exit":
        draw_line(x, y, x + size, y + size)
        draw_line(x + size, y, x, y + size)

def display_text(x, y, text, color):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


def key_input(key, x, y):
    global catcher_x, game_over
    if key == b'\x1b':  # ESC key
        sys.exit()
    if game_over:
        return
    if key == b'a':  # Left
        catcher_x = max(60, catcher_x - 25)
    elif key == b'd':  # Right
        catcher_x = min(SCREEN_WIDTH - CATCHER_WIDTH // 2, catcher_x + 25)

def special_key_input(key, x, y):
    global catcher_x, game_over
    if game_over:
        return
    if key == GLUT_KEY_LEFT:  # Left arrow key
        catcher_x = max(60, catcher_x - 25)
    elif key == GLUT_KEY_RIGHT:  # Right arrow key
        catcher_x = min(SCREEN_WIDTH - CATCHER_WIDTH // 2, catcher_x + 25)

def mouse_input(button, state, x, y):
    global game_over, game_paused, score, missed_circles

    # Invert the y-coordinate because OpenGL's origin is bottom-left, GLUT's is top-left
    y = SCREEN_HEIGHT - y

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if x < BUTTON_SIZE + 20 and y < BUTTON_SIZE + 20:
            # Restart button clicked
            if game_over:
                score = 0
                missed_circles = 0
                projectiles.clear()
                falling_circles.clear()
                game_over = False
        elif SCREEN_WIDTH // 2 - BUTTON_SIZE // 2 < x < SCREEN_WIDTH // 2 + BUTTON_SIZE // 2 and y < BUTTON_SIZE + 20:
            # Pause button clicked
            game_paused = not game_paused
        elif SCREEN_WIDTH - BUTTON_SIZE - 20 < x < SCREEN_WIDTH and y < BUTTON_SIZE + 20:
            # Exit button clicked
            sys.exit(0)




def point_in_trapezium(px, py, x, y, width, height):
    half_width = width // 2
    half_height = height // 2

    upper_left_x = x - half_width
    upper_right_x = x + half_width
    upper_y = y - half_height


    lower_left_x = x - width // 4
    lower_right_x = x + width // 4
    lower_y = y + half_height


    if py >= upper_y and py <= lower_y:
        if py == upper_y:
            min_x = upper_left_x
            max_x = upper_right_x
        elif py == lower_y:
            min_x = lower_left_x
            max_x = lower_right_x
        else:
            min_x = upper_left_x + (lower_left_x - upper_left_x) * (py - upper_y) / (lower_y - upper_y)
            max_x = upper_right_x + (lower_right_x - upper_right_x) * (py - upper_y) / (lower_y - upper_y)

        if px >= min_x and px <= max_x:
            return True

    return False

def update(value):
    global diamond_y, diamond_x, score, diamond_speed, game_over, current_diamond_color
    if not game_over and not game_paused:
        diamond_y += diamond_speed
        if diamond_y > SCREEN_HEIGHT:
            game_over = True
            update_score_window()
        if point_in_trapezium(diamond_x + DIAMOND_SIZE // 2, diamond_y + DIAMOND_SIZE // 2, catcher_x, catcher_y, CATCHER_WIDTH, CATCHER_HEIGHT):
            score += 1
            diamond_x = random.randint(0, SCREEN_WIDTH - DIAMOND_SIZE)
            diamond_y = 0
            diamond_speed += 1
            current_diamond_color = random.choice(COLORS)
            update_score_window()
    glutPostRedisplay()
    glutTimerFunc(30, update, 0)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_trapezium(catcher_x, catcher_y, CATCHER_WIDTH, CATCHER_HEIGHT, WHITE if not game_over else RED)
    draw_diamond(diamond_x, diamond_y, DIAMOND_SIZE, current_diamond_color)
    draw_button(20, 20, BUTTON_SIZE, CYAN, "left")
    draw_button(SCREEN_WIDTH // 2 - BUTTON_SIZE // 2, 20, BUTTON_SIZE, YELLOW, "pause" if not game_paused else "play")
    draw_button(SCREEN_WIDTH - BUTTON_SIZE - 20, 20, BUTTON_SIZE, RED, "exit")
    glFlush()

def display_text(x, y, text, color):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def update_score_window():
    global root, score_label
    score_label.config(text=f"Score: {score}")
    if game_over:
        score_label.config(text=f"Score: {score}\nGoodbye")


def init():
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, SCREEN_WIDTH, SCREEN_HEIGHT, 0.0, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)

def create_score_window():
    global root, score_label
    root = tk.Tk()
    root.title("Score Window")
    score_label = tk.Label(root, text=f"Score: {score}", font=("Helvetica", 18))
    score_label.pack()
    root.geometry("400x200")
    root.mainloop()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    

    glutInitWindowSize(SCREEN_WIDTH, SCREEN_HEIGHT)
    glutCreateWindow(b"Catch the Diamonds!")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(key_input)
    glutSpecialFunc(special_key_input)
    glutMouseFunc(mouse_input)
    glutTimerFunc(30, update, 0)

    threading.Thread(target=create_score_window).start()
    
    glutMainLoop()

if __name__ == "__main__":
    main()
