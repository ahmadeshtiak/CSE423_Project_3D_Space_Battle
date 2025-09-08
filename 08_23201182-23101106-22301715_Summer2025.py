from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, random, time

# Game state constants
START_SCREEN = 0
PLAYING = 1
GAME_OVER = 2

# Initialize game state
game_state = START_SCREEN

# Camera-related variables
camera_pos = (0, 250, 250)
fovY = 120
GRID_LENGTH = 600
angle = 0
ship_angle = 0
ship_roll = 0
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
p_speed = False

# Arena settings
arena_size = 800

# Random stars
stars = [(random.randint(-1500,1500), random.randint(-1500,1500), random.randint(-1500,1500)) for _ in range(500)]
#powerup effect vars
powerup_durations = {"speed": 10, "firerate": 10, "shield": 10}
powerup_timers = {"speed": 0, "firerate": 0, "shield": 0}

# Enemy variables
enemies = []  
max_enemies = 3 
player_health = 100
score = 0
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
        
        current_time = time.time()
        self.laser_end_time = current_time + 0.3  
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
            
            if time.time() - spawn_time < 5: 
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
        
        current_time = time.time()
        if hasattr(self, 'laser_end_time') and current_time < self.laser_end_time:
            glColor3f(1, 0.2, 0.2)  
            glLineWidth(1) 
            
            ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
            distance_to_ship = math.sqrt((ship_x - self.x)**2 + (ship_y - self.y)**2 + (ship_z - self.z)**2)
            
            dx, dy, dz = self.laser_direction
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0)  
            glVertex3f(dx * distance_to_ship, dy * distance_to_ship, dz * distance_to_ship)
            glEnd()
            
            glLineWidth(1)  
                
        glPopMatrix()

def spawn_initial_enemies():
    global enemies
    if len(enemies) == 0:
        for i in range(max_enemies):
            enemy = Enemy(i)  
            enemies.append(enemy)

def update_enemies():
    global enemies, last_enemy_destroy_time
    
    current_time = time.time()
    
    for enemy in enemies[:]:
        enemy.update()
        
        ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
        dist = math.sqrt((enemy.x - ship_x)**2 + (enemy.y - ship_y)**2 + (enemy.z - ship_z)**2)
        
        if dist < 150 or dist > 1000 or (ship_x - enemy.x) * math.sin(math.radians(angle)) + (ship_y - enemy.y) * math.cos(math.radians(angle)) < -100:
            enemies.remove(enemy)
    
    if (len(enemies) < max_enemies and 
        current_time - last_enemy_destroy_time > enemy_respawn_cooldown):
        
        # Respawn all missing enemies at once
        while len(enemies) < max_enemies:
            new_enemy = Enemy(len(enemies))
            enemies.append(new_enemy)
        
        last_enemy_destroy_time = current_time 

def cleanup_far_enemies():
    global enemies
    ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
    for enemy in enemies[:]:
        dist = math.sqrt((enemy.x - ship_x)**2 + (enemy.y - ship_y)**2 + (enemy.z - ship_z)**2)
        
        if dist > 1200:
            enemies.remove(enemy)

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
                    if len(enemies) < max_enemies:
                        enemies.append(Enemy(len(enemies))) 
                if bullet in bullets:
                    bullets.remove(bullet)
                break

def toggle_camera_mode():
    global first_person_mode, camera_mode_timer
    current_time = time.time()
    if current_time - camera_mode_timer > 0.5: 
        first_person_mode = not first_person_mode
        camera_mode_timer = current_time

def draw_cockpit():
    if first_person_mode:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 1000)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
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
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

