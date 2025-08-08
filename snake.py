import pygame
import random
import time
from itertools import cycle
import math
from collections import deque

# Initialize Pygame
pygame.init()

# Set up the game window
width = 800
height = 600
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")

# Game Constants
trail_length = 10
particle_lifetime = 20
turn_smoothness = 5
snake_block = 20
snake_speed = 15

# Color pairs (bright, neon-like colors that pop against black)
color_pairs = [
    ((0, 255, 127), (255, 50, 100)),    # Bright Green & Hot Pink
    ((0, 191, 255), (255, 140, 0)),     # Deep Sky Blue & Orange
    ((255, 0, 255), (0, 255, 200)),     # Magenta & Cyan
    ((147, 112, 219), (255, 215, 0)),   # Purple & Gold
    ((255, 69, 0), (0, 255, 255)),      # Red-Orange & Aqua
    ((255, 255, 0), (0, 128, 255)),     # Yellow & Blue-Orange
]
color_cycle = cycle(color_pairs)

# Current colors
current_pair = next(color_cycle)
snake_color = current_pair[0]
food_color = current_pair[1]

# Colors
background = (0, 0, 0)        # Black
score_color = (200, 200, 200) # Light gray
box_color = (50, 50, 50)      # Dark gray

# Initialize clock
clock = pygame.time.Clock()

