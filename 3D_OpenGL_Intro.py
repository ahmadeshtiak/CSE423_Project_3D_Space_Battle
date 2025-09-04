from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time

# -----------------------------
# 3D Space Battle Arena - Full Game
# Single-file OpenGL (PyOpenGL + freeglut) script
# Features implemented:
#  - Player spaceship (simple primitives)
#  - Full 6-DOF movement (forward/back, strafing, vertical)
#  - Ship rotation (pitch, yaw, roll)
#  - Laser bullets fired by left-click / Space
#  - AI enemy drones with two behaviors (wander / seek)
#  - Cheat mode: spawn allies equal to enemies which auto-fire and teleport to face enemies
#  - Power-ups: speed, firerate, shield
#  - Multiple camera modes: third-person, first-person, free
#  - Skybox-like starfield
#  - Collision detection, scoring, game states (start, playing, game over, victory)
#  - All gameplay tuned to be slower/paced as requested
# -----------------------------

# Window
WINDOW_W, WINDOW_H = 1000, 800

# Game states
STATE_START = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
STATE_VICTORY = 3

game_state = STATE_START

# Camera modes
CAMERA_THIRD = 0
CAMERA_FIRST = 1
CAMERA_FREE = 2
camera_mode = CAMERA_THIRD

# Arena
ARENA_HALF = 500
MIN_Z = 10
MAX_Z = 400

# Player ship
player_pos = [0.0, 0.0, 50.0]
player_rot = [0.0, 0.0, 0.0]  # yaw, pitch, roll
PLAYER_SIZE = 20.0
PLAYER_BASE_SPEED = 3.0   # slowed movement
player_speed = PLAYER_BASE_SPEED
player_health = 100

# Bullets
bullets = []  # {'pos':[x,y,z],'dir':[dx,dy,dz],'born':t,'owner': 'player'/'enemy'/'ally'}
BULLET_SPEED = 12.0  # slowed bullet speed
BULLET_SIZE = 3.0
BULLET_LIFETIME = 4.0
PLAYER_FIRE_COOLDOWN = 0.4
player_last_fire = 0.0

# Enemies
enemies = []  # {'pos':[x,y,z], 'type':'wander'/'seek', 'size', 'last_shot', 'health'}
ENEMY_COUNT = 5
ENEMY_SIZE = 28.0
ENEMY_SPEED = 1.2  # slow enemies

# Allies (for cheat mode)
allies = []  # {'pos':[x,y,z], 'rot':[yaw,pitch,roll], 'last_shot'}
ALLY_FIRE_COOLDOWN = 0.4

# Power-ups
powerups = []  # {'pos':[x,y,z], 'type':'speed'/'firerate'/'shield', 'spawn':t}
POWERUP_TYPES = ['speed', 'firerate', 'shield']
POWERUP_SPAWN_INTERVAL = 16.0
last_powerup_spawn = 0.0
active_powerups = {'speed':0.0, 'firerate':0.0, 'shield':0.0}
POWERUP_DURATION = 9.0

# Stars
stars = []
NUM_STARS = 300
STAR_SEED = 42

# Score & victory
score = 0
SCORE_TO_WIN = 200

# Cheats
cheat_mode = False
auto_fire = False
cheat_vision = False

# Timing
last_time = time.time()

# Utility functions

def clamp(v, a, b):
    return max(a, min(b, v))


def rand_between(a, b):
    return random.uniform(a, b)

# Drawing helpers

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
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


