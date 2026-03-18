import cv2
import mediapipe as mp
import pygame
import random
import math
import time

# ========================
# MediaPipe Setup
# ========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
start_time = time.time()
base_fall_delay = 0.5
fall_delay = base_fall_delay
# ========================
# Pygame Setup
# ========================
pygame.init()
game_over = False
WIDTH, HEIGHT = 300, 600
BLOCK = 30
rotate_lock = False
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Tetris")

clock = pygame.time.Clock()

# ========================
# Tetris Shapes
# ========================
SHAPES = [
    ([[1,1,1,1]], (0,255,255)),        # I - Cyan
    ([[1,1],[1,1]], (255,255,0)),      # O - Yellow
    ([[0,1,0],[1,1,1]], (128,0,128)),  # T - Purple
    ([[1,0,0],[1,1,1]], (0,0,255)),    # J - Blue
    ([[0,0,1],[1,1,1]], (255,165,0)),  # L - Orange
    ([[1,1,0],[0,1,1]], (0,255,0)),    # S - Green
    ([[0,1,1],[1,1,0]], (255,0,0)),    # Z - Red
]
# ========================
# Game State
# ========================
grid = [[None]*10 for _ in range(20)]

def new_piece():
    shape, color = random.choice(SHAPES)
    return {
        "shape": shape,
        "color": color,
        "x": 3,
        "y": 0
    }

piece = new_piece()

# ========================
# Helpers
# ========================
def draw_grid():
    win.fill((0,0,0))

    # Draw locked blocks
    for y in range(20):
        for x in range(10):
            if grid[y][x]:
                pygame.draw.rect(
                    win,
                    grid[y][x],  # use stored color
                    (x*BLOCK, y*BLOCK, BLOCK, BLOCK)
                )

    # Draw current piece
    for y,row in enumerate(piece["shape"]):
        for x,val in enumerate(row):
            if val:
                pygame.draw.rect(
                    win,
                    piece["color"],
                    ((piece["x"]+x)*BLOCK,
                     (piece["y"]+y)*BLOCK,
                     BLOCK, BLOCK)
                )

    pygame.display.update()

def valid_move(px, py, shape):
    for y,row in enumerate(shape):
        for x,val in enumerate(row):
            if val:
                nx = px + x
                ny = py + y
                if nx < 0 or nx >= 10 or ny >= 20:
                    return False
                if ny >= 0 and grid[ny][nx]:
                    return False
    return True

def lock_piece():
    global piece, game_over

    for y,row in enumerate(piece["shape"]):
        for x,val in enumerate(row):
            if val:
                py = piece["y"] + y

                if py < 1:
                    game_over = True

                grid[py][piece["x"]+x] = piece["color"]

    clear_lines()   

    piece = new_piece()

def rotate(shape):
    return list(zip(*shape[::-1]))


def draw_game_over():
    win.fill((0,0,0))
    font = pygame.font.SysFont(None, 50)
    text = font.render("GAME OVER", True, (255,0,0))
    win.blit(text, text.get_rect(center=(WIDTH//2, HEIGHT//2)))
    pygame.display.update()

# ========================
# Gesture Detection
# ========================
def is_fist(hand):
    lm = hand.landmark

    return (
        lm[8].y > lm[6].y and
        lm[12].y > lm[10].y and
        lm[16].y > lm[14].y and
        lm[20].y > lm[18].y
    )

def get_hand_angle(hand):
    lm = hand.landmark
    wrist = lm[0]
    index = lm[8]

    angle = math.degrees(math.atan2(
        index.y - wrist.y,
        index.x - wrist.x
    ))
    return angle

clap_prev_dist = None
clap_time = 0

clap_ready = False
last_clap_time = 0

def detect_clap(hands_landmarks):
    global clap_ready, last_clap_time

    if len(hands_landmarks) < 2:
        clap_ready = False
        return False

    h1 = hands_landmarks[0].landmark[0]
    h2 = hands_landmarks[1].landmark[0]

    dist = math.hypot(h1.x - h2.x, h1.y - h2.y)
    now = time.time()

    if dist > 0.35:
        clap_ready = True

    if clap_ready and dist < 0.15 and (now - last_clap_time > 0.5):
        clap_ready = False
        last_clap_time = now
        return True

    return False


def clear_lines():
    global grid

    new_grid = [row for row in grid if any(cell is None for cell in row)]
    cleared = 20 - len(new_grid)

    # Add empty rows at top
    for _ in range(cleared):
        new_grid.insert(0, [None]*10)

    grid = new_grid
# ========================
# Main Loop
# ========================
fall_time = time.time()
fall_delay = 0.5

last_move = 0
move_delay = 0.25

last_rotate = 0
rotate_delay = 0.4

running = True
while running:
    _, img = cap.read()
    img = cv2.flip(img, 1)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    move_left = False
    move_right = False
    rotate_now = False
    hard_drop = False

    elapsed = time.time() - start_time
    speed_multiplier = 1.2 ** int(elapsed // 20)
    fall_delay = base_fall_delay / speed_multiplier

    if results.multi_hand_landmarks:
        hands_list = results.multi_hand_landmarks

        # Detect clap
        if detect_clap(hands_list):
            hard_drop = True

        for hand in hands_list:
            lm = hand.landmark
            wrist_x = lm[0].x

            fist = is_fist(hand)

            if fist:
                if wrist_x < 0.5:
                    move_left = True
                else:
                    move_right = True

            angle = get_hand_angle(hand)
            both_fists = False

            if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
                h1, h2 = results.multi_hand_landmarks

                if is_fist(h1) and is_fist(h2):
                    both_fists = True

                    # ROTATION (both fists)
            if both_fists and not rotate_lock:
                new_shape = rotate(piece["shape"])
                if valid_move(piece["x"], piece["y"], new_shape):
                    piece["shape"] = new_shape
                rotate_lock = True

            if not both_fists:
                rotate_lock = False

            mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)

        if game_over:
            draw_game_over()
            continue

    # ========================
    # Apply Gestures
    # ========================
    now = time.time()

    if move_left and not move_right and now - last_move > move_delay:
        if valid_move(piece["x"]-1, piece["y"], piece["shape"]):
            piece["x"] -= 1
        last_move = now

    if move_right and not move_left and now - last_move > move_delay:
        if valid_move(piece["x"]+1, piece["y"], piece["shape"]):
            piece["x"] += 1
        last_move = now

    if rotate_now and now - last_rotate > rotate_delay:
        new_shape = rotate(piece["shape"])
        if valid_move(piece["x"], piece["y"], new_shape):
            piece["shape"] = new_shape
        last_rotate = now

    if hard_drop:
        while valid_move(piece["x"], piece["y"]+1, piece["shape"]):
            piece["y"] += 1
        lock_piece()

    # ========================
    # Gravity
    # ========================
    if time.time() - fall_time > fall_delay:
        if valid_move(piece["x"], piece["y"]+1, piece["shape"]):
            piece["y"] += 1
        else:
            lock_piece()
        fall_time = time.time()

    # ========================
    # Draw
    # ========================
    draw_grid()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    cv2.imshow("Camera", img)
    if cv2.waitKey(1) & 0xFF == 27:
        break

    clock.tick(60)

cap.release()
cv2.destroyAllWindows()
pygame.quit()