import cv2
import mediapipe as mp
import pygame
import time

# ========================
# Gesture Detection Setup
# ========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
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

snake = [(300, 300)]
direction = "RIGHT"
food = (200, 200)

font = pygame.font.SysFont(None, 36)

# ========================
# Helpers
# ========================
def draw():
    win.fill((0, 0, 0))

    # snake
    for s in snake:
        pygame.draw.rect(win, (0, 255, 0), (*s, block, block))

    # food
    pygame.draw.rect(win, (255, 0, 0), (*food, block, block))

    # direction text
    txt = font.render(direction, True, (255, 255, 255))
    win.blit(txt, (10, 10))

    pygame.display.update()


def move_snake():
    global food

    x, y = snake[0]

    if direction == "UP":
        y -= block
    elif direction == "DOWN":
        y += block
    elif direction == "LEFT":
        x -= block
    elif direction == "RIGHT":
        x += block

    new_head = (x, y)
    snake.insert(0, new_head)

    if new_head == food:
        import random
        food = (random.randrange(0, WIDTH, block),
                random.randrange(0, HEIGHT, block))
    else:
        snake.pop()


# ========================
# Main Loop
# ========================
prev_direction = direction
threshold = 0.1
last_move_time = time.time()
move_delay = 0.15  # smooth movement

running = True
while running:
    # -------- Gesture Detection --------
    success, img = cap.read()
    img = cv2.flip(img, 1)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

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

            # prevent instant reverse
            opposite = {
                "UP": "DOWN",
                "DOWN": "UP",
                "LEFT": "RIGHT",
                "RIGHT": "LEFT"
            }

            if new_dir != opposite[direction]:
                direction = new_dir

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Camera", img)

    # -------- Snake Logic --------
    if time.time() - last_move_time > move_delay:
        move_snake()
        last_move_time = time.time()

    # -------- Pygame Events --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw()
    clock.tick(60)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()