def draw_spaceship_at(pos, rot, scale=1.0, color=(0.5,0.6,0.95)):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rot[0], 0, 0, 1)  # yaw around Z
    glRotatef(rot[1], 0, 1, 0)  # pitch about Y
    glRotatef(rot[2], 1, 0, 0)  # roll about X

    # Cockpit sphere (main body)
    glColor3f(*color)
    quad = gluNewQuadric()
    gluSphere(quad, 8*scale, 12, 12)

    # Body cone (nose)
    glColor3f(min(color[0]*1.2,1.0), min(color[1]*1.2,1.0), min(color[2]*1.2,1.0))
    glPushMatrix()
    glTranslatef(0, 0, 14*scale)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 8*scale, 0, 28*scale, 10, 6)
    glPopMatrix()

    # Wings (left and right)
    glColor3f(0.25,0.25,0.25)
    glPushMatrix()
    glTranslatef(0, 12*scale, 0)
    glScalef(2.4*scale, 6*scale, 0.8*scale)
    glutSolidCube(3)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, -12*scale, 0)
    glScalef(2.4*scale, 6*scale, 0.8*scale)
    glutSolidCube(3)
    glPopMatrix()

    # Engine details (small cubes at the back)
    glColor3f(0.8, 0.4, 0.2)
    glPushMatrix()
    glTranslatef(0, 0, -8*scale)
    glScalef(1.5*scale, 1.5*scale, 3*scale)
    glutSolidCube(2)
    glPopMatrix()

    glPopMatrix()


def draw_player():
    draw_spaceship_at(player_pos, player_rot, scale=1.0, color=(0.6,0.6,1.0))


def draw_enemies():
    for e in enemies:
        glPushMatrix()
        glTranslatef(e['pos'][0], e['pos'][1], e['pos'][2])
        
        # Rotate enemies for visual effect
        glRotatef(time.time() * 30, 0, 0, 1)
        
        if cheat_vision:
            glColor3f(1,0,0)  # Red when cheat vision is on
        else:
            # Different colors for different enemy types
            if e['type']=='seek':
                glColor3f(0.9,0.3,0.3)  # Red for seeking enemies
            else:
                glColor3f(0.2,0.9,0.3)  # Green for wandering enemies
        
        # Draw enemy as a cube with some detail
        glutSolidCube(e['size'])
        
        # Add a small indicator on top
        glColor3f(1.0, 1.0, 0.0)
        glTranslatef(0, 0, e['size']/2 + 5)
        glutSolidCube(3)
        
        glPopMatrix()


def draw_allies():
    for a in allies:
        draw_spaceship_at(a['pos'], a['rot'], scale=0.8, color=(0.4,0.8,0.7))


def draw_bullets():
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['pos'][0], b['pos'][1], b['pos'][2])
        # Different colors for different bullet owners
        if b['owner'] == 'player':
            glColor3f(0.2, 0.8, 1.0)  # Blue laser for player
        elif b['owner'] == 'ally':
            glColor3f(0.2, 1.0, 0.2)  # Green laser for allies
        else:  # enemy
            glColor3f(1.0, 0.2, 0.2)  # Red laser for enemies
        
        # Draw laser as a small glowing sphere
        quad = gluNewQuadric()
        gluSphere(quad, BULLET_SIZE, 8, 8)
        
        # Add a small trail effect
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(quad, BULLET_SIZE*0.5, 6, 6)
        glPopMatrix()


def draw_powerups():
    for p in powerups:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        
        # Rotate power-ups for visual effect
        glRotatef(time.time() * 50, 0, 1, 0)
        
        if p['type']=='speed':
            glColor3f(0.9,0.7,0.2)  # Orange for speed
        elif p['type']=='firerate':
            glColor3f(0.8,0.2,0.9)  # Purple for firerate
        else:  # shield
            glColor3f(0.2,0.6,0.9)  # Blue for shield
        
        # Draw main power-up sphere
        quad = gluNewQuadric()
        gluSphere(quad, 7, 8, 8)
        
        # Add glowing effect
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(quad, 4, 6, 6)
        
        glPopMatrix()


def draw_stars():
    glPointSize(1.5)
    glBegin(GL_POINTS)
    for s in stars:
        # Vary star brightness and color slightly
        brightness = random.uniform(0.6, 1.0)
        glColor3f(brightness, brightness, brightness)
        glVertex3f(s[0], s[1], s[2])
    glEnd()
    
    # Add some brighter stars
    glPointSize(3.0)
    glBegin(GL_POINTS)
    glColor3f(1.0, 1.0, 0.8)
    for i in range(0, len(stars), 10):  # Every 10th star is brighter
        s = stars[i]
        glVertex3f(s[0], s[1], s[2])
    glEnd()


