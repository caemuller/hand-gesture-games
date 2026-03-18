import cv2
import mediapipe as mp
import pygame
import time
import random
import math

# ========================
# Gesture Detection Setup
# ========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ========================
# Snake Game Setup
# ========================
pygame.init()

WIDTH, HEIGHT = 600, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Snake")

clock = pygame.time.Clock()

block = 20

font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 60)

# ========================
# Game State
# ========================
def reset_game():
    global snake, direction, food, score, game_over
    snake = [(300, 300)]
    direction = "RIGHT"
    food = (random.randrange(0, WIDTH, block),
            random.randrange(0, HEIGHT, block))
    score = 0
    game_over = False


waiting_start = True
reset_game()

# ========================
# Helpers
# ========================
def draw():
    win.fill((0, 0, 0))

    for s in snake:
        pygame.draw.rect(win, (0, 255, 0), (*s, block, block))

    pygame.draw.rect(win, (255, 0, 0), (*food, block, block))

    txt = font.render(f"Score: {score}", True, (255, 255, 255))
    win.blit(txt, (10, 10))

    pygame.display.update()


def draw_start_screen():
    win.fill((0, 0, 0))

    text1 = big_font.render("Gesture Snake", True, (0, 255, 0))
    text2 = font.render("Show OK sign to start", True, (200, 200, 200))

    win.blit(text1, text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
    win.blit(text2, text2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))

    pygame.display.update()


def draw_game_over():
    win.fill((0, 0, 0))

    text1 = big_font.render("YOU LOSE", True, (255, 0, 0))
    text2 = font.render(f"Score: {score}", True, (255, 255, 255))
    text3 = font.render("Show OK sign", True, (200, 200, 200))

    win.blit(text1, text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
    win.blit(text2, text2.get_rect(center=(WIDTH//2, HEIGHT//2)))
    win.blit(text3, text3.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))

    pygame.display.update()


def move_snake():
    global food, score, game_over

    x, y = snake[0]

    if direction == "UP":
        y -= block
    elif direction == "DOWN":
        y += block
    elif direction == "LEFT":
        x -= block
    elif direction == "RIGHT":
        x += block

    x %= WIDTH
    y %= HEIGHT

    new_head = (x, y)

    if new_head in snake:
        game_over = True
        return

    snake.insert(0, new_head)

    if new_head == food:
        score += 1
        food = (random.randrange(0, WIDTH, block),
                random.randrange(0, HEIGHT, block))
    else:
        snake.pop()


# ========================
# Gesture Helpers
# ========================
ok_start_time = None

def is_ok_gesture(hand_landmarks):
    global ok_start_time

    lm = hand_landmarks.landmark

    thumb_tip = lm[4]
    index_tip = lm[8]
    middle_tip = lm[12]
    ring_tip = lm[16]
    pinky_tip = lm[20]

    dist_thumb_index = math.hypot(
        thumb_tip.x - index_tip.x,
        thumb_tip.y - index_tip.y
    )

    touching = dist_thumb_index < 0.05

    fingers_extended = (
        middle_tip.y < lm[10].y and
        ring_tip.y < lm[14].y and
        pinky_tip.y < lm[18].y
    )

    valid_ok = touching and fingers_extended

    if valid_ok:
        if ok_start_time is None:
            ok_start_time = time.time()
        elif time.time() - ok_start_time > 0.8:
            ok_start_time = None
            return True
    else:
        ok_start_time = None

    return False


# ========================
# Main Loop
# ========================
threshold = 0.1
last_move_time = time.time()
move_delay = 0.12

running = True
while running:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # ========================
    # START SCREEN
    # ========================
    if waiting_start:
        draw_start_screen()

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            if is_ok_gesture(hand):
                time.sleep(0.5)
                reset_game()
                waiting_start = False

        cv2.imshow("Camera", img)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if cv2.waitKey(1) & 0xFF == 27:
            break

        continue

    # ========================
    # GAME OVER
    # ========================
    if game_over:
        draw_game_over()

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            if is_ok_gesture(hand):
                time.sleep(0.5)
                waiting_start = True

        cv2.imshow("Camera", img)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if cv2.waitKey(1) & 0xFF == 27:
            break

        continue

    # ========================
    # NORMAL GAME
    # ========================
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm = handLms.landmark

            wrist = lm[0]
            index_tip = lm[8]

            dx = index_tip.x - wrist.x
            dy = index_tip.y - wrist.y

            new_dir = direction

            if abs(dx) > abs(dy):
                if dx > threshold:
                    new_dir = "RIGHT"
                elif dx < -threshold:
                    new_dir = "LEFT"
            else:
                if dy > threshold:
                    new_dir = "DOWN"
                elif dy < -threshold:
                    new_dir = "UP"

            opposite = {
                "UP": "DOWN",
                "DOWN": "UP",
                "LEFT": "RIGHT",
                "RIGHT": "LEFT"
            }

            if new_dir != opposite[direction]:
                direction = new_dir

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

    # Move snake
    if time.time() - last_move_time > move_delay:
        move_snake()
        last_move_time = time.time()

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