def draw_start_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 1000)
    
    # Set up orthographic projection for 2D text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 1000)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw title
    glColor3f(1, 1, 1)
    text = "3D SPACE BATTLE ARENA"
    glRasterPos2f(350, 700)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Draw instructions
    instructions = [
        "Controls:",
        "W/S - Move forward/backward",
        "A/D - Rotate ship",
        "J/L - Roll ship",
        "P/O - Power up/down",
        "Arrow Keys - Adjust camera",
        "Left Click - Fire weapon",
        "C - Toggle camera view",
        "",
        "Press SPACE to start/pause",
        "Press R to restart"
    ]
    
    y_pos = 600
    for line in instructions:
        glRasterPos2f(400, y_pos)
        for ch in line:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        y_pos -= 30
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_game_over_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 1000)
    
    # Set up orthographic projection for 2D text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 1000)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw game over text
    glColor3f(1, 0, 0)
    text = "GAME OVER"
    glRasterPos2f(400, 700)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Draw score
    glColor3f(1, 1, 1)
    score_text = f"Final Score: {score}"
    glRasterPos2f(430, 600)
    for ch in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Draw restart instructions
    instructions = [
        "Press R to restart",
        "Press ESC to quit"
    ]
    
    y_pos = 500
    for line in instructions:
        glRasterPos2f(430, y_pos)
        for ch in line:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        y_pos -= 30
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def reset_game():
    global game_state, player_health, score, enemies, bullets, powerups
    global move_1, move_2, vert, angle, ship_angle, ship_roll
    
    # Reset game variables
    player_health = 100
    score = 0
    enemies = []
    bullets = []
    powerups = []
    move_1 = 0
    move_2 = 0
    vert = 0
    angle = 0
    ship_angle = 0
    ship_roll = 0  # Reset roll angle
    
    # Initialize powerups
    for _ in range(8):
        t = random.choice(["speed", "firerate", "shield"])
        x = random.randint(-arena_size//2, arena_size//2)
        y = random.randint(-arena_size//2, arena_size//2)
        z = random.randint(50, 200)
        powerups.append((x, y, z, t))
    game_state = PLAYING

def check_powerup_collision():
    global move_1, move_2, vert, powerups, powerup_effects, powerup_timers
    ship_pos = (-move_1, move_2, 100+vert)
    new_list=[]
    for (x,y,z,t) in powerups:
        if abs(ship_pos[0]-x)<30 and abs(ship_pos[1]-y)<30 and abs(ship_pos[2]-z)<30:
            powerup_effects[t] = 2 if t in ["speed","firerate"] else True
            powerup_timers[t] = time.time()
        else:
            new_list.append((x,y,z,t))
    powerups=new_list
def update_powerups():
    global powerup_effects, powerup_timers
    current = time.time()
    for t in ["speed","firerate","shield"]:
        if powerup_effects[t] != (1 if t!="shield" else False):
            if current - powerup_timers[t] > powerup_durations[t]:
                powerup_effects[t] = 1 if t!="shield" else False
def check_enemy_laser_hits():
    global enemies, player_health, powerup_effects
    ship_x, ship_y, ship_z = -move_1, move_2, 100 + vert
    for enemy in enemies:
        if hasattr(enemy, 'laser_end_time') and time.time() < enemy.laser_end_time:
            dx, dy, dz = enemy.laser_direction
            px, py, pz = ship_x - enemy.x, ship_y - enemy.y, ship_z - enemy.z
            
            # projection of ship onto laser direction
            proj = px*dx + py*dy + pz*dz
            
            if 0 < proj < enemy.laser_distance:  # within laser beam range
                # perpendicular distance from line
                cross_x = py*dz - pz*dy
                cross_y = pz*dx - px*dz
                cross_z = px*dy - py*dx
                dist = math.sqrt(cross_x**2 + cross_y**2 + cross_z**2)
                
                if dist < 30:  # tighter hitbox
                    if not powerup_effects["shield"]:
                        if not hasattr(enemy, "last_damage_time") or time.time() - enemy.last_damage_time > 0.5:
                            player_health -= 0.1
                            enemy.last_damage_time = time.time()


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
    global move_1, move_2, vert, ship_angle, ship_roll  
    glPushMatrix()
    glColor3f(0.33, 0.45, 0.19)
    glTranslatef(-move_1, move_2, 100+vert)
    

    glRotatef(ship_roll, 0, 1, 0)  # Roll around y axis
    glRotatef(90+ship_angle, 0, 0, 1)  # Yaw rotation
    
    glRotatef(-90, 0, 0, 1)
    glScalef(1,3/2,1)
    glutSolidCube(100)
    glScalef(1,2/3,1)
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
    glTranslatef(20, 120, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 5, 60, 10, 10)
    glTranslatef(-40, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 5, 60, 10, 10)
    glColor3f(0.1, 0.2, 0.3)
    glRotatef(-90, 1, 0, 0)
    glTranslatef(-20, -120, 0)
    glTranslatef(40, -40, 0)
    glRotatef(90, 1, 0, 0)
    glTranslate(0,40,0)
    gluCylinder(gluNewQuadric(), 40, 5, 200, 10, 10)
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
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glutSolidSphere(8, 10, 10)  
        glPopMatrix()
        
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
    global game_state, vert, angle, move_1, move_2, ship_angle, ship_roll, powerup_effects
    
    # Handle game state transitions
    if key == b' ':
        if game_state == PLAYING:
            game_state = START_SCREEN
        elif game_state == START_SCREEN:
            game_state = PLAYING
        return
    
    if key == b'r' or key == b'R':
        reset_game()
        return
    
    if key == b'\x1b':  # ESC key
        glutLeaveMainLoop()
        return
    
    # Only process movement keys if in PLAYING state
    if game_state != PLAYING:
        return
    
    sp = 3 * powerup_effects["speed"]
    
    if key == b'w' or key == b'W':
        rad = math.radians(ship_angle)
        if first_person_mode:
            move_1 -= math.sin(rad) * sp 
            move_2 -= math.cos(rad) * sp 
        else:
            move_1 -= math.sin(rad) * sp
            move_2 -= math.cos(rad) * sp
      
    if key == b's' or key == b'S':
        rad = math.radians(ship_angle)
        if first_person_mode:
            move_1 += math.sin(rad) * sp  
            move_2 += math.cos(rad) * sp  
        else:
            move_1 += math.sin(rad) * sp
            move_2 += math.cos(rad) * sp
    
    if key == b'a' or key == b'A':
        if first_person_mode:
            rad = math.radians(ship_angle)
            move_1 -= math.cos(rad) * sp 
            move_2 += math.sin(rad) * sp 
        else:
            ship_angle += 15  
            if ship_angle < 0:
                ship_angle += 360
    
    if key == b'd' or key == b'D':
        if first_person_mode:
            rad = math.radians(ship_angle)
            move_1 += math.cos(rad) * sp 
            move_2 -= math.sin(rad) * sp 
        else:
            ship_angle -= 15  
            if ship_angle > 360:
                ship_angle -= 360
    
    # Add roll controls
    if key == b'j' or key == b'J':  # Roll left
        ship_roll += 15
        if ship_roll > 360:
            ship_roll -= 360
    
    if key == b'l' or key == b'L':  # Roll right
        ship_roll -= 15
        if ship_roll < 0:
            ship_roll += 360
    
    if key == b'c' or key == b'C':
        toggle_camera_mode()
    
    if key == b'p' or key == b'P':
        powerup_effects["speed"] = 10
    if key == b'o' or key == b'o':
        powerup_effects["speed"] = 1

def specialKeyListener(key, x, y):
    global camera_pos, move_1, move_2, angle, vert
    
    # Only process special keys if in PLAYING state
    if game_state != PLAYING:
        return
    
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
    
    x, y, z = camera_pos
    camera_pos = (x, y, z)

def mouseListener(button, state, x, y):
    global bullets, move_1, move_2, vert, ship_angle

    if game_state != PLAYING:
        return
    
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
        player_angle_rad = math.radians(ship_angle)  
        
        camera_x = ship_x
        camera_y = ship_y
        camera_z = ship_z + 30  
        
        look_x = ship_x - math.sin(player_angle_rad) * 100
        look_y = ship_y - math.cos(player_angle_rad) * 100
        look_z = ship_z
        
        gluLookAt(camera_x, camera_y, camera_z,  
                  look_x, look_y, look_z,        
                  0, 0, 1)                    
    else:
        # Third-person view (original)
        player_angle_rad = math.radians(angle)
        
        camera_distance = 300
        camera_height = 150
        camera_x = ship_x + math.sin(player_angle_rad) * camera_distance
        camera_y = ship_y + math.cos(player_angle_rad) * camera_distance
        camera_z = ship_z + camera_height
        
        gluLookAt(camera_x, camera_y, camera_z,  
                  ship_x, ship_y, ship_z,       
                  0, 0, 1) 

def idle():
    if game_state == PLAYING:
        check_powerup_collision()
        update_powerups()               # keep powerup timer update
        spawn_initial_enemies()
        update_enemies()
        cleanup_far_enemies()
        cleanup_old_bullets()
        check_bullet_enemy_collision()
        check_enemy_laser_hits()        # <-- make sure this runs!
    
    glutPostRedisplay()


def showScreen():
    global game_state
    
    if game_state == START_SCREEN:
        draw_start_screen()
        return
    
    if game_state == GAME_OVER:
        draw_game_over_screen()
        return
    
    # PLAYING state
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 1000)
    setupCamera()
    
    # Check for game over condition
    if player_health <= 0:
        game_state = GAME_OVER
        draw_game_over_screen()
        return
    
    # Draw 3D scene
    draw_stars()
    draw_arena()
    draw_powerups()
    if not first_person_mode:  
        draw_shapes()
    draw_bullets()
    draw_enemies()
    
    draw_cockpit()
    
    # Save current matrices and set up for 2D text rendering
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 1000)  # Set up 2D orthographic projection
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth testing for text
    glDisable(GL_DEPTH_TEST)
    
    # Draw HUD with game info
    draw_text(20, 80, f"Health: {player_health:.1f}")  # Show health with 1 decimal
    draw_text(20, 110, f"Score: {score}")
    draw_text(20, 140, f"PowerUp Mode: {'OFF' if powerup_effects['speed']==1 else 'ON'}")
    draw_text(20, 170, f"View: {'1st Person' if first_person_mode else '3rd Person'}")
    draw_text(20, 200, f"Roll: {ship_roll}°")
    
    # Restore settings
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def main():
    global powerups
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
    
    # Initialize powerups
    for _ in range(8):
        t = random.choice(["speed", "firerate", "shield"])
        x = random.randint(-arena_size//2, arena_size//2)
        y = random.randint(-arena_size//2, arena_size//2)
        z = random.randint(50, 200)
        powerups.append((x, y, z, t))
    
    print("Game started! Press SPACE to begin.")
    
    glutMainLoop()

if __name__=="__main__":
    main()