def draw_arena():
    # floor with grid pattern
    glBegin(GL_QUADS)
    glColor3f(0.05,0.05,0.08)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, ARENA_HALF, 0)
    glVertex3f(-ARENA_HALF, ARENA_HALF, 0)
    glEnd()
    
    # Draw grid lines on floor
    glColor3f(0.1, 0.1, 0.15)
    glBegin(GL_LINES)
    for i in range(-ARENA_HALF, ARENA_HALF+1, 100):
        glVertex3f(i, -ARENA_HALF, 0)
        glVertex3f(i, ARENA_HALF, 0)
        glVertex3f(-ARENA_HALF, i, 0)
        glVertex3f(ARENA_HALF, i, 0)
    glEnd()
    
    # walls with subtle color variation
    glColor3f(0.12,0.12,0.12)
    glBegin(GL_QUADS)
    # front wall
    glVertex3f(-ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, -ARENA_HALF, ARENA_HALF)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, ARENA_HALF)
    # back wall
    glVertex3f(-ARENA_HALF, ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, ARENA_HALF, ARENA_HALF)
    glVertex3f(-ARENA_HALF, ARENA_HALF, ARENA_HALF)
    # left wall
    glVertex3f(-ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(-ARENA_HALF, ARENA_HALF, 0)
    glVertex3f(-ARENA_HALF, ARENA_HALF, ARENA_HALF)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, ARENA_HALF)
    # right wall
    glVertex3f(ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, ARENA_HALF, ARENA_HALF)
    glVertex3f(ARENA_HALF, -ARENA_HALF, ARENA_HALF)
    glEnd()

# Spawning

def spawn_enemies():
    global enemies
    enemies = []
    for _ in range(ENEMY_COUNT):
        x = rand_between(-ARENA_HALF+ENEMY_SIZE, ARENA_HALF-ENEMY_SIZE)
        y = rand_between(-ARENA_HALF+ENEMY_SIZE, ARENA_HALF-ENEMY_SIZE)
        z = rand_between(40, 260)
        t = random.choice(['wander','seek'])
        enemies.append({'pos':[x,y,z], 'type':t, 'size':ENEMY_SIZE, 'last_shot':time.time(), 'health':30})
    if cheat_mode:
        create_allies()


def create_allies():
    global allies
    allies = []
    for e in enemies:
        ex,ey,ez = e['pos']
        # Position ally at same level (z-coordinate) as enemy drone
        ang = rand_between(0, math.tau)
        offset = 100  # Distance from enemy
        ax = ex + math.cos(ang)*offset
        ay = ey + math.sin(ang)*offset
        az = ez  # Same level as enemy drone
        dx,dy,dz = ex-ax, ey-ay, ez-az
        L = math.sqrt(dx*dx+dy*dy+dz*dz)+1e-6
        dirv = [dx/L, dy/L, dz/L]
        yaw = math.degrees(math.atan2(dirv[1], dirv[0]))
        pitch = math.degrees(math.asin(clamp(dirv[2], -1.0, 1.0)))
        allies.append({'pos':[ax,ay,az], 'rot':[yaw,pitch,0.0], 'last_shot':0.0, 'target_enemy':e})


def spawn_powerup():
    t = random.choice(POWERUP_TYPES)
    x = rand_between(-ARENA_HALF+20, ARENA_HALF-20)
    y = rand_between(-ARENA_HALF+20, ARENA_HALF-20)
    z = rand_between(30, 180)
    powerups.append({'pos':[x,y,z], 'type':t, 'spawn':time.time()})

# Firing

