"""
Snake — pygbag/WebAssembly build of the real pygame game.

This is the same game as ../../snake.py, restructured for the browser:
  * one async main loop driven by a `state` machine (no recursion, no quit())
  * `await asyncio.sleep(0)` each frame so the browser stays responsive

Build & run locally:
    pip install pygbag
    cd web/pygame
    pygbag .                 # serves at http://localhost:8000
    # production build lands in build/web/  — host those files anywhere static

Note: pygbag requires the entry file to be named main.py.
"""
import asyncio
import math
import random
from collections import deque
from itertools import cycle

import pygame

pygame.init()

# ── Window / constants ──
width, height = 800, 600
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")

trail_length = 10
particle_lifetime = 20
turn_smoothness = 5
snake_block = 20
snake_speed = 15

color_pairs = [
    ((0, 255, 127), (255, 50, 100)),
    ((0, 191, 255), (255, 140, 0)),
    ((255, 0, 255), (0, 255, 200)),
    ((147, 112, 219), (255, 215, 0)),
    ((255, 69, 0), (0, 255, 255)),
    ((255, 255, 0), (0, 128, 255)),
]

background = (0, 0, 0)
score_color = (200, 200, 200)
box_color = (50, 50, 50)

clock = pygame.time.Clock()
score_box_font = pygame.font.SysFont("courier", 24)


class Particle:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        self.lifetime = particle_lifetime
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface):
        pygame.draw.circle(
            surface, self.color, (int(self.x), int(self.y)), int(self.size)
        )


