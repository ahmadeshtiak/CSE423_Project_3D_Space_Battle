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
first_person_mode = False
camera_mode_timer = 0


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
enemies = []  
max_enemies = 3 
player_health = 100
score = 0
game_start_time = time.time()
last_enemy_destroy_time = 0
enemy_respawn_cooldown = 10 

class Enemy:
    def __init__(self, index):
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        
        self.distance = random.uniform(400, 600)
        
        horizontal_spread = 500
        if max_enemies == 3:
            positions = [-horizontal_spread, 0, horizontal_spread]
            horizontal_offset = positions[index]
        else:
            horizontal_offset = random.uniform(-horizontal_spread, horizontal_spread)
        
        player_angle_rad = math.radians(angle)
        forward_x = -math.sin(player_angle_rad)
        forward_y = -math.cos(player_angle_rad)
        
        right_x = math.cos(player_angle_rad)
        right_y = -math.sin(player_angle_rad)
        
        self.x = ship_x + forward_x * self.distance + right_x * horizontal_offset
        self.y = ship_y + forward_y * self.distance + right_y * horizontal_offset
        self.z = ship_z + random.uniform(-50, 50) 
        
        self.health = 100
        self.base_size = 20  
        self.color = (0.8, 0.2, 0.2)  
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
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        current_distance = math.sqrt((self.x - ship_x)**2 + (self.y - ship_y)**2 + (self.z - ship_z)**2)
        self.distance = current_distance

        self.rotation += 1  
        if self.rotation > 360:
            self.rotation = 0
        
        current_time = time.time()
        if current_distance < 800 and current_time - self.last_shot > self.shot_interval:
            self.shoot()
            self.last_shot = current_time
            

        
    def get_scale(self):
        if self.distance < 100:
            return 2.0
        elif self.distance > 1000:
            return 0.3
        else:
            scale = 2.0 - (1.7 * (self.distance - 100) / 900)
            return max(0.3, min(2.0, scale))
            
    def shoot(self):
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        dx = ship_x - self.x
        dy = ship_y - self.y
        dz = ship_z - self.z
        
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist > 0:
            dx /= dist
            dy /= dist
            dz /= dist
        
        # Create a brief laser effect instead of persistent bullet
        current_time = time.time()
        self.laser_end_time = current_time + 0.3  # Laser lasts only 0.3 seconds
        self.laser_direction = (dx, dy, dz)
        self.laser_distance = dist 

    def update_bullets(self):  
        new_bullets = []
        bullet_speed = 12
        
        for bullet in self.bullets:
            x, y, z, dx, dy, dz, spawn_time = bullet
            x += dx * bullet_speed
            y += dy * bullet_speed
            z += dz * bullet_speed
            
            # Remove distance check - only check lifetime
            if time.time() - spawn_time < 5:  # Keep bullets for 5 seconds regardless of distance
                new_bullets.append([x, y, z, dx, dy, dz, spawn_time])
                    
        self.bullets = new_bullets
        
    def draw_drone_shape(self, scale):
        glPushMatrix()
        glScalef(scale, scale, scale)
        
        glColor3f(0.3, 0.3, 0.3)
        glutSolidSphere(self.base_size * 0.8, 16, 16)
        
        glRotatef(self.rotation, 0, 0, 1)
        
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
        
        glColor3f(0.1, 0.1, 0.1)
        for i in range(4):
            glPushMatrix()
            glRotatef(90 * i + self.rotation * 2, 0, 0, 1)  
            glTranslatef(arm_length, 0, 0)
            glutSolidSphere(self.base_size * 0.4, 12, 12)
            glPopMatrix()
        
        glPopMatrix()
        
    def draw(self):
        scale = self.get_scale()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        self.draw_drone_shape(scale)
        
        # Draw laser if currently firing
        current_time = time.time()
        if hasattr(self, 'laser_end_time') and current_time < self.laser_end_time:
            glColor3f(1, 0.2, 0.2)  # Red laser color
            glLineWidth(1)  # Thicker laser
            
            # Calculate distance to ship to make laser reach exactly to the ship
            ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
            distance_to_ship = math.sqrt((ship_x - self.x)**2 + (ship_y - self.y)**2 + (ship_z - self.z)**2)
            
            # Draw laser beam that reaches exactly to the ship position
            dx, dy, dz = self.laser_direction
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0)  # Start at drone position
            # End at the calculated point that reaches the ship
            glVertex3f(dx * distance_to_ship, dy * distance_to_ship, dz * distance_to_ship)
            glEnd()
            
            glLineWidth(1)  # Reset line width
                
        glPopMatrix()

