
A real-time hand gesture–controlled games using computer vision. Built with MediaPipe and OpenCV

## 🚀 Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your machine.

### 2. Install Dependencies
Open your terminal (or Command Prompt) and run:
```bash
pip install opencv-python mediapipe pygame
```
### 3. Clone the Repo
```bash
git clone https://github.com/caemuller/gesture-games.git
cd gesture-games
```


### 4. Running the Games
Launch the specific Python file for the game you want to play:

```python
python snake.py

python tetris.py

python fruit_ninja.py

python breakout.py
```

# 🐍 Snake (Gesture-Controlled)

### 🧠 Objective
Control the snake, eat food, and grow as long as possible without colliding with yourself.

---

### ✋ Controls

- 👆 **Pointing Direction (Index Finger)**  
  Move your hand relative to your wrist:
  - Up → Snake moves up  
  - Down → Snake moves down  
  - Left → Snake moves left  
  - Right → Snake moves right  

- 👌 **OK Gesture (Thumb + Index touching)**  
  - Start the game  
  - Restart after losing  

---

### ⚙️ Gameplay Notes

- The snake wraps around screen edges  
- Game ends if the snake collides with itself  
- You must **hold the OK gesture briefly** to trigger actions  

---

# 🧱 Tetris (Gesture-Controlled)

### 🧠 Objective
Arrange falling blocks to complete horizontal lines. Completed lines disappear and award space. The game ends when blocks reach the top.

---

### ✋ Controls

- ✊ **Left Hand Fist** → Move piece left  
- ✊ **Right Hand Fist** → Move piece right  
- ✊✊ **Both Fists** → Rotate piece (one rotation per gesture)  
- 👏 **Clap (hands apart → together)** → Hard drop (instantly place piece)

---

### ⚙️ Gameplay Mechanics

- 🧱 Includes all **7 classic Tetris pieces**, each with unique colors  
- 🧹 **Line Clearing**: Full horizontal rows are removed  
- ⏫ **Speed Increase**: Game speed increases by **1.5× every 20 seconds**  
- 💀 **Game Over**: Triggered when a piece locks at the top row  

---

### 🧠 Gesture Notes

- Movement requires **two hands visible**  
- Rotation only triggers when **both fists are closed simultaneously**  
- Clap detection requires:
  - Hands first apart  
  - Then quickly brought together  


---
