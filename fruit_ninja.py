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
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Optimization to reduce camera lag

# ========================
# PYGAME SETUP
# ========================
pygame.init()

WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture Fruit Ninja")

clock = pygame.time.Clock()

# Colors
BG = (30, 30, 40)
WHITE = (255, 255, 255)
FRUIT_COLORS = [(255, 100, 100), (255, 200, 100), (100, 255, 100)]
BLADE_COLOR = (200, 200, 255)

font = pygame.font.SysFont("Segoe UI", 28, bold=True)
big_font = pygame.font.SysFont("Segoe UI", 60, bold=True)

# ========================
# GAME STATE
# ========================
class Fruit:
    def __init__(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = HEIGHT + 20
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-16, -11) # Pop up speed
        self.radius = random.randint(20, 35)
        self.color = random.choice(FRUIT_COLORS)
        self.sliced = False
        self.off_screen = False

    def update(self):
        self.vy += 0.4  # Gravity
        self.x += self.vx
        self.y += self.vy

        # Mark as off-screen only once it falls back down past the bottom
        if self.vy > 0 and self.y > HEIGHT + 50:
            self.off_screen = True

    def draw(self):
        pygame.draw.circle(win, self.color, (int(self.x), int(self.y)), self.radius)


def reset_game():
    global fruits, score, misses, game_over, trail  # Add trail to the global list
    fruits = []
    trail = []  # Initialize it as an empty list instead of trail.clear()
    score = 0
    misses = 0
    game_over = False

reset_game()

# ========================
# GESTURES
# ========================
ok_start_time = 0

def is_ok_gesture(hand_landmarks):
    global ok_start_time
    lm = hand_landmarks.landmark
    dist = math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y)
    
    fingers_extended = lm[12].y < lm[10].y and lm[16].y < lm[14].y and lm[20].y < lm[18].y
    
    if dist < 0.05 and fingers_extended:
        if ok_start_time == 0: ok_start_time = time.time()
        elif time.time() - ok_start_time > 0.8:
            ok_start_time = 0
            return True
    else:
        ok_start_time = 0
    return False

def is_pointing_gesture(hand_landmarks):
    """Checks if index is extended and others are folded, regardless of hand rotation."""
    lm = hand_landmarks.landmark
    wrist = lm[0]

    # Helper to calculate distance between two points
    def get_dist(p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    # A finger is extended if its tip is further from the wrist than its middle joint
    index_extended = get_dist(lm[8], wrist) > get_dist(lm[6], wrist)
    
    # A finger is folded if its tip is closer to the wrist than its middle joint
    middle_folded = get_dist(lm[12], wrist) < get_dist(lm[10], wrist)
    ring_folded = get_dist(lm[16], wrist) < get_dist(lm[14], wrist)
    pinky_folded = get_dist(lm[20], wrist) < get_dist(lm[18], wrist)

    return index_extended and middle_folded and ring_folded and pinky_folded    

# ========================
# SLICE TRACKING
# ========================
trail = []
MAX_TRAIL = 8

def update_trail(x, y):
    trail.append((x, y))
    if len(trail) > MAX_TRAIL:
        trail.pop(0)

def draw_trail():
    if len(trail) > 1:
        # Draw a line that gets thicker towards the finger
        for i in range(1, len(trail)):
            thickness = int((i / len(trail)) * 8) + 1
            pygame.draw.line(win, BLADE_COLOR, trail[i-1], trail[i], thickness)

# ========================
# COLLISION
# ========================
def line_circle_collision(p1, p2, cx, cy, r):
    px, py = p1
    qx, qy = p2
    dx, dy = qx - px, qy - py

    if dx == 0 and dy == 0: return False

    t = max(0, min(1, ((cx - px)*dx + (cy - py)*dy) / (dx*dx + dy*dy)))
    closest_x = px + t * dx
    closest_y = py + t * dy

    return math.hypot(cx - closest_x, cy - closest_y) < r

# ========================
# DRAWING
# ========================
def draw():
    win.fill(BG)

    for fruit in fruits:
        fruit.draw()

    draw_trail()

    # UI
    score_txt = font.render(f"Score: {score}", True, WHITE)
    miss_txt = font.render(f"Misses: {misses}/5", True, (255, 100, 100))
    win.blit(score_txt, (20, 20))
    win.blit(miss_txt, (20, 60))

    pygame.display.update()

def draw_game_over():
    win.fill(BG)
    text1 = big_font.render("GAME OVER", True, (255, 80, 80))
    text2 = font.render(f"Final Score: {score}", True, WHITE)
    text3 = font.render("Make OK sign to restart", True, (200, 200, 200))

    win.blit(text1, text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
    win.blit(text2, text2.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))
    win.blit(text3, text3.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))
    pygame.display.update()

# ========================
# MAIN LOOP
# ========================
spawn_timer = 0
running = True

while running:
    success, img = cap.read()
    if not success: continue
    
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # -------------------------
    # GAME OVER STATE
    # -------------------------
    if game_over:
        draw_game_over()
        if results.multi_hand_landmarks:
            if is_ok_gesture(results.multi_hand_landmarks[0]):
                time.sleep(0.5)
                reset_game()

        cv2.imshow("Camera", img)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
        if cv2.waitKey(1) & 0xFF == 27: break
        continue

    # -------------------------
    # NORMAL GAME STATE
    # -------------------------
    blade_active = False

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        
        # Check if user is pointing
        if is_pointing_gesture(hand):
            blade_active = True
            index_tip = hand.landmark[8]
            x = int(index_tip.x * WIDTH)
            y = int(index_tip.y * HEIGHT)
            update_trail(x, y)
            
            # Draw a dot on the camera feed to show tracking
            mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)
            
    # Shrink the trail smoothly if blade is not active
    if not blade_active and len(trail) > 0:
        trail.pop(0)

    # Spawning
    spawn_timer += 1
    if spawn_timer > 45:  # Slightly slower spawn rate
        fruits.append(Fruit())
        spawn_timer = 0

    # ========================
    # COLLISION (SLICE)
    # ========================
    if blade_active and len(trail) >= 2:
        for fruit in fruits:
            if not fruit.sliced and not fruit.off_screen:
                # Check collision against every segment of the trail for fast swipes
                for i in range(1, len(trail)):
                    p1 = trail[i-1]
                    p2 = trail[i]
                    if line_circle_collision(p1, p2, fruit.x, fruit.y, fruit.radius):
                        fruit.sliced = True
                        score += 1
                        break # Stop checking this fruit once it's sliced

    # Cleanup & Updating state
    active_fruits = []
    for fruit in fruits:
        fruit.update()
        
        if fruit.sliced:
            # We don't add sliced fruits back to active_fruits (they vanish)
            continue
            
        elif fruit.off_screen:
            # Only counts as a miss if it fell off without being sliced
            misses += 1
            if misses >= 5:
                game_over = True
                
        else:
            active_fruits.append(fruit)

    fruits = active_fruits

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