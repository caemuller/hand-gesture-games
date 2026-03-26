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
# Optimization: Ask OpenCV to only keep the newest frame, reducing latency
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

# ========================
# Snake Game Setup
# ========================
pygame.init()

WIDTH, HEIGHT = 500, 500
block = 25  # Grid size (20x20 grid)

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Google-Style Gesture Snake")
clock = pygame.time.Clock()

font = pygame.font.SysFont("comicsansms", 28, bold=True)
big_font = pygame.font.SysFont("comicsansms", 50, bold=True)

# Colors
BG1 = (170, 215, 81)       
BG2 = (162, 209, 73)       
SNAKE_BODY = (69, 115, 232) 
SNAKE_HEAD = (50, 90, 200)  
APPLE_RED = (231, 71, 29)   

# ========================
# OPTIMIZATION: Pre-Rendered Surfaces
# ========================
# 1. Pre-draw the background grid ONCE to save CPU
bg_surface = pygame.Surface((WIDTH, HEIGHT))
for row in range(HEIGHT // block):
    for col in range(WIDTH // block):
        color = BG1 if (row + col) % 2 == 0 else BG2
        pygame.draw.rect(bg_surface, color, (col * block, row * block, block, block))

# 2. Pre-create the transparent overlay ONCE
overlay_surface = pygame.Surface((WIDTH, HEIGHT))
overlay_surface.set_alpha(150)
overlay_surface.fill((0, 0, 0))


# ========================
# Game State
# ========================
def reset_game():
    global snake, direction, food, score, game_over
    snake = [(250, 250), (225, 250), (200, 250), (175, 250)] 
    direction = "RIGHT"
    score = 0
    game_over = False
    spawn_food()

def spawn_food():
    global food
    while True:
        food = (random.randrange(0, WIDTH, block),
                random.randrange(0, HEIGHT, block))
        if food not in snake:
            break

waiting_start = True
reset_game()

# ========================
# Drawing Helpers
# ========================
def draw_apple(x, y):
    center_x, center_y = x + block // 2, y + block // 2
    radius = int(block * 0.45)
    pygame.draw.circle(win, APPLE_RED, (center_x, center_y), radius)
    pygame.draw.rect(win, (139, 69, 19), (center_x - 2, center_y - radius - 4, 4, 8))
    pygame.draw.ellipse(win, (34, 139, 34), (center_x + 2, center_y - radius - 4, 8, 4))

def draw_snake():
    n = len(snake)
    for i in range(n):
        thickness_ratio = 1.0 - (i / max(1, n - 1)) * 0.6 
        radius = max(3, int((block // 2.1) * thickness_ratio))
        
        center = (snake[i][0] + block // 2, snake[i][1] + block // 2)
        color = SNAKE_HEAD if i == 0 else SNAKE_BODY
        
        pygame.draw.circle(win, color, center, radius)
        
        if i < n - 1:
            next_center = (snake[i+1][0] + block // 2, snake[i+1][1] + block // 2)
            if abs(center[0] - next_center[0]) <= block and abs(center[1] - next_center[1]) <= block:
                next_ratio = 1.0 - ((i + 1) / max(1, n - 1)) * 0.6
                next_radius = max(3, int((block // 2.1) * next_ratio))
                line_width = radius + next_radius
                pygame.draw.line(win, SNAKE_BODY, center, next_center, line_width)

    head_center = (snake[0][0] + block // 2, snake[0][1] + block // 2)
    d = int(block * 0.25)
    
    eye_offset_1, eye_offset_2 = (0, 0), (0, 0)
    if direction == "UP": eye_offset_1, eye_offset_2 = (-d, -d), (d, -d)
    elif direction == "DOWN": eye_offset_1, eye_offset_2 = (-d, d), (d, d)
    elif direction == "LEFT": eye_offset_1, eye_offset_2 = (-d, -d), (-d, d)
    elif direction == "RIGHT": eye_offset_1, eye_offset_2 = (d, -d), (d, d)

    eye1_pos = (head_center[0] + eye_offset_1[0], head_center[1] + eye_offset_1[1])
    eye2_pos = (head_center[0] + eye_offset_2[0], head_center[1] + eye_offset_2[1])

    pygame.draw.circle(win, (255, 255, 255), eye1_pos, 4)
    pygame.draw.circle(win, (255, 255, 255), eye2_pos, 4)
    pygame.draw.circle(win, (0, 0, 0), eye1_pos, 2)
    pygame.draw.circle(win, (0, 0, 0), eye2_pos, 2)

def draw_overlay(text1_str, text2_str, color1):
    # Simply blit the pre-made surface instead of creating a new one
    win.blit(overlay_surface, (0, 0))

    text1 = big_font.render(text1_str, True, color1)
    text2 = font.render(text2_str, True, (255, 255, 255))
    shadow = big_font.render(text1_str, True, (0, 0, 0))
    
    win.blit(shadow, shadow.get_rect(center=(WIDTH//2 + 3, HEIGHT//2 - 47)))
    win.blit(text1, text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
    win.blit(text2, text2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
    pygame.display.update()

def draw():
    # Blit the pre-rendered background instantly
    win.blit(bg_surface, (0, 0))
    
    draw_apple(*food)
    draw_snake()

    score_txt = font.render(f"Score: {score}", True, (255, 255, 255))
    shadow_txt = font.render(f"Score: {score}", True, (50, 50, 50))
    win.blit(shadow_txt, (12, 12))
    win.blit(score_txt, (10, 10))

    pygame.display.update()

# ========================
# Game & Gesture Logic
# ========================
def move_snake():
    global score, game_over
    x, y = snake[0]

    if direction == "UP": y -= block
    elif direction == "DOWN": y += block
    elif direction == "LEFT": x -= block
    elif direction == "RIGHT": x += block

    x %= WIDTH
    y %= HEIGHT
    new_head = (x, y)

    if new_head in snake:
        game_over = True
        return

    snake.insert(0, new_head)
    if new_head == food:
        score += 1
        spawn_food()
    else:
        snake.pop()

ok_start_time = 0
def is_ok_gesture(hand_landmarks):
    global ok_start_time
    lm = hand_landmarks.landmark
    thumb_tip, index_tip = lm[4], lm[8]
    middle_tip, ring_tip, pinky_tip = lm[12], lm[16], lm[20]

    dist_thumb_index = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
    touching = dist_thumb_index < 0.05

    fingers_extended = (
        middle_tip.y < lm[10].y and
        ring_tip.y < lm[14].y and
        pinky_tip.y < lm[18].y
    )

    if touching and fingers_extended:
        if ok_start_time == 0:
            ok_start_time = time.time()
        elif time.time() - ok_start_time > 0.8:
            ok_start_time = 0
            return True
    else:
        ok_start_time = 0

    return False

# ========================
# Main Loop
# ========================
threshold = 0.1
last_move_time = time.time()
move_delay = 0.22 

running = True
while running:
    success, img = cap.read()
    if not success: continue
    
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # -------------------------
    # START SCREEN
    # -------------------------
    if waiting_start:
        win.blit(bg_surface, (0, 0)) 
        draw_overlay("Gesture Snake", "Show 'OK' sign to start", (255, 215, 0))

        if results.multi_hand_landmarks:
            if is_ok_gesture(results.multi_hand_landmarks[0]):
                # Removed time.sleep(0.3) to prevent freezing
                reset_game()
                waiting_start = False

        cv2.imshow("Camera", img)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
        if cv2.waitKey(1) & 0xFF == 27: break
        continue

    # -------------------------
    # GAME OVER
    # -------------------------
    if game_over:
        win.blit(bg_surface, (0, 0))
        draw_snake() 
        draw_overlay("GAME OVER", f"Score: {score} | Show 'OK' to retry", (255, 50, 50))

        if results.multi_hand_landmarks:
            if is_ok_gesture(results.multi_hand_landmarks[0]):
                # Removed time.sleep(0.3) to prevent freezing
                waiting_start = True

        cv2.imshow("Camera", img)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
        if cv2.waitKey(1) & 0xFF == 27: break
        continue

    # -------------------------
    # NORMAL GAME
    # -------------------------
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm = handLms.landmark
            wrist, index_tip = lm[0], lm[8]

            dx = index_tip.x - wrist.x
            dy = index_tip.y - wrist.y
            new_dir = direction

            if abs(dx) > abs(dy):
                if dx > threshold: new_dir = "RIGHT"
                elif dx < -threshold: new_dir = "LEFT"
            else:
                if dy > threshold: new_dir = "DOWN"
                elif dy < -threshold: new_dir = "UP"

            opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
            
            if new_dir != opposite.get(direction, ""):
                direction = new_dir

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

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