import pygame
import sys

# ---------- Settings ----------
WIDTH, HEIGHT = 800, 600
FPS = 60

PLAYER_WIDTH, PLAYER_HEIGHT = 40, 40
PLAYER_SPEED = 5
JUMP_POWER = 14
GRAVITY = 0.8
MAX_FALL_SPEED = 20
DASH_DISTANCE = 100  # pixels

# Colors
BG = (135, 206, 235)
PLATFORM_COLOR = (100, 100, 100)
PLAYER_COLOR = (50, 150, 255)
FLAG_COLOR = (30, 180, 30)
DASH_PICKUP_COLOR = (255, 200, 0)
TEXT_COLOR = (20, 20, 20)

# ---------- Initialize ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vania")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# ---------- Player ----------
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.x_vel = 0
        self.y_vel = 0
        self.on_ground = False
        self.can_dash = False
        self.dash_used = False

    def handle_input(self, keys):
        self.x_vel = 0
        if keys[pygame.K_a]:
            self.x_vel = -PLAYER_SPEED
        if keys[pygame.K_d]:
            self.x_vel = PLAYER_SPEED

    def jump(self):
        if self.on_ground:
            self.y_vel = -JUMP_POWER
            self.on_ground = False
            self.dash_used = False

    def dash(self, direction):
        if self.can_dash and not self.dash_used:
            if direction != 0:
                self.rect.x += DASH_DISTANCE * direction
                self.dash_used = True

    def apply_gravity(self):
        self.y_vel += GRAVITY
        if self.y_vel > MAX_FALL_SPEED:
            self.y_vel = MAX_FALL_SPEED

    def move(self, platforms):
        self.rect.x += int(self.x_vel)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.x_vel > 0:
                    self.rect.right = p.rect.left
                elif self.x_vel < 0:
                    self.rect.left = p.rect.right
        self.rect.y += int(self.y_vel)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.y_vel > 0:
                    self.rect.bottom = p.rect.top
                    self.y_vel = 0
                    self.on_ground = True
                elif self.y_vel < 0:
                    self.rect.top = p.rect.bottom
                    self.y_vel = 0

    def update(self, platforms):
        self.apply_gravity()
        self.move(platforms)

    def draw(self, surf, scroll_x):
        pygame.draw.rect(surf, PLAYER_COLOR, (self.rect.x - scroll_x, self.rect.y, self.rect.width, self.rect.height))

# ---------- Platform / Flag / DashPickup ----------
class Platform:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, surf, scroll_x):
        pygame.draw.rect(surf, PLATFORM_COLOR, (self.rect.x - scroll_x, self.rect.y, self.rect.width, self.rect.height))

class Flag:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, surf, scroll_x):
        pygame.draw.rect(surf, FLAG_COLOR, (self.rect.x - scroll_x, self.rect.y, self.rect.width, self.rect.height))

class DashPickup:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.collected = False

    def draw(self, surf, scroll_x):
        if not self.collected:
            pygame.draw.rect(surf, DASH_PICKUP_COLOR, (self.rect.x - scroll_x, self.rect.y, self.rect.width, self.rect.height))

# ---------- Levels ----------
levels = [
    # Level 1
    {
        "platforms": [
            Platform((0, 580, 1600, 20)),
            Platform((200, 520, 150, 20)),
            Platform((450, 450, 150, 20)),
            Platform((700, 380, 150, 20)),
            Platform((950, 310, 150, 20)),
            Platform((1200, 240, 150, 20)),
            Platform((1400, 180, 150, 20)),
        ],
        "flag": Flag((1550, 130, 30, 50)),
        "dash_pickup": None,
        "player_start": (50, 540),
        "width": 1600
    },
    # Level 2: Dash tutorial with left slope rising to left
    {
        "platforms": [
            # Floor
            Platform((0, 580, 5000, 20)),

            # Left slope rising to left
            Platform((650, 480, 100, 20)),  # lowest on right
            Platform((500, 400, 100, 20)),
            Platform((350, 330, 100, 20)),
            Platform((200, 250, 100, 20)),  # highest left, dash pickup

            # Right side dash-required jumps
            Platform((1000, 400, 100, 20)),
            Platform((1300, 350, 100, 20)),
            Platform((1600, 300, 100, 20)),
            Platform((1900, 250, 100, 20)),
            Platform((2200, 200, 100, 20)),
        ],
        "flag": Flag((2200, 150, 30, 50)),
        "dash_pickup": DashPickup((215, 170, 30, 20)),  # highest left platform
        "player_start": (500, 540),
        "width": 2300
    }
]

current_level = 0
scroll_x = 0
player = Player(*levels[current_level]["player_start"])

# Jump buffering
jump_buffer_time = 150
last_jump_press = 0
prev_w_state = False  # track W key for jump edge detection

def reset_level():
    global player, scroll_x, last_jump_press, prev_w_state
    data = levels[current_level]
    player.rect.x, player.rect.y = data["player_start"]
    player.x_vel = 0
    player.y_vel = 0
    player.on_ground = False
    player.dash_used = False
    scroll_x = 0
    last_jump_press = 0
    prev_w_state = False
    if data["dash_pickup"]:
        data["dash_pickup"].collected = False
        player.can_dash = False

def handle_input(keys):
    global last_jump_press, prev_w_state
    player.handle_input(keys)

    # Jump only when W is pressed, not held
    if keys[pygame.K_w] and not prev_w_state:
        last_jump_press = pygame.time.get_ticks()
    prev_w_state = keys[pygame.K_w]

    # Dash
    if keys[pygame.K_j]:
        direction = 0
        if keys[pygame.K_a]:
            direction = -1
        elif keys[pygame.K_d]:
            direction = 1
        player.dash(direction)

def update():
    global scroll_x, current_level, last_jump_press
    player.update(levels[current_level]["platforms"])
    
    # Jump buffering
    if player.on_ground:
        now = pygame.time.get_ticks()
        if now - last_jump_press <= jump_buffer_time:
            player.jump()
            last_jump_press = 0

    # Scroll camera to follow player
    scroll_x = player.rect.centerx - WIDTH // 2
    level_width = levels[current_level]["width"]
    scroll_x = max(0, min(scroll_x, level_width - WIDTH))

    # Dash pickup
    pickup = levels[current_level]["dash_pickup"]
    if pickup and not pickup.collected and player.rect.colliderect(pickup.rect):
        pickup.collected = True
        player.can_dash = True

    # Level complete
    if player.rect.colliderect(levels[current_level]["flag"].rect):
        current_level += 1
        if current_level >= len(levels):
            print("You won the game!")
            pygame.quit()
            sys.exit()
        else:
            reset_level()

def draw():
    screen.fill(BG)
    for plat in levels[current_level]["platforms"]:
        plat.draw(screen, scroll_x)
    levels[current_level]["flag"].draw(screen, scroll_x)
    if levels[current_level]["dash_pickup"]:
        levels[current_level]["dash_pickup"].draw(screen, scroll_x)
    player.draw(screen, scroll_x)
    text = "Dash unlocked! press J" if player.can_dash else "-"
    hud = font.render(text, True, TEXT_COLOR)
    screen.blit(hud, (10, 10))
    pygame.display.flip()

# ---------- Main Loop ----------
while True:
    dt = clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    keys = pygame.key.get_pressed()
    handle_input(keys)
    update()
    draw()
