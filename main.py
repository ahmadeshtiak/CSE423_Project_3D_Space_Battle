from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

# Camera-related variables
camera_pos = (0, 250, 250)
fovY = 120
GRID_LENGTH = 600
angle = 0
ship_angle = 0
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


# Enemy variabls
enemies = []  # List to store enemy drones
max_enemies = 3  # Maximum of 3 enemies at once
player_health = 100
score = 0
game_start_time = time.time()
last_enemy_destroy_time = 0
enemy_respawn_cooldown = 10 

class Enemy:
    def __init__(self, index):
        # Spawn enemy horizontally in front of the player
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        
        # Start at medium distance (400-600 units)
        self.distance = random.uniform(400, 600)
        
        # Position enemies horizontally (left, center, right)
        horizontal_spread = 200  # Spread enemies horizontally
        if max_enemies == 3:
            positions = [-horizontal_spread, 0, horizontal_spread]
            horizontal_offset = positions[index]
        else:
            horizontal_offset = random.uniform(-horizontal_spread, horizontal_spread)
        
        # Calculate position based on player's forward direction
        player_angle_rad = math.radians(angle)
        forward_x = -math.sin(player_angle_rad)
        forward_y = -math.cos(player_angle_rad)
        
        # Calculate right vector for horizontal offset
        right_x = math.cos(player_angle_rad)
        right_y = -math.sin(player_angle_rad)
        
        # Set position with horizontal spread
        self.x = ship_x + forward_x * self.distance + right_x * horizontal_offset
        self.y = ship_y + forward_y * self.distance + right_y * horizontal_offset
        self.z = ship_z + random.uniform(-50, 50)  # Small vertical variation
        
        self.health = 100
        self.base_size = 20  # Base size that will scale with distance
        self.color = (0.8, 0.2, 0.2)  # Dark red color
        self.last_shot = time.time()
        self.shot_interval = random.uniform(3.0, 5.0)
        self.bullets = []
        self.rotation = 0
        self.spawn_time = time.time()
        self.initial_distance = self.calculate_initial_distance()

    def calculate_initial_distance(self):
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        return math.sqrt((self.x - ship_x)**2 + (self.y - ship_y)**2 + (self.z - ship_z)**2)

    def update(self):
        # Update distance to player
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        current_distance = math.sqrt((self.x - ship_x)**2 + (self.y - ship_y)**2 + (self.z - ship_z)**2)
        self.distance = current_distance

        self.rotation += 1  # Faster rotation
        if self.rotation > 360:
            self.rotation = 0
        
        # Shoot at player periodically (only when close enough)
        current_time = time.time()
        if current_distance < 800 and current_time - self.last_shot > self.shot_interval:
            self.shoot()
            self.last_shot = current_time
            
        # Update bullets
        self.update_bullets()
        
    def get_scale(self):
        # Scale based on distance - smaller when far, larger when close
        # Scale from 0.3 to 2.0 as distance decreases from 1000 to 100
        if self.distance < 100:
            return 2.0
        elif self.distance > 1000:
            return 0.3
        else:
            # Linear scaling: 2.0 at 100 units, 0.3 at 1000 units
            scale = 2.0 - (1.7 * (self.distance - 100) / 900)
            return max(0.3, min(2.0, scale))
        
    def shoot(self):
        # Calculate direction to player
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        dx = ship_x - self.x
        dy = ship_y - self.y
        dz = ship_z - self.z
        
        # Normalize direction
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist > 0:
            dx /= dist
            dy /= dist
            dz /= dist
            
        # Add bullet
        self.bullets.append([self.x, self.y, self.z, dx, dy, dz, time.time()])  # Add spawn time
        
    def update_bullets(self):  # ADD THIS MISSING METHOD
        # Update bullet positions
        new_bullets = []
        bullet_speed = 12
        
        for bullet in self.bullets:
            x, y, z, dx, dy, dz, spawn_time = bullet
            x += dx * bullet_speed
            y += dy * bullet_speed
            z += dz * bullet_speed
            
            # Remove bullets after 5 seconds or if they go too far
            if (time.time() - spawn_time < 5 and 
                abs(x) < 2000 and abs(y) < 2000 and abs(z) < 2000):
                new_bullets.append([x, y, z, dx, dy, dz, spawn_time])
                
        self.bullets = new_bullets
        
    def draw_drone_shape(self, scale):
        # Draw a drone-like shape (X-shaped with central body)
        glPushMatrix()
        glScalef(scale, scale, scale)
        
        # Central body (sphere)
        glColor3f(0.3, 0.3, 0.3)
        glutSolidSphere(self.base_size * 0.8, 16, 16)
        
        # Rotate the arms
        glRotatef(self.rotation, 0, 0, 1)
        
        # Four arms in X formation
        arm_length = self.base_size * 2
        arm_thickness = self.base_size * 0.3
        
        glColor3f(0.8, 0.2, 0.2)
        for i in range(4):
            glPushMatrix()
            glRotatef(90 * i, 0, 0, 1)
            glTranslatef(arm_length/2, 0, 0)
            glScalef(arm_length, arm_thickness, arm_thickness)
            glutSolidCube(1)
            glPopMatrix()
        
        # Propellers at the end of each arm
        glColor3f(0.1, 0.1, 0.1)
        for i in range(4):
            glPushMatrix()
            glRotatef(90 * i + self.rotation * 2, 0, 0, 1)  # Faster rotation for propellers
            glTranslatef(arm_length, 0, 0)
            glutSolidSphere(self.base_size * 0.4, 12, 12)
            glPopMatrix()
        
        glPopMatrix()
        
    def draw(self):
        scale = self.get_scale()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Draw the drone
        self.draw_drone_shape(scale)
        
        # Draw enemy bullets (laser beams)
        glColor3f(1, 0.2, 0.2)  # Red laser color
        for x, y, z, dx, dy, dz, spawn_time in self.bullets:
            # Draw as line segments for laser effect
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0)
            glVertex3f(x - self.x, y - self.y, z - self.z)
            glEnd()
            
        glPopMatrix()

