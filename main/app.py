import cv2
import mediapipe as mp
import pyautogui
import math
import time
import numpy as np
from keyboard_ctrl import SpeechController

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Get screen size
screen_width, screen_height = pyautogui.size()

# Disable the fail-safe feature
pyautogui.FAILSAFE = False

# Create a low-pass filter for smoother cursor movement
class LowPassFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.value = None

    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

cursor_filter_x = LowPassFilter(alpha=0.5)
cursor_filter_y = LowPassFilter(alpha=0.5)

def map_to_screen(x, y, frame_width, frame_height):
    return (
        int(cursor_filter_x.update(x * screen_width * 1.5)),
        int(cursor_filter_y.update(y * screen_height * 1.5))
    )

def is_finger_extended(finger_tip, finger_pip, hand_landmarks):
    return hand_landmarks.landmark[finger_tip].y < hand_landmarks.landmark[finger_pip].y

def is_fist_closed(hand_landmarks):
    fingers = [
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]
    finger_mcp = [
        mp_hands.HandLandmark.INDEX_FINGER_MCP,
        mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
        mp_hands.HandLandmark.RING_FINGER_MCP,
        mp_hands.HandLandmark.PINKY_MCP
    ]
    return all(hand_landmarks.landmark[tip].y > hand_landmarks.landmark[mcp].y for tip, mcp in zip(fingers, finger_mcp))

# Initialize speech controller
speech_controller = SpeechController()
speech_controller.start()

# Variables for click cooldown, drag state, and scroll state
last_action_time = 0
action_cooldown = 0.2
is_dragging = False
middle_finger_was_extended = False
scrolling = False
last_y_position = None

running = True
while running:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

            fist_closed = is_fist_closed(hand_landmarks)
            index_extended = is_finger_extended(mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_PIP, hand_landmarks)
            middle_extended = is_finger_extended(mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_PIP, hand_landmarks)
            ring_extended = is_finger_extended(mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_PIP, hand_landmarks)
            pinky_extended = is_finger_extended(mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_PIP, hand_landmarks)

            index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            if fist_closed or (index_extended and middle_extended and not ring_extended and not pinky_extended):
                x, y = map_to_screen(index_mcp.x, index_mcp.y, frame.shape[1], frame.shape[0])
                pyautogui.moveTo(x, y, duration=0)

            current_time = time.time()

            if fist_closed and not is_dragging and current_time - last_action_time > action_cooldown:
                pyautogui.mouseDown(button='left')
                is_dragging = True
                last_action_time = current_time
            elif not fist_closed and is_dragging and current_time - last_action_time > action_cooldown:
                pyautogui.mouseUp(button='left')
                is_dragging = False
                last_action_time = current_time

            if index_extended and not middle_extended and not ring_extended and not pinky_extended and current_time - last_action_time > action_cooldown:
                pyautogui.click(button='right')
                last_action_time = current_time

            if not middle_extended and middle_finger_was_extended and current_time - last_action_time > action_cooldown:
                pyautogui.click(button='right')
                last_action_time = current_time

            if index_extended and middle_extended:
                finger_distance = math.dist(
                    (hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x, hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y),
                    (hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x, hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y)
                )
                if finger_distance < 0.03 and current_time - last_action_time > action_cooldown:
                    pyautogui.click(button='left')
                    last_action_time = current_time

            if middle_extended and not index_extended and not ring_extended and not pinky_extended and current_time - last_action_time > action_cooldown:
                pyautogui.doubleClick(button='left')
                last_action_time = current_time

            finger_distance = math.dist(
                (index_tip.x, index_tip.y),
                (thumb_tip.x, thumb_tip.y)
            )
            if finger_distance < 0.03:
                if not scrolling:
                    scrolling = True
                    last_y_position = index_tip.y
                else:
                    scroll_amount = (index_tip.y - last_y_position) * frame.shape[0]
                    pyautogui.scroll(int(scroll_amount))
                    last_y_position = index_tip.y
            else:
                if scrolling:
                    scrolling = False

            middle_finger_was_extended = middle_extended

    cv2.imshow('Virtual Mouse and Keyboard', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False

cap.release()
cv2.destroyAllWindows()
speech_controller.stop()