# Fonts
score_font = pygame.font.SysFont(None, 36)
score_box_font = pygame.font.SysFont('courier', 24)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = particle_lifetime
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface):
        alpha = int((self.lifetime / particle_lifetime) * 255)
        color = (*self.color[:3], alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

class Snake:
    def __init__(self, x, y):
        self.positions = deque([(x, y)])  # Start with just the head
        self.trail = deque(maxlen=trail_length)
        self.particles = []
        self.target_angle = 0
        self.current_angle = 0
        self.length = 1  # Start with length 1
        self.turning = False

    def update(self, new_head):
        # Update positions
        self.positions.append(new_head)
        if len(self.positions) > self.length:
            self.positions.popleft()

        # Update trail
        self.trail.append(new_head)

        # Update particles
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update()

        # Smooth turning
        if self.turning:
            angle_diff = (self.target_angle - self.current_angle) % 360
            if abs(angle_diff) > 1:
                self.current_angle += angle_diff / turn_smoothness
            else:
                self.turning = False

    def add_particles(self, x, y, color):
        for _ in range(5):
            self.particles.append(Particle(x, y, color))

    def draw(self, surface):
        # Draw snake body (solid color)
        for i, pos in enumerate(self.positions):
            if i == len(self.positions) - 1:
                # Draw head
                self.draw_head(surface, pos[0], pos[1])
            else:
                # Draw body segment
                pygame.draw.circle(surface, snake_color,
                                 (int(pos[0] + snake_block//2),
                                  int(pos[1] + snake_block//2)),
                                 snake_block//2 - 2)

        # Draw particles
        for particle in self.particles:
            particle.draw(surface)

    def draw_head(self, surface, x, y):
        # Calculate eye positions based on current angle
        eye_offset = 3
        eye_distance = 5
        
        center_x = x + snake_block//2
        center_y = y + snake_block//2
        
        # Draw head
        pygame.draw.circle(surface, snake_color, (center_x, center_y), snake_block//2)
        
        # Calculate eye positions
        eye1_x = center_x + math.cos(math.radians(self.current_angle - eye_offset)) * eye_distance
        eye1_y = center_y + math.sin(math.radians(self.current_angle - eye_offset)) * eye_distance
        eye2_x = center_x + math.cos(math.radians(self.current_angle + eye_offset)) * eye_distance
        eye2_y = center_y + math.sin(math.radians(self.current_angle + eye_offset)) * eye_distance
        
        # Draw eyes
        pygame.draw.circle(surface, (255, 255, 255), (int(eye1_x), int(eye1_y)), 3)
        pygame.draw.circle(surface, (255, 255, 255), (int(eye2_x), int(eye2_y)), 3)
        pygame.draw.circle(surface, (0, 0, 0), (int(eye1_x), int(eye1_y)), 1)
        pygame.draw.circle(surface, (0, 0, 0), (int(eye2_x), int(eye2_y)), 1)

def draw_score_box(score):
    # Create the score text
    score_text = f"[SCORE: {score}]"
    text_surface = score_box_font.render(score_text, True, score_color)
    text_rect = text_surface.get_rect()
    
    # Position in top right with margin
    margin = 20
    text_rect.topright = (width - margin, margin)
    
    # Draw box around score with more transparency
    padding = 10
    box_rect = pygame.Rect(text_rect.x - padding,
                          text_rect.y - padding,
                          text_rect.width + (padding * 2),
                          text_rect.height + (padding * 2))
    
    # More transparent box
    s = pygame.Surface((box_rect.width, box_rect.height))
    s.set_alpha(25)
    s.fill(box_color)
    window.blit(s, box_rect)
    
    # Subtle border
    pygame.draw.rect(window, score_color, box_rect, 1)
    
    # Draw text
    window.blit(text_surface, text_rect)

def draw_food(x, y):
    pygame.draw.circle(window, food_color, (x + snake_block//2, y + snake_block//2), snake_block//2)

def game_loop():
    global snake_color, food_color
    game_over = False
    game_close = False

    snake = Snake(width / 2, height / 2)
    # Start moving to the right by default
    x1_change = snake_block
    y1_change = 0

    foodx = round(random.randrange(0, width - snake_block) / 20.0) * 20.0
    foody = round(random.randrange(0, height - snake_block) / 20.0) * 20.0

    while not game_over:
        while game_close:
            window.fill(background)
            game_over_text = score_box_font.render("Game Over! Q-Quit or C-Play Again", True, score_color)
            text_rect = game_over_text.get_rect(center=(width/2, height/2))
            window.blit(game_over_text, text_rect)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                    game_close = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_c or \
                       (event.unicode and event.unicode.lower() == 'q') or \
                       (event.unicode and event.unicode.lower() == 'c'):
                        if event.key == pygame.K_q or (event.unicode and event.unicode.lower() == 'q'):
                            game_over = True
                            game_close = False
                        if event.key == pygame.K_c or (event.unicode and event.unicode.lower() == 'c'):
                            return game_loop()  # Return to start a new game

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x1_change <= 0:
                    x1_change = -snake_block
                    y1_change = 0
                    snake.target_angle = 180
                    snake.turning = True
                elif event.key == pygame.K_RIGHT and x1_change >= 0:
                    x1_change = snake_block
                    y1_change = 0
                    snake.target_angle = 0
                    snake.turning = True
                elif event.key == pygame.K_UP and y1_change <= 0:
                    y1_change = -snake_block
                    x1_change = 0
                    snake.target_angle = 270
                    snake.turning = True
                elif event.key == pygame.K_DOWN and y1_change >= 0:
                    y1_change = snake_block
                    x1_change = 0
                    snake.target_angle = 90
                    snake.turning = True

        # Get next position
        x1 = snake.positions[-1][0] + x1_change
        y1 = snake.positions[-1][1] + y1_change

        # Handle wrapping
        if x1 >= width:
            x1 = 0
        elif x1 < 0:
            x1 = width - snake_block
        if y1 >= height:
            y1 = 0
        elif y1 < 0:
            y1 = height - snake_block

        # Check collision with self (only if snake length > 1)
        if len(snake.positions) > 1:
            if [x1, y1] in [[pos[0], pos[1]] for pos in list(snake.positions)[:-1]]:
                game_close = True

        # Update and draw
        snake.update((x1, y1))
        
        window.fill(background)
        draw_food(foodx, foody)
        snake.draw(window)
        draw_score_box(len(snake.positions) - 1)

        pygame.display.update()

        # Handle food collision
        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, width - snake_block) / 20.0) * 20.0
            foody = round(random.randrange(0, height - snake_block) / 20.0) * 20.0
            snake.length += 1
            snake.add_particles(x1 + snake_block//2, y1 + snake_block//2, food_color)

            if (snake.length - 1) % 5 == 0:
                current_pair = next(color_cycle)
                snake_color = current_pair[0]
                food_color = current_pair[1]

        clock.tick(snake_speed)

    pygame.quit()
    quit()

def get_point_on_rect(rect, pos):
    # Returns (x, y) at a given distance along the rectangle's perimeter
    if pos < rect.width:
        return rect.left + pos, rect.top
    pos -= rect.width
    if pos < rect.height:
        return rect.right, rect.top + pos
    pos -= rect.height
    if pos < rect.width:
        return rect.right - pos, rect.bottom
    pos -= rect.width
    return rect.left, rect.bottom - pos

def show_start_page():
    import time
    title = "SNAKE"
    title_font = pygame.font.SysFont('arial', 120, bold=True)
    letter_colors = [pair[0] for pair in color_pairs]
    letter_surfaces = [title_font.render(letter, True, color) for letter, color in zip(title, letter_colors)]
    total_width = sum(surf.get_width() for surf in letter_surfaces)
    max_height = max(surf.get_height() for surf in letter_surfaces)
    title_rect = pygame.Rect(0, 0, total_width, max_height)
    title_rect.center = (width // 2, height // 2 - 30)  # Move title up a bit for instructions
    # Rectangle path parameters
    rect_distance = 60  # Distance from title to snake path
    rect = pygame.Rect(
        title_rect.left - rect_distance,
        title_rect.top - rect_distance,
        title_rect.width + 2 * rect_distance,
        title_rect.height + 2 * rect_distance
    )
    perimeter = 2 * (rect.width + rect.height)
    snake_length = 12
    color_index = 0
    last_color_change = time.time()
    snake_pos = 0
    running = True
    clock = pygame.time.Clock()
    while running:
        window.fill(background)
        # Draw the title, centered
        x = title_rect.x
        for surf in letter_surfaces:
            surf_rect = surf.get_rect()
            surf_rect.y = title_rect.y
            surf_rect.x = x
            window.blit(surf, surf_rect)
            x += surf.get_width()
        # Draw instruction below the rectangle
        instr_font = pygame.font.SysFont(None, 36)
        instr_text = instr_font.render("Press ENTER to start", True, score_color)
        instr_rect = instr_text.get_rect(center=(width//2, rect.bottom + 40))
        window.blit(instr_text, instr_rect)
        # Draw rectangle snake
        for i in range(snake_length, 0, -1):
            pos_on_path = (snake_pos - i * 18) % perimeter
            seg_x, seg_y = get_point_on_rect(rect, pos_on_path)
            color = color_pairs[color_index][0]
            pygame.draw.circle(window, color, (int(seg_x), int(seg_y)), snake_block // 2)
        # Draw snake head (slightly larger)
        head_x, head_y = get_point_on_rect(rect, snake_pos % perimeter)
        pygame.draw.circle(window, color_pairs[color_index][0], (int(head_x), int(head_y)), snake_block // 2 + 2)
        # Draw eyes on the head (facing forward along the path)
        next_head_x, next_head_y = get_point_on_rect(rect, (snake_pos + 6) % perimeter)
        dx = next_head_x - head_x
        dy = next_head_y - head_y
        length = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        ex = dx / length
        ey = dy / length
        perp_ex = -ey
        perp_ey = ex
        eye_offset = 10
        eye_sep = 6
        eye1_x = int(head_x + ex * eye_offset + perp_ex * eye_sep)
        eye1_y = int(head_y + ey * eye_offset + perp_ey * eye_sep)
        eye2_x = int(head_x + ex * eye_offset - perp_ex * eye_sep)
        eye2_y = int(head_y + ey * eye_offset - perp_ey * eye_sep)
        pygame.draw.circle(window, (255,255,255), (eye1_x, eye1_y), 4)
        pygame.draw.circle(window, (255,255,255), (eye2_x, eye2_y), 4)
        pygame.draw.circle(window, (0,0,0), (eye1_x, eye1_y), 2)
        pygame.draw.circle(window, (0,0,0), (eye2_x, eye2_y), 2)
        pygame.display.update()
        # Animate
        snake_pos = (snake_pos + 4) % perimeter
        if time.time() - last_color_change > 5:
            color_index = (color_index + 1) % len(color_pairs)
            last_color_change = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    running = False
        clock.tick(60)

if __name__ == "__main__":
    show_start_page()
    game_loop()