def spawn_initial_enemies():
    global enemies
    if len(enemies) == 0 and time.time() - game_start_time > 2:
        for i in range(max_enemies):
            enemy = Enemy(i)  # Pass index for horizontal positioning
            enemies.append(enemy)
            print(f"Enemy {i+1} spawned at: ({enemy.x:.1f}, {enemy.y:.1f}, {enemy.z:.1f})")
            print(f"Initial distance: {enemy.initial_distance:.1f}")
        print("Enemy drones deployed!")

def update_enemies():
    global enemies, last_enemy_destroy_time
    
    current_time = time.time()
    
    # Remove enemies that are too close OR too far
    for enemy in enemies[:]:
        enemy.update()
        
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        dist = math.sqrt((enemy.x - ship_x)**2 + (enemy.y - ship_y)**2 + (enemy.z - ship_z)**2)
        
        # Remove enemy if too close OR too far (behind or very distant)
        if dist < 150 or dist > 1000 or (ship_x - enemy.x) * math.sin(math.radians(angle)) + (ship_y - enemy.y) * math.cos(math.radians(angle)) < -100:
            enemies.remove(enemy)
            print(f"Enemy removed (distance: {dist:.1f})")
    
    # Respawn enemies only if cooldown has passed and we need more enemies
    if (len(enemies) < max_enemies and 
        current_time - last_enemy_destroy_time > enemy_respawn_cooldown):
        
        # Respawn all missing enemies at once
        while len(enemies) < max_enemies:
            new_enemy = Enemy(len(enemies))
            enemies.append(new_enemy)
            print(f"Enemy respawned at distance: {new_enemy.distance:.1f}")
        
        last_enemy_destroy_time = current_time 
def cleanup_far_enemies():
    global enemies
    
    ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
    
    for enemy in enemies[:]:
        dist = math.sqrt((enemy.x - ship_x)**2 + (enemy.y - ship_y)**2 + (enemy.z - ship_z)**2)
        
        # Remove enemy if it's very far away (behind player or too distant)
        if dist > 1200:
            enemies.remove(enemy)
            print(f"Far enemy removed (distance: {dist:.1f})")

def draw_enemies():
    for enemy in enemies:
        enemy.draw()

def check_bullet_enemy_collision():
    global enemies, score, bullets
    
    for bullet in bullets[:]:
        x, y, z, dx, dy, dz = bullet
        for enemy in enemies[:]:
            dist = math.sqrt((x - enemy.x)**2 + (y - enemy.y)**2 + (z - enemy.z)**2)
            scale = enemy.get_scale()
            if dist < enemy.base_size * scale * 2:  # Collision based on scaled size
                enemy.health -= 40
                if enemy.health <= 0:
                    enemies.remove(enemy)
                    score += 200
                    print(f"Drone destroyed! Score: {score}")
                    # Spawn new enemy to maintain count
                    if len(enemies) < max_enemies:
                        enemies.append(Enemy(len(enemies)))  # FIXED: Added index parameter
                if bullet in bullets:
                    bullets.remove(bullet)
                break


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
    global move_1, move_2, vert, ship_angle  # Remove angle, add ship_angle
    glPushMatrix()
    glColor3f(0.33, 0.45, 0.19)
    glTranslatef(-move_1, move_2, 100+vert)
    glRotatef(90+ship_angle, 0, 0, 1)  # Change angle to ship_angle
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
        x -= dx*bullet_speed
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


