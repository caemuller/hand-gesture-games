import cv2
import mediapipe as mp
import pyautogui

# Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

prev_direction = None
threshold = 0.1  # sensitivity

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    direction = None

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm = handLms.landmark

            wrist = lm[0]
            index_tip = lm[8]

            dx = index_tip.x - wrist.x
            dy = index_tip.y - wrist.y

            if abs(dx) > abs(dy):
                if dx > threshold:
                    direction = "RIGHT"
                elif dx < -threshold:
                    direction = "LEFT"
            else:
                if dy > threshold:
                    direction = "DOWN"
                elif dy < -threshold:
                    direction = "UP"

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

    # Send key only if changed
    if direction and direction != prev_direction:
        print(direction)

        if direction == "UP":
            pyautogui.press("up")
        elif direction == "DOWN":
            pyautogui.press("down")
        elif direction == "LEFT":
            pyautogui.press("left")
        elif direction == "RIGHT":
            pyautogui.press("right")

        prev_direction = direction

    cv2.imshow("Gesture Control", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