def spawn_initial_enemies():
    global enemies
    if len(enemies) == 0 and time.time() - game_start_time > 2:
        for i in range(max_enemies):
            enemy = Enemy(i)  
            enemies.append(enemy)
            print(f"Enemy {i+1} spawned at: ({enemy.x:.1f}, {enemy.y:.1f}, {enemy.z:.1f})")
            print(f"Initial distance: {enemy.initial_distance:.1f}")
        print("Enemy drones deployed!")

def update_enemies():
    global enemies, last_enemy_destroy_time
    
    current_time = time.time()
    
    for enemy in enemies[:]:
        enemy.update()
        
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        dist = math.sqrt((enemy.x - ship_x)**2 + (enemy.y - ship_y)**2 + (enemy.z - ship_z)**2)
        
        if dist < 150 or dist > 1000 or (ship_x - enemy.x) * math.sin(math.radians(angle)) + (ship_y - enemy.y) * math.cos(math.radians(angle)) < -100:
            enemies.remove(enemy)
            print(f"Enemy removed (distance: {dist:.1f})")
    
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
        
        if dist > 1200:
            enemies.remove(enemy)
            print(f"Far enemy removed (distance: {dist:.1f})")

def cleanup_old_enemy_bullets():
    global enemies
    for enemy in enemies:
        current_time = time.time()
        enemy.bullets = [b for b in enemy.bullets if current_time - b[6] < 5]  # Keep bullets for 5 seconds

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
            if dist < enemy.base_size * scale * 2:  
                enemy.health -= 40
                if enemy.health <= 0:
                    enemies.remove(enemy)
                    score += 200
                    print(f"Drone destroyed! Score: {score}")
                    if len(enemies) < max_enemies:
                        enemies.append(Enemy(len(enemies))) 
                if bullet in bullets:
                    bullets.remove(bullet)
                break

def toggle_camera_mode():
    global first_person_mode, camera_mode_timer
    current_time = time.time()
    if current_time - camera_mode_timer > 0.5:  # Debounce to prevent rapid toggling
        first_person_mode = not first_person_mode
        camera_mode_timer = current_time
        if first_person_mode:
            print("First-person view activated!")
        else:
            print("Third-person view activated!")

def draw_cockpit():
    if first_person_mode:
        # Switch to 2D orthographic projection for HUD
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 1000)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw simple cockpit frame (crosshairs and basic elements)
        glColor3f(0.8, 0.8, 0.8)
        
        # Crosshairs
        glBegin(GL_LINES)
        # Horizontal line
        glVertex2f(450, 500)
        glVertex2f(550, 500)
        # Vertical line
        glVertex2f(500, 450)
        glVertex2f(500, 550)
        glEnd()
        
        # Cockpit frame elements
        glBegin(GL_QUADS)
        # Bottom panel
        glVertex2f(100, 100)
        glVertex2f(900, 100)
        glVertex2f(900, 200)
        glVertex2f(100, 200)
        
        # Side panels
        glVertex2f(100, 200)
        glVertex2f(200, 200)
        glVertex2f(200, 800)
        glVertex2f(100, 800)
        
        glVertex2f(800, 200)
        glVertex2f(900, 200)
        glVertex2f(900, 800)
        glVertex2f(800, 800)
        glEnd()
        
        # Restore 3D projection
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

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
    global move_1, move_2, vert, ship_angle  
    glPushMatrix()
    glColor3f(0.33, 0.45, 0.19)
    glTranslatef(-move_1, move_2, 100+vert)
    glRotatef(90+ship_angle, 0, 0, 1) 
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
    glColor3f(1, 0, 0)
    new_bullets = []
    for b in bullets:
        x, y, z, dx, dy, dz = b
        x -= dx * bullet_speed
        y += dy * bullet_speed
        z += dz * bullet_speed
        
        # Remove distance check - bullets should be visible until they time out
        # Only check if they've been alive for too long
        glPushMatrix()
        glTranslatef(x, y, z)
        glutSolidSphere(8, 10, 10)  # Increased size for better visibility
        glPopMatrix()
        
        # Keep bullets for longer distance but add timeout
        new_bullets.append((x, y, z, dx, dy, dz))
    
    bullets = new_bullets