def fire_bullet(owner='player', start_pos=None, direction=None):
    global bullets, player_last_fire
    now = time.time()
    if owner=='player':
        cooldown = PLAYER_FIRE_COOLDOWN
        if active_powerups['firerate'] > now:
            cooldown = max(0.06, cooldown*0.45)
        if now - player_last_fire < cooldown:
            return
        player_last_fire = now
        # default direction from player rot
        if start_pos is None:
            yaw = math.radians(player_rot[0])
            pitch = math.radians(player_rot[1])
            dx = math.cos(yaw)*math.cos(pitch)
            dy = math.sin(yaw)*math.cos(pitch)
            dz = math.sin(pitch)
            start_pos = [player_pos[0]+dx*30, player_pos[1]+dy*30, player_pos[2]+dz*30]
            direction = [dx,dy,dz]
    bullets.append({'pos':[start_pos[0],start_pos[1],start_pos[2]], 'dir':[direction[0],direction[1],direction[2]], 'born':time.time(), 'owner':owner})

# Updates

def update_bullets(dt):
    global bullets, enemies, score
    now = time.time()
    new_b = []
    for b in bullets:
        b['pos'][0] += b['dir'][0] * BULLET_SPEED * dt
        b['pos'][1] += b['dir'][1] * BULLET_SPEED * dt
        b['pos'][2] += b['dir'][2] * BULLET_SPEED * dt
        # lifetime
        if now - b['born'] > BULLET_LIFETIME:
            continue
        # bounds
        x,y,z = b['pos']
        if not (-ARENA_HALF*1.5 <= x <= ARENA_HALF*1.5 and -ARENA_HALF*1.5 <= y <= ARENA_HALF*1.5 and MIN_Z <= z <= MAX_Z*1.5):
            continue
        hit = False
        if b['owner'] in ('player','ally'):
            for e in enemies[:]:
                ex,ey,ez = e['pos']
                dist = math.sqrt((x-ex)**2+(y-ey)**2+(z-ez)**2)
                if dist < (BULLET_SIZE + e['size']/2):
                    e['health'] -= 10
                    if e['health'] <= 0:
                        try:
                            enemies.remove(e)
                        except ValueError:
                            pass
                        score += 10
                    hit = True
                    break
        elif b['owner']=='enemy':
            dx = x - player_pos[0]
            dy = y - player_pos[1]
            dz = z - player_pos[2]
            if math.sqrt(dx*dx+dy*dy+dz*dz) < (BULLET_SIZE + PLAYER_SIZE/2):
                # player hit
                if active_powerups['shield'] < now:
                    global player_health
                    player_health -= 10
                    if player_health <= 0:
                        set_game_over()
                hit = True
        if not hit:
            new_b.append(b)
    bullets = new_b


def update_enemies(dt):
    global enemies, bullets
    now = time.time()
    for e in enemies:
        ex,ey,ez = e['pos']
        if e['type']=='wander':
            ex += rand_between(-0.8,0.8) * dt * 60
            ey += rand_between(-0.8,0.8) * dt * 60
            ez += rand_between(-0.3,0.3) * dt * 60
        else: # seek
            dx = player_pos[0]-ex
            dy = player_pos[1]-ey
            dz = player_pos[2]-ez
            L = math.sqrt(dx*dx+dy*dy+dz*dz)+1e-6
            ex += (dx/L) * ENEMY_SPEED * dt * 60
            ey += (dy/L) * ENEMY_SPEED * dt * 60
            ez += (dz/L) * ENEMY_SPEED * dt * 60 * rand_between(0.6,1.1)
        e['pos'][0] = clamp(ex, -ARENA_HALF+e['size']/2, ARENA_HALF-e['size']/2)
        e['pos'][1] = clamp(ey, -ARENA_HALF+e['size']/2, ARENA_HALF-e['size']/2)
        e['pos'][2] = clamp(ez, 40, 320)
        # enemy shooting
        if now - e['last_shot'] > rand_between(1.6,3.2):
            dx = player_pos[0]-e['pos'][0]
            dy = player_pos[1]-e['pos'][1]
            dz = player_pos[2]-e['pos'][2]
            L = math.sqrt(dx*dx+dy*dy+dz*dz)+1e-6
            dirv = [(dx/L)+rand_between(-0.03,0.03), (dy/L)+rand_between(-0.03,0.03), (dz/L)+rand_between(-0.01,0.01)]
            fire_bullet(owner='enemy', start_pos=[e['pos'][0],e['pos'][1],e['pos'][2]], direction=dirv)
            e['last_shot']=now
    # respawn wave if none
    if len(enemies)==0:
        spawn_enemies()
        if cheat_mode:
            create_allies()