class Snake:
    def __init__(self, x, y):
        self.positions = deque([(x, y)])
        self.particles = []
        self.target_angle = 0
        self.current_angle = 0
        self.length = 1
        self.turning = False

    def update(self, new_head):
        self.positions.append(new_head)
        if len(self.positions) > self.length:
            self.positions.popleft()
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for p in self.particles:
            p.update()
        if self.turning:
            angle_diff = (self.target_angle - self.current_angle) % 360
            if abs(angle_diff) > 1:
                self.current_angle += angle_diff / turn_smoothness
            else:
                self.turning = False

    def add_particles(self, x, y, color):
        for _ in range(5):
            self.particles.append(Particle(x, y, color))

    def draw(self, surface, snake_color):
        for i, pos in enumerate(self.positions):
            if i == len(self.positions) - 1:
                self.draw_head(surface, pos[0], pos[1], snake_color)
            else:
                pygame.draw.circle(
                    surface, snake_color,
                    (int(pos[0] + snake_block // 2), int(pos[1] + snake_block // 2)),
                    snake_block // 2 - 2,
                )
        for p in self.particles:
            p.draw(surface)

    def draw_head(self, surface, x, y, snake_color):
        eye_offset, eye_distance = 3, 5
        cx, cy = x + snake_block // 2, y + snake_block // 2
        pygame.draw.circle(surface, snake_color, (cx, cy), snake_block // 2)
        for sign in (-1, 1):
            ex = cx + math.cos(math.radians(self.current_angle + sign * eye_offset)) * eye_distance
            ey = cy + math.sin(math.radians(self.current_angle + sign * eye_offset)) * eye_distance
            pygame.draw.circle(surface, (255, 255, 255), (int(ex), int(ey)), 3)
            pygame.draw.circle(surface, (0, 0, 0), (int(ex), int(ey)), 1)


def draw_score_box(score):
    text = f"[SCORE: {score}]"
    surf = score_box_font.render(text, True, score_color)
    rect = surf.get_rect()
    rect.topright = (width - 20, 20)
    pad = 10
    box = pygame.Rect(rect.x - pad, rect.y - pad, rect.width + pad * 2, rect.height + pad * 2)
    s = pygame.Surface((box.width, box.height))
    s.set_alpha(25)
    s.fill(box_color)
    window.blit(s, box)
    pygame.draw.rect(window, score_color, box, 1)
    window.blit(surf, rect)


def draw_food(x, y, food_color):
    pygame.draw.circle(window, food_color, (x + snake_block // 2, y + snake_block // 2), snake_block // 2)


def get_point_on_rect(rect, pos):
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


async def show_start_page():
    """Animated title screen; returns True to start, False if the window closed."""
    title = "SNAKE"
    title_font = pygame.font.SysFont("arial", 120, bold=True)
    letter_colors = [pair[0] for pair in color_pairs]
    letter_surfaces = [title_font.render(c, True, col) for c, col in zip(title, letter_colors)]
    total_width = sum(s.get_width() for s in letter_surfaces)
    max_height = max(s.get_height() for s in letter_surfaces)
    title_rect = pygame.Rect(0, 0, total_width, max_height)
    title_rect.center = (width // 2, height // 2 - 30)

    rect_distance = 60
    rect = pygame.Rect(
        title_rect.left - rect_distance, title_rect.top - rect_distance,
        title_rect.width + 2 * rect_distance, title_rect.height + 2 * rect_distance,
    )
    perimeter = 2 * (rect.width + rect.height)
    snake_length = 12
    color_index = 0
    snake_pos = 0
    frames = 0
    instr_font = pygame.font.SysFont(None, 36)

    while True:
        window.fill(background)
        x = title_rect.x
        for surf in letter_surfaces:
            r = surf.get_rect()
            r.y, r.x = title_rect.y, x
            window.blit(surf, r)
            x += surf.get_width()

        instr = instr_font.render("Press ENTER to start", True, score_color)
        window.blit(instr, instr.get_rect(center=(width // 2, rect.bottom + 40)))

        for i in range(snake_length, 0, -1):
            pos = (snake_pos - i * 18) % perimeter
            sx, sy = get_point_on_rect(rect, pos)
            pygame.draw.circle(window, color_pairs[color_index][0], (int(sx), int(sy)), snake_block // 2)
        hx, hy = get_point_on_rect(rect, snake_pos % perimeter)
        pygame.draw.circle(window, color_pairs[color_index][0], (int(hx), int(hy)), snake_block // 2 + 2)

        nx, ny = get_point_on_rect(rect, (snake_pos + 6) % perimeter)
        dx, dy = nx - hx, ny - hy
        length = max(1, (dx * dx + dy * dy) ** 0.5)
        ex, ey = dx / length, dy / length
        px, py = -ey, ex
        for sign in (1, -1):
            e1x = int(hx + ex * 10 + px * 6 * sign)
            e1y = int(hy + ey * 10 + py * 6 * sign)
            pygame.draw.circle(window, (255, 255, 255), (e1x, e1y), 4)
            pygame.draw.circle(window, (0, 0, 0), (e1x, e1y), 2)

        pygame.display.update()

        snake_pos = (snake_pos + 4) % perimeter
        frames += 1
        if frames % 300 == 0:
            color_index = (color_index + 1) % len(color_pairs)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return True

        clock.tick(60)
        await asyncio.sleep(0)


async def game_round():
    """Play one game. Returns 'restart', 'quit', or 'closed'."""
    color_cycle = cycle(color_pairs)
    snake_color, food_color = next(color_cycle)

    snake = Snake(width / 2, height / 2)
    x1_change, y1_change = snake_block, 0
    foodx = round(random.randrange(0, width - snake_block) / 20.0) * 20.0
    foody = round(random.randrange(0, height - snake_block) / 20.0) * 20.0

    game_close = False
    while True:
        if game_close:
            window.fill(background)
            msg = score_box_font.render("Game Over! Q-Quit or C-Play Again", True, score_color)
            window.blit(msg, msg.get_rect(center=(width / 2, height / 2)))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "closed"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return "quit"
                    if event.key == pygame.K_c:
                        return "restart"
            clock.tick(snake_speed)
            await asyncio.sleep(0)
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "closed"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x1_change <= 0:
                    x1_change, y1_change, snake.target_angle, snake.turning = -snake_block, 0, 180, True
                elif event.key == pygame.K_RIGHT and x1_change >= 0:
                    x1_change, y1_change, snake.target_angle, snake.turning = snake_block, 0, 0, True
                elif event.key == pygame.K_UP and y1_change <= 0:
                    y1_change, x1_change, snake.target_angle, snake.turning = -snake_block, 0, 270, True
                elif event.key == pygame.K_DOWN and y1_change >= 0:
                    y1_change, x1_change, snake.target_angle, snake.turning = snake_block, 0, 90, True

        x1 = snake.positions[-1][0] + x1_change
        y1 = snake.positions[-1][1] + y1_change
        if x1 >= width:
            x1 = 0
        elif x1 < 0:
            x1 = width - snake_block
        if y1 >= height:
            y1 = 0
        elif y1 < 0:
            y1 = height - snake_block

        if len(snake.positions) > 1 and [x1, y1] in [[p[0], p[1]] for p in list(snake.positions)[:-1]]:
            game_close = True

        snake.update((x1, y1))

        window.fill(background)
        draw_food(foodx, foody, food_color)
        snake.draw(window, snake_color)
        draw_score_box(len(snake.positions) - 1)
        pygame.display.update()

        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, width - snake_block) / 20.0) * 20.0
            foody = round(random.randrange(0, height - snake_block) / 20.0) * 20.0
            snake.length += 1
            snake.add_particles(x1 + snake_block // 2, y1 + snake_block // 2, food_color)
            if (snake.length - 1) % 5 == 0:
                snake_color, food_color = next(color_cycle)

        clock.tick(snake_speed)
        await asyncio.sleep(0)


async def main():
    while True:
        if not await show_start_page():
            break
        result = "restart"
        while result == "restart":
            result = await game_round()
        if result in ("quit", "closed"):
            break
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
