from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

# Camera-related variables
camera_pos = (0, 250, 250)
fovY = 120
GRID_LENGTH = 600
angle = 0
move_1 = 0
move_2 = 0
vert = 0

# Bullets (x,y,z,dx,dy,dz)
bullets = []
bullet_speed = 5

# Power-ups (x,y,z,type)
powerups = []
powerup_effects = {"speed": 1, "firerate": 1, "shield": False}
last_powerup_time = 0

# Arena settings
arena_size = 800

# Random stars
stars = [(random.randint(-1500,1500), random.randint(-1500,1500), random.randint(-1500,1500)) for _ in range(500)]

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 1000)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_shapes():
    global angle, move_1, move_2, vert
    glPushMatrix()
    glColor3f(0.33, 0.45, 0.19)
    glTranslatef(-move_1, move_2, 100+vert)
    glRotatef(90+angle, 0, 0, 1)
    glRotatef(-90, 0, 0, 1)
    glutSolidCube(100)
    glColor3f(0.15, 0.25, 0.19)
    glTranslatef(50, 0, -10)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 40, 5, 150, 10, 10)
    glRotatef(-90, 0, 1, 0)
    glTranslatef(-100, 0, 0)
    glRotatef(-90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 40, 5, 150, 10, 10)
    glColor3f(0.2, 0.7, 0.6)
    glRotatef(90, 0, 1, 0)
    glTranslatef(50, 0, 0)
    glTranslatef(20, 100, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 5, 60, 10, 10)
    glTranslatef(-40, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 5, 60, 10, 10)
    glColor3f(0.1, 0.2, 0.3)
    glRotatef(-90, 1, 0, 0)
    glTranslatef(-20, -100, 0)
    glTranslatef(40, -40, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 40, 5, 150, 10, 10)
    glPopMatrix()

def draw_bullets():
    global bullets
    glColor3f(1,0,0)
    new_bullets = []
    for b in bullets:
        x,y,z,dx,dy,dz = b
        x += dx*bullet_speed
        y += dy*bullet_speed
        z += dz*bullet_speed
        if abs(x)<arena_size and abs(y)<arena_size and abs(z)<arena_size:
            glPushMatrix()
            glTranslatef(x,y,z)
            glutSolidSphere(5,10,10)
            glPopMatrix()
            new_bullets.append((x,y,z,dx,dy,dz))
    bullets = new_bullets

def draw_powerups():
    global powerups
    glColor3f(0,1,0)
    for (x,y,z,t) in powerups:
        glPushMatrix()
        glTranslatef(x,y,z)
        glutSolidSphere(15,10,10)
        glPopMatrix()

def check_powerup_collision():
    global move_1, move_2, vert, powerups, powerup_effects
    ship_pos = (-move_1, move_2, 100+vert)
    new_list=[]
    for (x,y,z,t) in powerups:
        if abs(ship_pos[0]-x)<30 and abs(ship_pos[1]-y)<30 and abs(ship_pos[2]-z)<30:
            if t=="speed": powerup_effects["speed"]=2
            elif t=="firerate": powerup_effects["firerate"]=2
            elif t=="shield": powerup_effects["shield"]=True
        else:
            new_list.append((x,y,z,t))
    powerups=new_list

def draw_arena():
    glColor3f(0.3,0.3,0.8)
    glBegin(GL_LINES)
    for i in [-arena_size,arena_size]:
        for j in [-arena_size,arena_size]:
            for k in [-arena_size,arena_size]:
                glVertex3f(i,j,-arena_size)
                glVertex3f(i,j,arena_size)
    glEnd()

def draw_stars():
    glColor3f(1,1,1)
    glBegin(GL_POINTS)
    for (x,y,z) in stars:
        glVertex3f(x,y,z)
    glEnd()

def keyboardListener(key, x, y):
    global vert
    if key == b'u': vert+=3
    if key == b'd': vert-=3

def specialKeyListener(key, x, y):
    global camera_pos,move_1,move_2,angle
    x,y,z=camera_pos
    sp=3*powerup_effects["speed"]
    if key==GLUT_KEY_UP:
        rad=math.radians(angle)
        move_1-=math.sin(rad)*sp
        move_2-=math.cos(rad)*sp
    if key==GLUT_KEY_DOWN:
        rad=math.radians(angle)
        move_1+=math.sin(rad)*sp
        move_2+=math.cos(rad)*sp
    if key==GLUT_KEY_LEFT: angle+=30
    if key==GLUT_KEY_RIGHT: angle-=30
    camera_pos=(x,y,z)

def mouseListener(button,state,x,y):
    global bullets,angle,move_1,move_2,vert
    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        rad=math.radians(angle)
        dx,dy,dz=-math.sin(rad),-math.cos(rad),0
        ship_x,ship_y,ship_z=-move_1,move_2,100+vert
        bullets.append((ship_x,ship_y,ship_z,dx,dy,dz))

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY,1,0.1,3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x,y,z=camera_pos
    gluLookAt(x,y,z,0,0,0,0,0,1)

def idle():
    check_powerup_collision()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0,0,1000,1000)
    setupCamera()
    draw_stars()
    draw_arena()
    draw_powerups()
    draw_shapes()
    draw_bullets()
    glutSwapBuffers()

def main():
    global powerups
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(1000,1000)
    glutInitWindowPosition(0,0)
    glutCreateWindow(b"OpenGL Battleship Arena")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    # Generate random powerups
    for _ in range(10):
        t=random.choice(["speed","firerate","shield"])
        x=random.randint(-arena_size//2,arena_size//2)
        y=random.randint(-arena_size//2,arena_size//2)
        z=random.randint(50,200)
        powerups.append((x,y,z,t))
    glutMainLoop()

if __name__=="__main__":
    main()
