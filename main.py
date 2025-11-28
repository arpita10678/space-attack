import pygame
import random
from settings import WIDTH, HEIGHT, FPS
from db import init_db, update_stats, get_high_scores

pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SPACE ATTACK")

clock = pygame.time.Clock()

# ---------------------------------------------------------
# LOAD ASSETS
# ---------------------------------------------------------
HOMEPAGE = pygame.image.load("assets/bg.png").convert()
HOMEPAGE = pygame.transform.scale(HOMEPAGE, (WIDTH, HEIGHT))

BG = pygame.image.load("assets/bg.png").convert()

SHIP = pygame.image.load("assets/ship.png").convert_alpha()
UFO = pygame.image.load("assets/ufo.png").convert_alpha()
BULLET = pygame.image.load("assets/bullet.png").convert_alpha()

PLANETS = [
    pygame.image.load("assets/planet1.png").convert_alpha(),
    pygame.image.load("assets/planet2.png").convert_alpha(),
    pygame.image.load("assets/planet3.png").convert_alpha(),
    pygame.image.load("assets/planet4.png").convert_alpha(),
]

METEOR = pygame.image.load("assets/meteor.png").convert_alpha()
EXPLOSION = pygame.image.load("assets/explosion.png").convert_alpha()
SMALL_EXPL = pygame.image.load("assets/small_explosion.png").convert_alpha()

# ---------------------------------------------------------
# FONTS
# ---------------------------------------------------------
TITLE_FONT = pygame.font.Font("assets/fonts/PressStart2P.ttf", 72)
BUTTON_FONT = pygame.font.Font("assets/fonts/PressStart2P.ttf", 32)
STAT_FONT = pygame.font.Font("assets/fonts/PressStart2P.ttf", 28)
GAMEOVER_FONT = pygame.font.Font("assets/fonts/PressStart2P.ttf", 64)

# ---------------------------------------------------------
# SCALE GAME SPRITES
# ---------------------------------------------------------
SHIP = pygame.transform.scale(SHIP, (85, 110))
UFO = pygame.transform.scale(UFO, (90, 60))
BULLET = pygame.transform.scale(BULLET, (10, 20))
METEOR = pygame.transform.scale(METEOR, (80, 80))

PLANETS = [
    pygame.transform.scale(PLANETS[0], (150, 150)),
    pygame.transform.scale(PLANETS[1], (160, 160)),
    pygame.transform.scale(PLANETS[2], (130, 130)),
    pygame.transform.scale(PLANETS[3], (150, 150)),
]

EXPLOSION = pygame.transform.scale(EXPLOSION, (150, 150))
SMALL_EXPL = pygame.transform.scale(SMALL_EXPL, (80, 80))

# ---------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------
scroll_y = 0
distance_traveled = 0

bullets = []
enemies = []
planets = []
meteors = []
small_explosions = []

ship_explosion = None
score = 0
kills = 0
lives = 3

paused = False
pause_start = 0
invincible = False
inv_timer = 0