def update_allies(dt):
    global allies
    if not cheat_mode:
        return
    now = time.time()
    if len(allies)!=len(enemies):
        create_allies()
    for i, a in enumerate(allies):
        if i>=len(enemies):
            continue
        e = enemies[i]
        ex,ey,ez = e['pos']
        # Teleport ally to face enemy at same level
        dx = ex - a['pos'][0]
        dy = ey - a['pos'][1]
        dz = ez - a['pos'][2]
        L = math.sqrt(dx*dx+dy*dy+dz*dz)+1e-6
        dirv = [dx/L, dy/L, dz/L]
        offset = 100  # Maintain distance from enemy
        # Position ally at same level as enemy drone
        a['pos'][0] = ex - dirv[0]*offset
        a['pos'][1] = ey - dirv[1]*offset
        a['pos'][2] = ez  # Same level as enemy
        # Orient ally to face enemy
        yaw = math.degrees(math.atan2(dirv[1], dirv[0]))
        pitch = math.degrees(math.asin(clamp(dirv[2], -1.0,1.0)))
        a['rot'][0]=yaw; a['rot'][1]=pitch
        # Auto-fire at enemy
        if now - a['last_shot'] > ALLY_FIRE_COOLDOWN:
            start=[a['pos'][0]+dirv[0]*25, a['pos'][1]+dirv[1]*25, a['pos'][2]+dirv[2]*25]
            fire_bullet(owner='ally', start_pos=start, direction=dirv)
            a['last_shot']=now

# Note: small constant for ally cooldown name used above
ALLY_FIRE_COOLDOWN = 0.35


def check_powerups():
    global powerups, active_powerups
    now = time.time()
    for p in powerups[:]:
        dx = player_pos[0]-p['pos'][0]
        dy = player_pos[1]-p['pos'][1]
        dz = player_pos[2]-p['pos'][2]
        d = math.sqrt(dx*dx+dy*dy+dz*dz)
        if d < PLAYER_SIZE + 10:
            if p['type']=='speed':
                active_powerups['speed'] = now + POWERUP_DURATION
            elif p['type']=='firerate':
                active_powerups['firerate'] = now + POWERUP_DURATION
            else:
                active_powerups['shield'] = now + POWERUP_DURATION
            try:
                powerups.remove(p)
            except ValueError:
                pass


def set_game_over():
    global game_state
    game_state = STATE_GAMEOVER

# Camera

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_W/WINDOW_H, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode==CAMERA_THIRD:
        yaw = math.radians(player_rot[0])
        pitch = math.radians(player_rot[1])
        cam_x = player_pos[0] - math.cos(yaw)*math.cos(pitch)*150
        cam_y = player_pos[1] - math.sin(yaw)*math.cos(pitch)*150
        cam_z = player_pos[2] - math.sin(pitch)*150 + 80
        gluLookAt(cam_x, cam_y, cam_z, player_pos[0], player_pos[1], player_pos[2], 0,0,1)
    elif camera_mode==CAMERA_FIRST:
        yaw = math.radians(player_rot[0]); pitch = math.radians(player_rot[1])
        look_x = player_pos[0] + math.cos(yaw)*math.cos(pitch)*200
        look_y = player_pos[1] + math.sin(yaw)*math.cos(pitch)*200
        look_z = player_pos[2] + math.sin(pitch)*200
        gluLookAt(player_pos[0], player_pos[1], player_pos[2], look_x, look_y, look_z, 0,0,1)
    else:
        gluLookAt(200,200,200, 0,0,0, 0,0,1)

# Main update loop