# Add a new global variable for ship rotation

# Replace the keyboardListener function with this:
def keyboardListener(key, x, y):
    global vert, angle, move_1, move_2, ship_angle
    
    sp = 3 * powerup_effects["speed"]
    
    # W key - Move forward (relative to ship rotation)
    if key == b'w' or key == b'W':
        rad = math.radians(ship_angle)  # Use ship_angle for movement
        move_1 -= math.sin(rad) * sp
        move_2 -= math.cos(rad) * sp
      
    # S key - Move backward (relative to ship rotation)
    if key == b's' or key == b'S':
        rad = math.radians(ship_angle)  # Use ship_angle for movement
        move_1 += math.sin(rad) * sp
        move_2 += math.cos(rad) * sp
    
    # A key - Rotate ship left 15 degrees (ship only)
    if key == b'a' or key == b'A':
        ship_angle += 15
        if ship_angle > 360:
            ship_angle -= 360
    
    # D key - Rotate ship right 15 degrees (ship only)
    if key == b'd' or key == b'D':
        ship_angle -= 15
        if ship_angle < 0:
            ship_angle += 360
    
    # U key - Move upward
    if key == b'u': vert += 3

def specialKeyListener(key, x, y):
    global camera_pos, move_1, move_2, angle, vert
    
    sp = 3 * powerup_effects["speed"]
    
    # LEFT arrow - Rotate camera/view left
    if key == GLUT_KEY_LEFT:
        angle += 15
        if angle > 360:
            angle -= 360
    
    # RIGHT arrow - Rotate camera/view right  
    if key == GLUT_KEY_RIGHT:
        angle -= 15
        if angle < 0:
            angle += 360
    
    # UP arrow - Move ship upward
    if key == GLUT_KEY_UP:
        vert += 3
    
    # DOWN arrow - Move ship downward
    if key == GLUT_KEY_DOWN:
        vert -= 3
    
    # Update camera position
    x, y, z = camera_pos
    camera_pos = (x, y, z)
# Replace the mouseListener function with this:

def mouseListener(button, state, x, y):
    global bullets, move_1, move_2, vert, ship_angle
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Use ship_angle for bullet direction (where the ship is pointing)
        rad = math.radians(ship_angle)
        
        # Calculate direction based on ship rotation
        dx = -math.sin(rad)
        dy = -math.cos(rad)
        dz = 0
        
        # Calculate bullet spawn position at the front of the ship
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        
        # Move bullet spawn position to the front edge of the ship
        bullet_offset = 60  # Distance from ship center to front edge
        bullet_x = ship_x + dx * bullet_offset
        bullet_y = ship_y + dy * bullet_offset
        bullet_z = ship_z + dz * bullet_offset
        
        bullets.append((bullet_x, bullet_y, bullet_z, dx, dy, dz))

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Camera follows the player from behind and above
    ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
    player_angle_rad = math.radians(angle)
    
    # Camera position: behind and above the player
    camera_distance = 300
    camera_height = 150
    camera_x = ship_x + math.sin(player_angle_rad) * camera_distance
    camera_y = ship_y + math.cos(player_angle_rad) * camera_distance
    camera_z = ship_z + camera_height
    
    gluLookAt(camera_x, camera_y, camera_z,  # Camera position
              ship_x, ship_y, ship_z,       # Look at player
              0, 0, 1)       


def idle():
    check_powerup_collision()
    spawn_initial_enemies()
    update_enemies()
    cleanup_far_enemies()
    check_bullet_enemy_collision()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 1000)
    setupCamera()
    draw_stars()
    draw_arena()
    draw_powerups()
    draw_shapes()
    draw_bullets()
    draw_enemies()
    
    # Display info with debug
    draw_text(20, 970, f"Health: {player_health}")
    draw_text(20, 940, f"Score: {score}")
    draw_text(20, 910, f"Drones: {len(enemies)}/{max_enemies}")
    
    
    glutSwapBuffers()

def main():
    global powerups, game_start_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 1000)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Space Battle - Drone Enemies")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    game_start_time = time.time()
    
    # Generate random powerups
    for _ in range(8):
        t = random.choice(["speed", "firerate", "shield"])
        x = random.randint(-arena_size//2, arena_size//2)
        y = random.randint(-arena_size//2, arena_size//2)
        z = random.randint(50, 200)
        powerups.append((x, y, z, t))
    
    print("Game started! Enemy drones will appear in the distance.")
    print("They will grow larger as you approach and fire laser beams.")
    
    glutMainLoop()

if __name__=="__main__":
    main()
