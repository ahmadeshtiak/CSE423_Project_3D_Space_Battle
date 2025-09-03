from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
# Camera-related variables
camera_pos = (0,250,250)

fovY = 120  # Field of view
GRID_LENGTH = 600  # Length of grid lines
rand_var = 423
angle=0
move_1=0
move_2=0
vert=0
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 1000)  # left, right, bottom, top

    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_shapes():
    global angle,move_1,move_2,vert
    glPushMatrix()  # Save the current matrix state
    glColor3f(0.33, 0.45, 0.19)
    glTranslatef(0-move_1,0+move_2, 100+vert)
    glRotatef(90+angle, 0, 0, 1)
    glRotatef(-90, 0, 0, 1)
    #glTranslatef(0+move_1,0+move_2, 100)
    #glRotatef(90, 1, 0, 0)  
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
    glPopMatrix()  # Restore the previous matrix state


def keyboardListener(key, x, y):
    """
    

    Handles keyboard inputs for player movement, gun rotation, camera updates, and cheat mode toggles.
    """
    # # Move forward (W key)
    global vert
    if key == b'u':  
        vert+=3
    if key==b"d":
        vert-=3

    # # Move backward (S key)
    # if key == b's':

    # # Rotate gun left (A key)
    # if key == b'a':

    # # Rotate gun right (D key)
    # if key == b'd':

    # # Toggle cheat mode (C key)
    # if key == b'c':

    # # Toggle cheat vision (V key)
    # if key == b'v':

    # # Reset the game if R key is pressed
    # if key == b'r':


def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    global camera_pos,move_1,move_2,angle
    x, y, z = camera_pos
    sp=3
    # Move camera up (UP arrow key)
    if key == GLUT_KEY_UP:
        radian=math.radians(angle)
        
        move_1-=math.sin(radian)*sp
        move_2-=math.cos(radian)*sp

        
    # # Move camera down (DOWN arrow key)
    if key == GLUT_KEY_DOWN:
        radian=math.radians(angle)
        
        move_1+=math.sin(radian)*sp
        move_2+=math.cos(radian)*sp

    # moving camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        angle += 30  # Small angle decrement for smooth movement
        
    # moving camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        angle-= 30  # Small angle increment for smooth movement
        
    camera_pos = (x, y, z)


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs for firing bullets (left click) and toggling camera mode (right click).
    """
        # # Left mouse button fires a bullet
        # if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:

        # # Right mouse button toggles camera tracking mode
        # if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:


def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    # Set up a perspective projection (field of view, aspect ratio, near clip, far clip)
    gluPerspective(fovY, 1, 0.1, 1500) # Think why aspect ration is 1.25?
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix

    # Extract camera position and look-at target
    x, y, z = camera_pos
    # Position the camera and set its orientation
    gluLookAt(x, y, z,  # Camera position
              0, 0, 0,  # Look-at target
              0, 0, 1)  # Up vector (z-axis)


def idle():
    """
    Idle function that runs continuously:
    - Triggers screen redraw for real-time updates.
    """
    # Ensure the screen updates with the latest changes
    glutPostRedisplay()


def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws everything of the screen
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 1000)  # Set viewport size

    setupCamera()  # Configure camera perspective

    # Draw a random points
    glPointSize(20)
    glBegin(GL_POINTS)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()

    # Draw the grid (game floor)
    

    # Display game info text at a fixed screen position
    glBegin(GL_QUADS)
    
    glColor3f(1, 1, 1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)

    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(0, -GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(GRID_LENGTH, 0, 0)


    glColor3f(0.7, 0.5, 0.95)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, -GRID_LENGTH, 0)

    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glEnd()

    draw_shapes()

    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()


# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 1000)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"3D OpenGL Intro")  # Create the window

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to move the bullet automatically

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
