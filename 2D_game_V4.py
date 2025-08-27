import pygame
import random
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Metroidvania Platformer")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
PURPLE = (180, 0, 255)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
DARK_BLUE = (50, 50, 80)

# Game variables
clock = pygame.time.Clock()
FPS = 60
gravity = 0.5
scroll_threshold = 200
level_length = 5000

# Helper function for bounding box collision detection
def check_collision(rect1, rect2):
    return (rect1[0] < rect2[0] + rect2[2] and
            rect1[0] + rect1[2] > rect2[0] and
            rect1[1] < rect2[1] + rect2[3] and
            rect1[1] + rect1[3] > rect2[1])

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.jump_power = -12
        self.speed = 5
        self.is_jumping = False
        self.health = 100
        self.max_health = 100
        self.direction = 1  # 1 for right, -1 for left
        self.shoot_cooldown = 0
        self.invincibility = 0
        self.air_control = 0.8  # Control reduction in air
        self.shoot_direction = (1, 0)  # Default shoot direction (right)
        
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)
        
    def move(self, platforms):
        dx = 0
        dy = 0
        
        # Apply gravity
        self.vel_y += gravity
        if self.vel_y > 10:
            self.vel_y = 10
            
        # Process key presses
        keys = pygame.key.get_pressed()
        
        # Horizontal movement with air control factor
        control_factor = 1 if not self.is_jumping else self.air_control
        if keys[pygame.K_LEFT]:
            dx -= self.speed * control_factor
            self.direction = -1
        if keys[pygame.K_RIGHT]:
            dx += self.speed * control_factor
            self.direction = 1
            
        # Vertical movement (up/down) when in air
        if self.is_jumping:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= self.speed * 0.7  # Slightly slower vertical movement
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += self.speed * 0.7
                
        # Jumping
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True
            
        # Update shoot direction based on arrow keys
        self.shoot_direction = (0, 0)
        if keys[pygame.K_UP]:
            self.shoot_direction = (self.shoot_direction[0], -1)
        elif keys[pygame.K_DOWN]:
            self.shoot_direction = (self.shoot_direction[0], 1)
            
        if keys[pygame.K_LEFT]:
            self.shoot_direction = (-1, self.shoot_direction[1])
            self.direction = -1
        elif keys[pygame.K_RIGHT]:
            self.shoot_direction = (1, self.shoot_direction[1])
            self.direction = 1
            
        # If no direction keys are pressed, use the player's facing direction
        if self.shoot_direction == (0, 0):
            self.shoot_direction = (self.direction, 0)
            
        # Update position
        dx += self.vel_x
        dy += self.vel_y
        
        # Check for collisions with platforms
        for platform in platforms:
            platform_rect = (platform.x, platform.y, platform.width, platform.height)
            player_rect = (self.x + dx, self.y, self.width, self.height)
            
            # Check for horizontal collisions
            if check_collision(player_rect, platform_rect):
                if dx > 0:  # Moving right
                    self.x = platform.x - self.width
                    dx = 0
                elif dx < 0:  # Moving left
                    self.x = platform.x + platform.width
                    dx = 0
                    
            player_rect = (self.x, self.y + dy, self.width, self.height)
            
            # Check for vertical collisions
            if check_collision(player_rect, platform_rect):
                if dy > 0:  # Falling
                    self.y = platform.y - self.height
                    self.is_jumping = False
                    dy = 0
                    self.vel_y = 0
                elif dy < 0:  # Jumping
                    self.y = platform.y + platform.height
                    dy = 0
                    self.vel_y = 0
        
        # Update player position
        self.x += dx
        self.y += dy
        
        # Keep player within screen boundaries
        if self.x < 0:
            self.x = 0
        if self.x > level_length - self.width:
            self.x = level_length - self.width
        if self.y < 0:
            self.y = 0
            self.vel_y = 0
        if self.y > HEIGHT - self.height:
            self.y = HEIGHT - self.height
            self.is_jumping = False
            self.vel_y = 0
            
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        # Update invincibility
        if self.invincibility > 0:
            self.invincibility -= 1
    
    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 15
            
            # Calculate bullet position based on shoot direction
            if self.shoot_direction[1] == 0:  # Horizontal shooting
                bullet_x = self.x + (self.width//2) + (self.shoot_direction[0] * 20)
                bullet_y = self.y + self.height//2
            elif self.shoot_direction[0] == 0:  # Vertical shooting
                bullet_x = self.x + self.width//2
                bullet_y = self.y + (self.height//2) + (self.shoot_direction[1] * 20)
            else:  # Diagonal shooting
                bullet_x = self.x + (self.width//2) + (self.shoot_direction[0] * 15)
                bullet_y = self.y + (self.height//2) + (self.shoot_direction[1] * 15)
                
            # Normalize the direction vector for consistent speed
            dx, dy = self.shoot_direction
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx = dx / length * 10
                dy = dy / length * 10
                
            return Bullet(bullet_x, bullet_y, dx, dy)
        return None
    
    def draw(self, screen, scroll):
        # Draw player
        color = BLUE if self.invincibility == 0 else (200, 200, 255)
        pygame.draw.rect(screen, color, (self.x - scroll, self.y, self.width, self.height))
        
        # Draw eyes
        eye_size = 8
        if self.direction == 1:
            pygame.draw.ellipse(screen, WHITE, (self.x - scroll + 20, self.y + 10, eye_size, eye_size))
            pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 22, self.y + 12, eye_size//2, eye_size//2))
        else:
            pygame.draw.ellipse(screen, WHITE, (self.x - scroll + 5, self.y + 10, eye_size, eye_size))
            pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 7, self.y + 12, eye_size//2, eye_size//2))
        
        # Draw health bar
        pygame.draw.rect(screen, RED, (10, 10, 200, 20))
        pygame.draw.rect(screen, GREEN, (10, 10, 200 * (self.health / self.max_health), 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
        
        # Draw shoot direction indicator when aiming
        if self.shoot_direction != (self.direction, 0):
            aim_x = self.x - scroll + self.width//2
            aim_y = self.y + self.height//2
            pygame.draw.line(screen, YELLOW, 
                            (aim_x, aim_y),
                            (aim_x + self.shoot_direction[0] * 20, aim_y + self.shoot_direction[1] * 20),
                            2)

# Bullet class
class Bullet:
    def __init__(self, x, y, vel_x, vel_y):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.radius = 5
        self.color = YELLOW
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        
    def get_rect(self):
        return (self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        
    def draw(self, screen, scroll):
        pygame.draw.circle(screen, self.color, (int(self.x - scroll), int(self.y)), self.radius)
        
    def is_off_screen(self, scroll):
        return (self.x < scroll or self.x > scroll + WIDTH or 
                self.y < 0 or self.y > HEIGHT)

# Enemy class
class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.type = enemy_type
        
        if enemy_type == "ground":
            self.width = 40
            self.height = 40
            self.speed = 2
            self.health = 30
            self.shoot_cooldown = 0
            self.direction = 1
            self.move_counter = 0
            self.shoot_delay = 90  # Slower shooting
        elif enemy_type == "flying":
            self.width = 35
            self.height = 35
            self.speed = 3
            self.health = 20
            self.shoot_cooldown = 0
            self.direction = 1
            self.move_counter = 0
            self.shoot_delay = 120  # Slower shooting
        else:  # boss
            self.width = 120
            self.height = 150
            self.speed = 1
            self.health = 300
            self.shoot_cooldown = 0
            self.direction = 1
            self.move_counter = 0
            self.attack_pattern = 0
            self.attack_timer = 0
            self.shoot_delay = 30  # Slower shooting
            
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)
            
    def update(self, player_x):
        if self.type == "ground":
            # Move back and forth
            self.move_counter += 1
            if self.move_counter > 60:
                self.direction *= -1
                self.move_counter = 0
                
            self.x += self.speed * self.direction
            
            # Face the player
            if player_x > self.x:
                self.direction = 1
            else:
                self.direction = -1
                
        elif self.type == "flying":
            # Move in sine pattern
            self.y += math.sin(self.move_counter / 10) * 2
            self.move_counter += 1
            
            # Face the player
            if player_x > self.x:
                self.direction = 1
            else:
                self.direction = -1
                
        else:  # boss
            # Boss movement and attack patterns
            self.attack_timer += 1
            if self.attack_timer > 180:
                self.attack_pattern = (self.attack_pattern + 1) % 3
                self.attack_timer = 0
                
            if self.attack_pattern == 0:
                # Move toward player slowly
                if player_x > self.x:
                    self.x += self.speed
                    self.direction = 1
                else:
                    self.x -= self.speed
                    self.direction = -1
            elif self.attack_pattern == 1:
                # Move up and down
                self.y += math.sin(self.attack_timer / 10) * 3
            else:
                # Stay in place
                pass
                
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self, player_x, player_y):
        if self.shoot_cooldown == 0:
            if self.type == "ground":
                self.shoot_cooldown = self.shoot_delay
                dx = 5 * self.direction
                return Bullet(self.x + self.width//2, self.y + self.height//2, dx, 0)
            elif self.type == "flying":
                self.shoot_cooldown = self.shoot_delay
                angle = math.atan2(player_y - (self.y + self.height//2), player_x - (self.x + self.width//2))
                dx = math.cos(angle) * 6
                dy = math.sin(angle) * 6
                return Bullet(self.x + self.width//2, self.y + self.height//2, dx, dy)
            else:  # boss
                self.shoot_cooldown = self.shoot_delay
                if self.attack_pattern == 0:
                    # Spread shot
                    bullets = []
                    for i in range(-2, 3):
                        angle = math.atan2(player_y - (self.y + self.height//2), player_x - (self.x + self.width//2))
                        angle += i * 0.2
                        dx = math.cos(angle) * 7
                        dy = math.sin(angle) * 7
                        bullets.append(Bullet(self.x + self.width//2, self.y + self.height//2, dx, dy))
                    return bullets
                elif self.attack_pattern == 1:
                    # Targeted shot
                    angle = math.atan2(player_y - (self.y + self.height//2), player_x - (self.x + self.width//2))
                    dx = math.cos(angle) * 8
                    dy = math.sin(angle) * 8
                    return [Bullet(self.x + self.width//2, self.y + self.height//2, dx, dy)]
                else:
                    # Circle shot
                    bullets = []
                    for i in range(8):
                        angle = i * math.pi / 4
                        dx = math.cos(angle) * 6
                        dy = math.sin(angle) * 6
                        bullets.append(Bullet(self.x + self.width//2, self.y + self.height//2, dx, dy))
                    return bullets
        return []
    
    def draw(self, screen, scroll):
        if self.type == "ground":
            color = RED
            pygame.draw.rect(screen, color, (self.x - scroll, self.y, self.width, self.height))
            # Draw eyes
            eye_size = 8
            if self.direction == 1:
                pygame.draw.ellipse(screen, WHITE, (self.x - scroll + 25, self.y + 10, eye_size, eye_size))
                pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 27, self.y + 12, eye_size//2, eye_size//2))
            else:
                pygame.draw.ellipse(screen, WHITE, (self.x - scroll + 10, self.y + 10, eye_size, eye_size))
                pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 12, self.y + 12, eye_size//2, eye_size//2))
                
        elif self.type == "flying":
            color = PURPLE
            pygame.draw.ellipse(screen, color, (self.x - scroll, self.y, self.width, self.height))
            # Draw eyes
            eye_size = 8
            if self.direction == 1:
                pygame.draw.ellipse(screen, WHITE, (self.x - scroll + 22, self.y + 10, eye_size, eye_size))
                pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 24, self.y + 12, eye_size//2, eye_size//2))
            else:
                pygame.draw.ellipse(screen, WHITE, (self.x - scroll + 8, self.y + 10, eye_size, eye_size))
                pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 10, self.y + 12, eye_size//2, eye_size//2))
                
        else:  # boss
            color = (180, 0, 0)
            pygame.draw.rect(screen, color, (self.x - scroll, self.y, self.width, self.height))
            # Draw details
            pygame.draw.rect(screen, (100, 0, 0), (self.x - scroll, self.y, self.width, 30))
            
            # Draw eyes
            eye_size = 20
            if self.direction == 1:
                pygame.draw.ellipse(screen, YELLOW, (self.x - scroll + 80, self.y + 40, eye_size, eye_size))
                pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 86, self.y + 46, eye_size//2, eye_size//2))
            else:
                pygame.draw.ellipse(screen, YELLOW, (self.x - scroll + 20, self.y + 40, eye_size, eye_size))
                pygame.draw.ellipse(screen, BLACK, (self.x - scroll + 26, self.y + 46, eye_size//2, eye_size//2))
                
            # Draw health bar
            bar_width = 120
            pygame.draw.rect(screen, RED, (self.x - scroll, self.y - 20, bar_width, 10))
            pygame.draw.rect(screen, GREEN, (self.x - scroll, self.y - 20, bar_width * (self.health / 300), 10))
            pygame.draw.rect(screen, WHITE, (self.x - scroll, self.y - 20, bar_width, 10), 1)

# Platform class
class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)
        
    def draw(self, screen, scroll):
        pygame.draw.rect(screen, BROWN, (self.x - scroll, self.y, self.width, self.height))

# Spike class
class Spike:
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        
    def get_rect(self):
        # Return a rect that matches the visual position of the spikes
        return (self.x, self.y, self.width, self.height)
        
    def draw(self, screen, scroll):
        for i in range(self.width // 20):
            points = [
                (self.x - scroll + i * 20, self.y + self.height),
                (self.x - scroll + i * 20 + 10, self.y),
                (self.x - scroll + i * 20 + 20, self.y + self.height)
            ]
            pygame.draw.polygon(screen, RED, points)

# Health pickup class
class HealthPickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.collected = False
        
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)
        
    def draw(self, screen, scroll):
        if not self.collected:
            pygame.draw.rect(screen, GREEN, (self.x - scroll, self.y, self.width, self.height))
            pygame.draw.rect(screen, WHITE, (self.x - scroll, self.y, self.width, self.height), 2)
            pygame.draw.rect(screen, GREEN, (self.x - scroll + 5, self.y + 5, 10, 10))
            
    def check_collision(self, player):
        if not self.collected and check_collision(player.get_rect(), self.get_rect()):
            player.health = min(player.max_health, player.health + 20)
            self.collected = True
            return True
        return False

# Initialize game objects
player = Player(100, 100)
platforms = []
enemies = []
player_bullets = []
enemy_bullets = []
spikes = []
health_pickups = []
scroll = 0
game_over = False
level_complete = False

# Create platforms
platforms.append(Platform(0, HEIGHT - 40, level_length, 40))  # Ground
platforms.append(Platform(200, 450, 100, 20))
platforms.append(Platform(400, 400, 100, 20))
platforms.append(Platform(600, 350, 100, 20))
platforms.append(Platform(800, 300, 100, 20))
platforms.append(Platform(1000, 400, 100, 20))
platforms.append(Platform(1200, 450, 100, 20))
platforms.append(Platform(1400, 400, 100, 20))
platforms.append(Platform(1600, 350, 100, 20))
platforms.append(Platform(1800, 400, 100, 20))
platforms.append(Platform(2000, 450, 100, 20))
platforms.append(Platform(2200, 400, 100, 20))
platforms.append(Platform(2400, 350, 100, 20))
platforms.append(Platform(2600, 300, 100, 20))
platforms.append(Platform(2800, 350, 100, 20))
platforms.append(Platform(3000, 400, 100, 20))
platforms.append(Platform(3200, 350, 100, 20))
platforms.append(Platform(3400, 300, 100, 20))
platforms.append(Platform(3600, 350, 100, 20))
platforms.append(Platform(3800, 400, 100, 20))
platforms.append(Platform(4000, 450, 100, 20))
platforms.append(Platform(4200, 400, 100, 20))
platforms.append(Platform(4400, 350, 100, 20))
platforms.append(Platform(4600, 400, 100, 20))

# Create spikes - positioned at the same level as the ground
spikes.append(Spike(300, HEIGHT - 40, 60))
spikes.append(Spike(500, HEIGHT - 40, 60))
spikes.append(Spike(700, HEIGHT - 40, 60))
spikes.append(Spike(1500, HEIGHT - 40, 60))
spikes.append(Spike(1700, HEIGHT - 40, 60))
spikes.append(Spike(2500, HEIGHT - 40, 60))
spikes.append(Spike(2700, HEIGHT - 40, 60))
spikes.append(Spike(3500, HEIGHT - 40, 60))
spikes.append(Spike(3700, HEIGHT - 40, 60))
spikes.append(Spike(4500, HEIGHT - 40, 60))

# Create health pickups
health_pickups.append(HealthPickup(300, HEIGHT - 100))
health_pickups.append(HealthPickup(800, 250))
health_pickups.append(HealthPickup(1500, HEIGHT - 100))
health_pickups.append(HealthPickup(2200, 350))
health_pickups.append(HealthPickup(3000, HEIGHT - 100))
health_pickups.append(HealthPickup(3800, 350))
health_pickups.append(HealthPickup(4500, HEIGHT - 100))

# Create enemies
enemies.append(Enemy(500, HEIGHT - 80, "ground"))
enemies.append(Enemy(900, HEIGHT - 80, "ground"))
enemies.append(Enemy(1300, HEIGHT - 80, "ground"))
enemies.append(Enemy(1700, HEIGHT - 80, "ground"))
enemies.append(Enemy(2100, HEIGHT - 80, "ground"))
enemies.append(Enemy(2500, 300, "flying"))
enemies.append(Enemy(2900, 250, "flying"))
enemies.append(Enemy(3300, 200, "flying"))
enemies.append(Enemy(3700, 250, "flying"))
enemies.append(Enemy(4100, 300, "flying"))

# Create final boss
boss = Enemy(4800, HEIGHT - 190, "boss")
enemies.append(boss)

# Game loop
running = True
while running:
    clock.tick(FPS)
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bullet = player.shoot()
                if bullet:
                    player_bullets.append(bullet)
            if event.key == pygame.K_r and (game_over or level_complete):
                # Reset game
                player = Player(100, 100)
                player_bullets = []
                enemy_bullets = []
                scroll = 0
                game_over = False
                level_complete = False
                
                # Reset enemies
                for enemy in enemies:
                    if enemy.type == "ground":
                        enemy.health = 30
                    elif enemy.type == "flying":
                        enemy.health = 20
                    else:
                        enemy.health = 300
                
                # Reset health pickups
                for pickup in health_pickups:
                    pickup.collected = False
    
    if not game_over and not level_complete:
        # Update player
        player.move(platforms)
        
        # Update scroll based on player position
        if player.x > scroll + WIDTH - scroll_threshold:
            scroll = player.x - (WIDTH - scroll_threshold)
        if player.x < scroll + scroll_threshold:
            scroll = player.x - scroll_threshold
        if scroll < 0:
            scroll = 0
        if scroll > level_length - WIDTH:
            scroll = level_length - WIDTH
            
        # Update player bullets
        for bullet in player_bullets[:]:
            bullet.update()
            if bullet.is_off_screen(scroll):
                player_bullets.remove(bullet)
                continue
                
            # Check for collision with enemies using bounding boxes
            for enemy in enemies[:]:
                if check_collision(bullet.get_rect(), enemy.get_rect()):
                    enemy.health -= 10
                    if bullet in player_bullets:
                        player_bullets.remove(bullet)
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                    break
                    
        # Update enemy bullets
        for bullet in enemy_bullets[:]:
            bullet.update()
            if bullet.is_off_screen(scroll):
                enemy_bullets.remove(bullet)
                continue
                
            # Check for collision with player using bounding boxes
            if check_collision(bullet.get_rect(), player.get_rect()) and player.invincibility == 0:
                player.health -= 10
                player.invincibility = 30
                if bullet in enemy_bullets:
                    enemy_bullets.remove(bullet)
                if player.health <= 0:
                    game_over = True
                    
        # Update enemies
        for enemy in enemies:
            enemy.update(player.x)
            
            # Check for collision with player using bounding boxes
            if check_collision(player.get_rect(), enemy.get_rect()) and player.invincibility == 0:
                player.health -= 5
                player.invincibility = 30
                if player.health <= 0:
                    game_over = True
                    
            # Enemy shooting
            if enemy.type == "boss":
                bullets = enemy.shoot(player.x, player.y)
                enemy_bullets.extend(bullets)
            else:
                bullet = enemy.shoot(player.x, player.y)
                if bullet:
                    enemy_bullets.append(bullet)
                    
        # Check for collision with spikes using bounding boxes
        for spike in spikes:
            spike_rect = spike.get_rect()
            
            # Check if player is touching the spike
            if check_collision(player.get_rect(), spike_rect) and player.invincibility == 0:
                player.health -= 20
                player.invincibility = 30
                if player.health <= 0:
                    game_over = True
                    
        # Check for health pickups
        for pickup in health_pickups:
            pickup.check_collision(player)
                    
        # Check if boss is defeated
        if boss not in enemies and not level_complete:
            level_complete = True
    
    # Draw everything
    screen.fill(DARK_BLUE)  # Background color
    
    # Draw a simple background
    for i in range(10):
        pygame.draw.rect(screen, (60, 60, 90), (i * 800 - scroll // 3 % 800, HEIGHT - 100, 100, 100))
    
    # Draw platforms
    for platform in platforms:
        platform.draw(screen, scroll)
        
    # Draw spikes
    for spike in spikes:
        spike.draw(screen, scroll)
        
    # Draw health pickups
    for pickup in health_pickups:
        pickup.draw(screen, scroll)
    
    # Draw enemies
    for enemy in enemies:
        enemy.draw(screen, scroll)
    
    # Draw player bullets
    for bullet in player_bullets:
        bullet.draw(screen, scroll)
        
    # Draw enemy bullets
    for bullet in enemy_bullets:
        bullet.draw(screen, scroll)
    
    # Draw player
    player.draw(screen, scroll)
    
    # Draw game status
    if game_over:
        font = pygame.font.SysFont(None, 72)
        text = font.render("GAME OVER", True, RED)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        
        font = pygame.font.SysFont(None, 36)
        text = font.render("Press R to restart", True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 50))
        
    if level_complete:
        font = pygame.font.SysFont(None, 72)
        text = font.render("LEVEL COMPLETE!", True, GREEN)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        
        font = pygame.font.SysFont(None, 36)
        text = font.render("Press R to play again", True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 50))
    
    # Draw controls help
    font = pygame.font.SysFont(None, 24)
    text = font.render("Arrow Keys: Move | W/Up: Jump | Space: Shoot (with direction) | S/Down: Move Down", True, WHITE)
    screen.blit(text, (10, HEIGHT - 30))
    
    # Update display
    pygame.display.flip()

pygame.quit()