def idle_func():
    global last_time, last_powerup_spawn, player_speed, player_health, score, game_state
    now = time.time()
    dt = now - last_time
    if dt <= 0:
        return
    last_time = now
    if game_state==STATE_PLAYING:
        # adjust player speed based on powerup
        player_speed = PLAYER_BASE_SPEED * (1.8 if active_powerups['speed']>now else 1.0)
        update_bullets(dt)
        update_enemies(dt)
        update_allies(dt)
        check_powerups()
        # spawn powerups periodically
        if now - last_powerup_spawn > POWERUP_SPAWN_INTERVAL:
            spawn_powerup()
            last_powerup_spawn = now
        # check victory
        if score >= SCORE_TO_WIN:
            game_state = STATE_VICTORY
        # health check
        if player_health <= 0:
            game_state = STATE_GAMEOVER
    glutPostRedisplay()

# Input handlers

def keyboard(key, x, y):
    global player_pos, player_rot, camera_mode, cheat_mode, auto_fire, cheat_vision, game_state, player_last_fire
    if game_state==STATE_START and key in (b' ', b'\r', b'\n'):
        start_game()
        return
    if game_state in (STATE_GAMEOVER, STATE_VICTORY) and key==b'r':
        start_game()
        return
    # Movement keys (instant apply, dt not used for simplicity)
    if key in (b'w', b'W'):
        yaw = math.radians(player_rot[0]); pitch = math.radians(player_rot[1])
        player_pos[0] += math.cos(yaw)*math.cos(pitch)*player_speed
        player_pos[1] += math.sin(yaw)*math.cos(pitch)*player_speed
        player_pos[2] += math.sin(pitch)*player_speed
    if key in (b's', b'S'):
        yaw = math.radians(player_rot[0]); pitch = math.radians(player_rot[1])
        player_pos[0] -= math.cos(yaw)*math.cos(pitch)*player_speed
        player_pos[1] -= math.sin(yaw)*math.cos(pitch)*player_speed
        player_pos[2] -= math.sin(pitch)*player_speed
    if key in (b'a', b'A'):
        rad = math.radians(player_rot[0]+90)
        player_pos[0] -= math.cos(rad)*player_speed
        player_pos[1] -= math.sin(rad)*player_speed
    if key in (b'd', b'D'):
        rad = math.radians(player_rot[0]+90)
        player_pos[0] += math.cos(rad)*player_speed
        player_pos[1] += math.sin(rad)*player_speed
    if key in (b'q', b'Q'):
        player_pos[2] += player_speed
    if key in (b'e', b'E'):
        player_pos[2] -= player_speed
    if key==b'x':
        toggle_cheat()
    if key==b'v':
        global cheat_vision
        cheat_vision = not cheat_vision
    if key==b' ':
        # fire
        fire_bullet('player')
    if key==b'r':
        start_game()
    # clamp
    player_pos[0]=clamp(player_pos[0], -ARENA_HALF+PLAYER_SIZE/2, ARENA_HALF-PLAYER_SIZE/2)
    player_pos[1]=clamp(player_pos[1], -ARENA_HALF+PLAYER_SIZE/2, ARENA_HALF-PLAYER_SIZE/2)
    player_pos[2]=clamp(player_pos[2], MIN_Z, MAX_Z)


def special_keys(key, x, y):
    if key==GLUT_KEY_LEFT:
        player_rot[0] += 6
    if key==GLUT_KEY_RIGHT:
        player_rot[0] -= 6
    if key==GLUT_KEY_UP:
        player_rot[1] += 6
    if key==GLUT_KEY_DOWN:
        player_rot[1] -= 6


def mouse(button, state, x, y):
    global camera_mode
    if game_state!=STATE_PLAYING:
        return
    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        fire_bullet('player')
    if button==GLUT_RIGHT_BUTTON and state==GLUT_DOWN:
        camera_mode = (camera_mode+1)%3

# Game control helpers

def toggle_cheat():
    global cheat_mode, auto_fire
    cheat_mode = not cheat_mode
    auto_fire = cheat_mode
    if cheat_mode:
        create_allies()
    else:
        allies.clear()