# ---------------------------------------------------------
# BUTTON CLASS (ANIMATED)
# ---------------------------------------------------------
class Button:
    def __init__(self, text, y, center_x=None):
        self.text = text
        self.font = BUTTON_FONT
        self.y = y
        self.scale = 1.0
        self.hovered = False
        self.center_x = center_x if center_x else WIDTH // 2

    def draw(self):
        mx, my = pygame.mouse.get_pos()
        
        rendered = self.font.render(self.text, True, (255, 255, 255))
        w, h = rendered.get_size()
        rect = pygame.Rect(self.center_x - w // 2, self.y, w, h)

        # Hover Animation
        if rect.collidepoint(mx, my):
            self.scale = min(self.scale + 0.08, 1.25)
            self.hovered = True
        else:
            self.scale = max(self.scale - 0.08, 1.0)
            self.hovered = False

        scaled = pygame.transform.scale(rendered, (int(w * self.scale), int(h * self.scale)))
        WIN.blit(scaled, (self.center_x - scaled.get_width()//2, self.y))

        return rect


# ---------------------------------------------------------
# PLANET PLACEMENT CHECK — NO MERGING
# ---------------------------------------------------------
def can_place_planet(new_x, new_y, sprite):
    nw, nh = sprite.get_width(), sprite.get_height()
    new_rect = pygame.Rect(new_x, new_y, nw, nh)

    for px, py, spr in planets:
        pw, ph = spr.get_width(), spr.get_height()
        p_rect = pygame.Rect(px, py, pw, ph)

        if new_rect.colliderect(p_rect):
            return False

        if abs(new_x - px) < (nw//2 + pw//2 + 100) and abs(new_y - py) < (nh//2 + ph//2 + 100):
            return False

    return True


# ---------------------------------------------------------
# UFO PLANET COLLISION CHECK
# ---------------------------------------------------------
def ufo_collides_planet(x, y):
    rect = pygame.Rect(x, y, UFO.get_width(), UFO.get_height())
    for p in planets:
        if rect.colliderect(pygame.Rect(p[0], p[1], p[2].get_width(), p[2].get_height())):
            return True
    return False


# ---------------------------------------------------------
# BLACKOUT SEQUENCE
# ---------------------------------------------------------
def start_life_lost_pause(px, py):
    global paused, pause_start, ship_explosion, invincible, inv_timer
    global enemies, meteors, bullets, planets

    paused = True
    pause_start = pygame.time.get_ticks()
    ship_explosion = (px - 30, py - 30)

    invincible = True
    inv_timer = pygame.time.get_ticks()

    enemies = []
    meteors = []
    bullets = []

    clean = []
    ship_rect = pygame.Rect(px, py, SHIP.get_width(), SHIP.get_height())
    for p in planets:
        if not ship_rect.colliderect(pygame.Rect(p[0], p[1], p[2].get_width(), p[2].get_height())):
            clean.append(p)
    planets = clean


def update_pause(px, py):
    global paused
    elapsed = pygame.time.get_ticks() - pause_start
    if elapsed >= 1200:
        paused = False
        return

    WIN.fill((0, 0, 0))

    if ship_explosion:
        WIN.blit(EXPLOSION, ship_explosion)

    if (pygame.time.get_ticks() // 150) % 2 == 0:
        WIN.blit(SHIP, (px, py))

    msg = pygame.font.Font("assets/fonts/PressStart2P.ttf", 64).render("LIFE LOST!", True, (255, 0, 0))
    WIN.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 150))
    pygame.display.update()


# ---------------------------------------------------------
# HOMEPAGE
# ---------------------------------------------------------
def homepage_screen():
    play_btn = Button("PLAY", 350)
    stats_btn = Button("VIEW STATS", 450)

    while True:
        WIN.blit(HOMEPAGE, (0, 0))

        title = TITLE_FONT.render("SPACE ATTACK", True, (255, 255, 255))
        WIN.blit(title, (WIDTH//2 - title.get_width()//2, 120))

        play_rect = play_btn.draw()
        stats_rect = stats_btn.draw()

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if play_rect.collidepoint(mx, my):
                    return
                if stats_rect.collidepoint(mx, my):
                    stats_screen()


# ---------------------------------------------------------
# GAME OVER SCREEN
# ---------------------------------------------------------
def game_over_screen(final_score, final_kills):

    restart_btn = Button("RESTART", 420)
    end_btn = Button("END", 500)

    while True:
        WIN.blit(HOMEPAGE, (0, 0))

        title = GAMEOVER_FONT.render("GAME OVER", True, (255, 255, 255))
        WIN.blit(title, (WIDTH//2 - title.get_width()//2, 140))

        sc = STAT_FONT.render(f"SCORE: {final_score}", True, (255, 255, 0))
        kl = STAT_FONT.render(f"KILLS: {final_kills}", True, (255, 200, 0))

        WIN.blit(sc, (WIDTH//2 - sc.get_width()//2, 260))
        WIN.blit(kl, (WIDTH//2 - kl.get_width()//2, 320))

        restart_rect = restart_btn.draw()
        end_rect = end_btn.draw()

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if restart_rect.collidepoint(mx, my):
                    return "RESTART"
                if end_rect.collidepoint(mx, my):
                    pygame.quit(); exit()


# ---------------------------------------------------------
# STATS SCREEN
# ---------------------------------------------------------
def stats_screen():

    back_button = Button("BACK", HEIGHT - 100, center_x=150)
    scores = get_high_scores()

    while True:
        WIN.blit(HOMEPAGE, (0, 0))

        title = TITLE_FONT.render("HIGH SCORES", True, (255, 255, 255))
        WIN.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        y = 220
        if scores:
            for s, k in scores[:8]:
                entry = STAT_FONT.render(f"SCORE {s}  KILLS {k}", True, (255, 255, 0))
                WIN.blit(entry, (WIDTH//2 - entry.get_width()//2, y))
                y += 50
        else:
            msg = STAT_FONT.render("NO DATA", True, (255, 255, 0))
            WIN.blit(msg, (WIDTH//2 - msg.get_width()//2, 300))

        back_rect = back_button.draw()

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if back_rect.collidepoint(mx, my):
                    return


# ---------------------------------------------------------
# DRAW GAME
# ---------------------------------------------------------
def draw_window(px, py):
    global scroll_y

    scroll_y += 2
    if scroll_y >= BG.get_height():
        scroll_y = 0

    WIN.blit(BG, (0, scroll_y - BG.get_height()))
    WIN.blit(BG, (0, scroll_y))

    for p in planets: WIN.blit(p[2], (p[0], p[1]))
    for m in meteors: WIN.blit(METEOR, (m[0], m[1]))
    for e in enemies: WIN.blit(UFO, (e[0], e[1]))
    for b in bullets: WIN.blit(BULLET, (b[0], b[1]))
    for ex in small_explosions: WIN.blit(SMALL_EXPL, (ex[0], ex[1]))

    if not invincible or (pygame.time.get_ticks() // 150) % 2 == 0:
        WIN.blit(SHIP, (px, py))

    ui = pygame.font.Font(None, 36)
    WIN.blit(ui.render(f"Score: {score}", True, (255, 255, 0)), (10, 10))
    WIN.blit(ui.render(f"Lives: {lives}", True, (255, 80, 80)), (WIDTH - 130, 10))

    pygame.display.update()


# ---------------------------------------------------------
# MAIN GAME LOOP (with smooth UFO AI)
# ---------------------------------------------------------
def main_game():
    global bullets, enemies, meteors, planets, small_explosions
    global score, kills, lives, paused, invincible, distance_traveled

    bullets = []
    enemies = []
    meteors = []
    planets = []
    small_explosions = []
    score = kills = 0
    lives = 3
    paused = False
    invincible = False
    distance_traveled = 0

    px = WIDTH//2 - SHIP.get_width()//2
    py = HEIGHT - 150

    enemy_timer = 0
    meteor_timer = 0

    UFO_AVOID_COOLDOWN = 300
    ufo_avoid_timer = 0

    while True:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                update_stats(score, kills)
                return

        if paused:
            update_pause(px, py)
            if not paused and lives <= 0:
                update_stats(score, kills)
                result = game_over_screen(score, kills)
                if result == "RESTART":
                    return "RESTART"
                return
            continue

        distance_traveled += 2
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] and px > 0: px -= 5
        if keys[pygame.K_RIGHT] and px < WIDTH - SHIP.get_width(): px += 5
        if keys[pygame.K_SPACE] and len(bullets) < 7:
            bullets.append([px + SHIP.get_width()//2 - 4, py])

        # BULLETS
        for b in bullets[:]:
            b[1] -= 10
            if b[1] < -40:
                bullets.remove(b)

        # ---------------------------------------------------------
        # PLANETS (NO OVERLAP)
        # ---------------------------------------------------------
        if distance_traveled % random.randint(900, 1600) < 5:
            sprite = random.choice(PLANETS)
            placed = False
            for attempt in range(25):
                x = random.randint(80, WIDTH - sprite.get_width() - 80)
                y = random.randint(-350, -200)
                if can_place_planet(x, y, sprite):
                    planets.append([x, y, sprite])
                    placed = True
                    break

        for p in planets[:]:
            p[1] += 2
            if p[1] > HEIGHT + 250:
                planets.remove(p)

        # ---------------------------------------------------------
        # UFOs — SMOOTH MOVEMENT FIX
        # ---------------------------------------------------------
        enemy_timer += 1
        if enemy_timer > 120:
            enemies.append([random.randint(60, WIDTH-100), -80, 0])  # add drift dir
            enemy_timer = 0

        for e in enemies[:]:
            ex, ey, drift = e

            # Smooth chase: curved alignment
            if ex < px - 15:
                ex += 1.5
            elif ex > px + 15:
                ex -= 1.5
            else:
                ex += (px - ex) * 0.03

            # Avoidance cooldown
            if now - ufo_avoid_timer < UFO_AVOID_COOLDOWN:
                ex += drift * 1.2
            else:
                if ufo_collides_planet(ex, ey):
                    drift = 1 if random.random() < 0.5 else -1
                    ufo_avoid_timer = now

            # limit ufo drifting inside screen
            ex = max(40, min(WIDTH - 140, ex))

            ey += 2
            if ey > HEIGHT:
                enemies.remove(e)
                continue

            # update
            e[0], e[1], e[2] = ex, ey, drift

            # bullet collision
            enemy_rect = pygame.Rect(ex, ey, 90, 60)
            for b in bullets[:]:
                if enemy_rect.colliderect(pygame.Rect(b[0], b[1], 10, 20)):
                    small_explosions.append([ex, ey, now])
                    enemies.remove(e)
                    bullets.remove(b)
                    score += 20
                    kills += 1
                    break

        # REMOVE SMALL EXPLOSIONS
        for ex in small_explosions[:]:
            if now - ex[2] > 240:
                small_explosions.remove(ex)

        # ---------------------------------------------------------
        # METEORS
        # ---------------------------------------------------------
        meteor_timer += 1
        if meteor_timer > 240:
            meteors.append([WIDTH + 50, -50])
            meteor_timer = 0

        for m in meteors[:]:
            m[0] -= 3
            m[1] += 4
            if m[1] > HEIGHT + 220:
                meteors.remove(m)

        # INVINCIBLE WINDOW
        if invincible and now - inv_timer > 1500:
            invincible = False

        ship_rect = pygame.Rect(px, py, SHIP.get_width(), SHIP.get_height())

        for m in meteors:
            if ship_rect.colliderect(pygame.Rect(m[0], m[1], 80, 80)) and not invincible:
                lives -= 1
                start_life_lost_pause(px, py)
                break

        for p in planets:
            if ship_rect.colliderect(pygame.Rect(p[0], p[1], p[2].get_width(), p[2].get_height())) and not invincible:
                lives -= 1
                start_life_lost_pause(px, py)
                break

        for ex, ey, drift in enemies:
            if ship_rect.colliderect(pygame.Rect(ex, ey, 90, 60)) and not invincible:
                lives -= 1
                start_life_lost_pause(px, py)
                break

        draw_window(px, py)


# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------
if __name__ == "__main__":
    init_db()

    while True:
        homepage_screen()
        result = main_game()

        if result == "RESTART":
            continue
