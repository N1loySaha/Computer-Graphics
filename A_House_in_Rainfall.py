from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random
import math


raindrops = []
raindrop_speed = 0.05
rain_angle = 0  # Angle in degrees


background_color = [0.0, 0.0, 0.0]
color_change_speed = 0.01


def draw_points(x, y):
    glPointSize(4)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def draw_lines(x1, y1, x2, y2):
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()

def draw_triangles(x1, y1, x2, y2, x3, y3):
    glBegin(GL_TRIANGLES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glVertex2f(x3, y3)
    glEnd()


def init_raindrops():
    global raindrops
    raindrops = []
    for i in range(100):
        x = random.randint(-1000, 1500)
        y = random.randint(500, 1000)
        raindrops.append([x, y])

def draw_baarish():
    global rain_angle
    angle_radians = math.radians(rain_angle)  # Convert angle in radian
    xprime = 10 * math.sin(angle_radians)
    yprime = 10 * math.cos(angle_radians)
    
    glLineWidth(2)
    glBegin(GL_LINES)
    for i in raindrops:
        x, y = i
        glVertex2f(x, y)
        glVertex2f(x - xprime, y - yprime)
    glEnd()

def iterate():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def showScreen():
    global background_color

    glClearColor(background_color[0], background_color[1], background_color[2], 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    iterate()

    # House
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(5)
    draw_lines(50, 50, 450, 50)
    draw_lines(50, 50, 50, 300)
    draw_lines(450, 50, 450, 300)
    
    # Roof
    glColor3f(1.0, 1.0, 1.0)
    draw_triangles(40, 300, 460, 300, 250, 450)
    glColor3f(0.0, 0.0, 0.0)
    draw_triangles(100, 320, 400, 320, 250, 430)

    
    # Door
    glLineWidth(1)
    glColor3f(1.0, 1.0, 1.0)
    draw_lines(135, 50, 135, 225)
    draw_lines(215, 50, 215, 225)
    draw_lines(135, 225, 215, 225)

    # Door lock
    draw_points(205, 150)

    # Window
    draw_lines(300, 150, 400, 150)
    draw_lines(300, 150, 300, 250)
    draw_lines(400, 150, 400, 250)
    draw_lines(300, 250, 400, 250)
    draw_lines(300, 200, 400, 200)
    draw_lines(350, 150, 350, 250)

    # Draw rain
    glColor3f(0.0, 1.0, 1.0)
    draw_baarish()

    glutSwapBuffers()

def keyboardListener(key, x, y):
    global background_color, color_change_speed

    if key == b'd':  # night to day
        if background_color[0] < 1.0:
            background_color[0] += color_change_speed
        if background_color[1] < 1.0:
            background_color[1] += color_change_speed
        if background_color[2] < 1.0:
            background_color[2] += color_change_speed
    elif key == b'n':  # day to night
        if background_color[0] > 0.0:
            background_color[0] -= color_change_speed
        if background_color[1] > 0.0:
            background_color[1] -= color_change_speed
        if background_color[2] > 0.0:
            background_color[2] -= color_change_speed

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global rain_angle
    if key == GLUT_KEY_LEFT:
        rain_angle += 0.8
        print("Left bended")
    if key == GLUT_KEY_RIGHT:
        rain_angle -= 0.8
        print("Right bended")
    glutPostRedisplay()
    
def animate():
    global raindrops, raindrop_speed, rain_angle

    angle_radians = math.radians(rain_angle)
    xprime = raindrop_speed * math.sin(angle_radians)
    yprime = raindrop_speed * math.cos(angle_radians)

    for i in raindrops:
        i[0] -= xprime
        i[1] -= yprime
        if i[1] < 300 or i[0] < -500 or i[0] > 1000:
            i[0] = random.randint(-1000, 1500)
            i[1] = random.randint(500, 1000)

    glutPostRedisplay()

glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(500, 500)
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Task - 1")
glutDisplayFunc(showScreen)
glutIdleFunc(animate)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)

init_raindrops()
glutMainLoop()