def start_game():
    global game_state, score, player_health, bullets, enemies, allies, powerups, stars, last_powerup_spawn, last_time
    game_state = STATE_PLAYING
    score = 0
    player_health = 100
    bullets = []
    powerups = []
    enemies = []
    allies = []
    # player reset
    player_pos[0], player_pos[1], player_pos[2] = 0.0, 0.0, 50.0
    player_rot[0], player_rot[1], player_rot[2] = 0.0, 0.0, 0.0
    # stars
    random.seed(STAR_SEED)
    stars.clear()
    for _ in range(NUM_STARS):
        stars.append([rand_between(-ARENA_HALF*3,ARENA_HALF*3), rand_between(-ARENA_HALF*3,ARENA_HALF*3), rand_between(0,ARENA_HALF*3)])
    spawn_enemies()
    last_powerup_spawn = time.time()
    last_time = time.time()

# Setup & main

def init_gl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_POINT_SMOOTH)
    glPointSize(2.0)
    glClearColor(0.0,0.0,0.0,1.0)


def display():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glViewport(0,0, WINDOW_W, WINDOW_H)
    setup_camera()
    # draw world
    draw_stars()
    draw_arena()
    if game_state==STATE_PLAYING:
        draw_powerups()
        draw_enemies()
        draw_allies()
        draw_bullets()
        draw_player()
    # HUD & screens
    draw_text(10, WINDOW_H-30, f"Score: {score}")
    draw_text(10, WINDOW_H-60, f"Health: {player_health}")
    draw_text(10, WINDOW_H-90, f"Enemies: {len(enemies)}")
    draw_text(10, WINDOW_H-120, f"Allies: {len(allies)}")
    draw_text(10, WINDOW_H-150, f"Cheat: {'ON' if cheat_mode else 'OFF'}")
    
    # Camera mode indicator
    camera_names = ["3rd Person", "1st Person", "Free Camera"]
    draw_text(WINDOW_W-200, WINDOW_H-30, f"Camera: {camera_names[camera_mode]}")
    
    # Power-up status
    now = time.time()
    yoff=180
    for k,v in active_powerups.items():
        if v>now:
            draw_text(10, WINDOW_H-yoff, f"{k.upper()} ({int(v-now)}s)")
            yoff+=30
    if game_state==STATE_START:
        draw_text(WINDOW_W/2-180, WINDOW_H/2+80, "3D SPACE BATTLE ARENA", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(WINDOW_W/2-200, WINDOW_H/2+40, "Press SPACE to START")
        draw_text(WINDOW_W/2-300, WINDOW_H/2, "MOVEMENT:")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-20, "W/S - Forward/Backward")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-40, "A/D - Strafe Left/Right")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-60, "Q/E - Up/Down")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-80, "Arrow Keys - Rotate Ship")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-100, "Mouse Left - Fire Laser")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-120, "Mouse Right - Change Camera")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-140, "X - Toggle Cheat Mode")
        draw_text(WINDOW_W/2-300, WINDOW_H/2-160, "V - Toggle Cheat Vision")
    if game_state==STATE_GAMEOVER:
        draw_text(WINDOW_W/2-80, WINDOW_H/2, "GAME OVER")
        draw_text(WINDOW_W/2-120, WINDOW_H/2-30, f"Score: {score}")
        draw_text(WINDOW_W/2-120, WINDOW_H/2-60, "Press R to restart")
    if game_state==STATE_VICTORY:
        draw_text(WINDOW_W/2-80, WINDOW_H/2, "VICTORY!")
        draw_text(WINDOW_W/2-140, WINDOW_H/2-30, f"Score: {score} - Press R to play again")
    glutSwapBuffers()

# Spawn helper reused


# Main

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"3D Space Battle Arena")
    init_gl()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutIdleFunc(idle_func)
    # prepare initial stars
    random.seed(STAR_SEED)
    stars.clear()
    for _ in range(NUM_STARS):
        stars.append([rand_between(-ARENA_HALF*3,ARENA_HALF*3), rand_between(-ARENA_HALF*3,ARENA_HALF*3), rand_between(0,ARENA_HALF*3)])
    glutMainLoop()

if __name__=="__main__":
    main()