def cleanup_old_bullets():
    global bullets
    if len(bullets) > 50:
        bullets = bullets[-50:]

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
    global vert, angle, move_1, move_2, ship_angle
    
    sp = 3 * powerup_effects["speed"]
    
    if key == b'w' or key == b'W':
        rad = math.radians(ship_angle)
        if first_person_mode:
            # First-person: move forward in the direction the ship is facing
            move_1 -= math.sin(rad) * sp  # Fixed: should be minus for forward
            move_2 -= math.cos(rad) * sp  # Fixed: should be minus for forward
        else:
            # Third-person: move forward (ship direction)
            move_1 -= math.sin(rad) * sp
            move_2 -= math.cos(rad) * sp
      
    if key == b's' or key == b'S':
        rad = math.radians(ship_angle)
        if first_person_mode:
            # First-person: move backward opposite to ship direction
            move_1 += math.sin(rad) * sp  # Fixed: should be plus for backward
            move_2 += math.cos(rad) * sp  # Fixed: should be plus for backward
        else:
            # Third-person: move backward
            move_1 += math.sin(rad) * sp
            move_2 += math.cos(rad) * sp
    
    if key == b'a' or key == b'A':
        if first_person_mode:
            # First-person: strafe left (perpendicular to ship direction)
            rad = math.radians(ship_angle)
            move_1 -= math.cos(rad) * sp  # Fixed: minus for left strafe
            move_2 += math.sin(rad) * sp  # Fixed: plus for left strafe
        else:
            # Third-person: rotate ship left (counter-clockwise)
            ship_angle += 15  # Fixed: should be minus for left rotation
            if ship_angle < 0:
                ship_angle += 360
    
    if key == b'd' or key == b'D':
        if first_person_mode:
            # First-person: strafe right (perpendicular to ship direction)
            rad = math.radians(ship_angle)
            move_1 += math.cos(rad) * sp  # Fixed: plus for right strafe
            move_2 -= math.sin(rad) * sp  # Fixed: minus for right strafe
        else:
            # Third-person: rotate ship right (clockwise)
            ship_angle -= 15  # Fixed: should be plus for right rotation
            if ship_angle > 360:
                ship_angle -= 360
    
    # Toggle camera mode with C key
    if key == b'c' or key == b'C':
        toggle_camera_mode()

def specialKeyListener(key, x, y):
    global camera_pos, move_1, move_2, angle, vert
    
    sp = 3 * powerup_effects["speed"]
    
    if key == GLUT_KEY_LEFT:
        angle += 15
        if angle > 360:
            angle -= 360
    

    if key == GLUT_KEY_RIGHT:
        angle -= 15
        if angle < 0:
            angle += 360
    

    if key == GLUT_KEY_UP:
        vert += 3
    
    if key == GLUT_KEY_DOWN:
        vert -= 3
    
    # Update camera position
    x, y, z = camera_pos
    camera_pos = (x, y, z)


def mouseListener(button, state, x, y):
    global bullets, move_1, move_2, vert, ship_angle
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        rad = math.radians(ship_angle)
        
        dx = -math.sin(rad)
        dy = -math.cos(rad)
        dz = 0
        
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        
        bullet_offset = 60  
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
    
    ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
    
    if first_person_mode:
        # First-person view from cockpit
        player_angle_rad = math.radians(ship_angle)  # Use ship angle for FPS view
        
        # Camera position: inside the ship cockpit
        camera_x = ship_x
        camera_y = ship_y
        camera_z = ship_z + 30  # Slightly above ship center
        
        # Calculate look-at direction based on ship rotation
        look_x = ship_x - math.sin(player_angle_rad) * 100
        look_y = ship_y - math.cos(player_angle_rad) * 100
        look_z = ship_z
        
        gluLookAt(camera_x, camera_y, camera_z,  # Camera position (cockpit)
                  look_x, look_y, look_z,        # Look direction (where ship is pointing)
                  0, 0, 1)                      # Up vector
    else:
        # Third-person view (original)
        player_angle_rad = math.radians(angle)
        
        # Camera position: behind and above the player
        camera_distance = 300
        camera_height = 150
        camera_x = ship_x + math.sin(player_angle_rad) * camera_distance
        camera_y = ship_y + math.cos(player_angle_rad) * camera_distance
        camera_z = ship_z + camera_height
        
        gluLookAt(camera_x, camera_y, camera_z,  # Camera position
                  ship_x, ship_y, ship_z,        # Look at player
                  0, 0, 1) 
       


def idle():
    check_powerup_collision()
    spawn_initial_enemies()
    update_enemies()
    cleanup_far_enemies()
    cleanup_old_bullets()
    check_bullet_enemy_collision()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 1000)
    setupCamera()
    
    # Draw 3D scene
    draw_stars()
    draw_arena()
    draw_powerups()
    if not first_person_mode:  # Don't draw own ship in first-person view
        draw_shapes()
    draw_bullets()
    draw_enemies()
    
    # Draw cockpit overlay if in first-person mode
    draw_cockpit()
    
    # Display info with debug
    draw_text(20, 970, f"Health: {player_health}")
    draw_text(20, 940, f"Score: {score}")
    draw_text(20, 910, f"Drones: {len(enemies)}/{max_enemies}")
    draw_text(20, 880, f"View: {'1st Person' if first_person_mode else '3rd Person'}")
    
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
