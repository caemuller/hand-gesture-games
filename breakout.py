import cv2
import mediapipe as mp
import pygame
import random
import time
import math

# ========================
# MEDIAPIPE SETUP
# ========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ========================
# PYGAME SETUP
# ========================
pygame.init()

WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Breakout")

clock = pygame.time.Clock()

# Colors
BG = (20, 20, 30)
WHITE = (255, 255, 255)
PADDLE_COLOR = (80, 200, 255)
BALL_COLOR = (255, 100, 100)
BRICK_COLORS = [(255, 99, 132), (255, 159, 64), (255, 205, 86),
                (75, 192, 192), (54, 162, 235)]

font = pygame.font.SysFont("Segoe UI", 28)
big_font = pygame.font.SysFont("Segoe UI", 60)

# ========================
# GAME STATE
# ========================
def reset_game():
    global paddle_x, ball_pos, ball_vel, bricks, score, game_over

    paddle_x = WIDTH // 2 - 60
    ball_pos = [WIDTH // 2, HEIGHT // 2]
    ball_vel = [random.choice([-4, 4]), -4]

    bricks = []
    rows, cols = 5, 10
    brick_w = WIDTH // cols
    brick_h = 25

    for r in range(rows):
        for c in range(cols):
            bricks.append(pygame.Rect(
                c * brick_w, r * brick_h + 50, brick_w - 2, brick_h - 2
            ))

    score = 0
    game_over = False

reset_game()

# Paddle
PADDLE_W, PADDLE_H = 120, 15
PADDLE_Y = HEIGHT - 40

# ========================
# OK GESTURE
# ========================
ok_start_time = None

def is_ok_gesture(hand_landmarks):
    global ok_start_time

    lm = hand_landmarks.landmark

    thumb = lm[4]
    index = lm[8]
    middle = lm[12]
    ring = lm[16]
    pinky = lm[20]

    dist = math.hypot(thumb.x - index.x, thumb.y - index.y)
    touching = dist < 0.04

    fingers_extended = (
        middle.y < lm[10].y and
        ring.y < lm[14].y and
        pinky.y < lm[18].y
    )

    valid = touching and fingers_extended

    if valid:
        if ok_start_time is None:
            ok_start_time = time.time()
        elif time.time() - ok_start_time > 0.8:
            ok_start_time = None
            return True
    else:
        ok_start_time = None

    return False

# ========================
# DRAW
# ========================
def draw():
    win.fill(BG)

    # Paddle
    pygame.draw.rect(win, PADDLE_COLOR,
                     (paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H),
                     border_radius=8)

    # Ball
    pygame.draw.circle(win, BALL_COLOR, ball_pos, 8)

    # Bricks
    for i, brick in enumerate(bricks):
        color = BRICK_COLORS[i % len(BRICK_COLORS)]
        pygame.draw.rect(win, color, brick, border_radius=4)

    # Score
    txt = font.render(f"Score: {score}", True, WHITE)
    win.blit(txt, (10, 10))

    pygame.display.update()


def draw_game_over():
    win.fill(BG)

    text1 = big_font.render("GAME OVER", True, (200, 50, 50))
    text2 = font.render(f"Score: {score}", True, WHITE)
    text3 = font.render("Make OK sign to restart", True, WHITE)

    win.blit(text1, text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
    win.blit(text2, text2.get_rect(center=(WIDTH//2, HEIGHT//2)))
    win.blit(text3, text3.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))

    pygame.display.update()

# ========================
# GAME LOGIC
# ========================

MAX_SPEED = 12

def clamp_velocity():
    ball_vel[0] = max(-MAX_SPEED, min(MAX_SPEED, ball_vel[0]))
    ball_vel[1] = max(-MAX_SPEED, min(MAX_SPEED, ball_vel[1]))

def update_ball():
    global game_over, score

    ball_pos[0] += ball_vel[0]
    ball_pos[1] += ball_vel[1]

    # Wall collisions
    if ball_pos[0] <= 0 or ball_pos[0] >= WIDTH:
        ball_vel[0] *= -1.1   # reverse + speed up

    if ball_pos[1] <= 0:
        ball_vel[1] *= -1.1

    # Paddle collision
    paddle_rect = pygame.Rect(paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)

    if paddle_rect.collidepoint(ball_pos[0], ball_pos[1]):
        ball_vel[1] *= -1.1

        # Add control based on hit position
        offset = (ball_pos[0] - paddle_x) / PADDLE_W - 0.5
        ball_vel[0] = offset * 10

    # Brick collision
    for brick in bricks[:]:
        if brick.collidepoint(ball_pos[0], ball_pos[1]):
            bricks.remove(brick)
            ball_vel[1] *= -1.1
            score += 1
            break

    # Lose condition
    if ball_pos[1] > HEIGHT:
        game_over = True

    clamp_velocity()
# ========================
# MAIN LOOP
# ========================
running = True

while running:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # ========================
    # GAME OVER
    # ========================
    if game_over:
        draw_game_over()

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            if is_ok_gesture(hand):
                time.sleep(1)
                reset_game()

        cv2.imshow("Camera", img)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if cv2.waitKey(1) & 0xFF == 27:
            break

        continue

    # ========================
    # GESTURE CONTROL
    # ========================
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            index_tip = handLms.landmark[8]

            # Map hand X → paddle X
            paddle_x = int(index_tip.x * WIDTH - PADDLE_W // 2)

            # Clamp inside screen
            paddle_x = max(0, min(WIDTH - PADDLE_W, paddle_x))

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

    # ========================
    # UPDATE
    # ========================
    update_ball()

    # ========================
    # EVENTS
    # ========================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw()
    clock.tick(60)

    cv2.imshow("Camera", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
