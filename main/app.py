import cv2
import mediapipe as mp
import pyautogui
import math
import time

# Initialize MediaPipe Hands with optimized settings
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.8,  # Increase detection confidence
    min_tracking_confidence=0.8    # Increase tracking confidence
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize webcam
cap = cv2.VideoCapture(0)

# Get screen size
screen_width, screen_height = pyautogui.size()

# Disable the fail-safe feature
pyautogui.FAILSAFE = False

# Define a function to map hand coordinates to screen coordinates
def map_to_screen(x, y, frame_width, frame_height):
    return (
        int(x * screen_width),
        int(y * screen_height)
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

# Variables for click cooldown, drag state, and scroll state
last_action_time = 0
action_cooldown = 0.3  # reduced cooldown time
is_dragging = False
middle_finger_was_extended = False  # Track the previous state of the middle finger
scrolling = False
last_y_position = None

while True:
    # Read frame from webcam
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a later selfie-view display
    frame = cv2.flip(frame, 1)

    # Get frame dimensions
    frame_height, frame_width, _ = frame.shape

    # Convert the BGR image to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame and detect hands
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

            # Check hand gestures
            fist_closed = is_fist_closed(hand_landmarks)
            index_extended = is_finger_extended(mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_PIP, hand_landmarks)
            middle_extended = is_finger_extended(mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_PIP, hand_landmarks)
            ring_extended = is_finger_extended(mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_PIP, hand_landmarks)
            pinky_extended = is_finger_extended(mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_PIP, hand_landmarks)

            index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            # Move cursor if fist is closed or if index and middle are extended, and others are closed
            if fist_closed or (index_extended and middle_extended and not ring_extended and not pinky_extended):
                x, y = map_to_screen(index_mcp.x, index_mcp.y, frame_width, frame_height)
                pyautogui.moveTo(x, y)

            current_time = time.time()

            # Long left-click logic
            if fist_closed and not is_dragging and current_time - last_action_time > action_cooldown:
                pyautogui.mouseDown(button='left')
                is_dragging = True
                last_action_time = current_time
                print("Holding left click (fist closed)")  # Debug print
            elif not fist_closed and is_dragging and current_time - last_action_time > action_cooldown:
                pyautogui.mouseUp(button='left')
                is_dragging = False
                last_action_time = current_time
                print("Releasing left click (fist opened)")  # Debug print

            # Perform right-click if only index finger is extended
            if index_extended and not middle_extended and not ring_extended and not pinky_extended and current_time - last_action_time > action_cooldown:
                pyautogui.click(button='right')
                last_action_time = current_time
                print("Right click")  # Debug print

            # Perform right-click when middle finger is closed
            if not middle_extended and middle_finger_was_extended and current_time - last_action_time > action_cooldown:
                pyautogui.click(button='right')
                last_action_time = current_time
                print("Right click (middle finger closed)")  # Debug print

            # Perform left-click when index and middle finger tips touch
            if index_extended and middle_extended:
                finger_distance = math.dist(
                    (hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x, hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y),
                    (hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x, hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y)
                )
                if finger_distance < 0.03 and current_time - last_action_time > action_cooldown:
                    pyautogui.click(button='left')
                    last_action_time = current_time
                    print("Left click (index and middle fingers touched)")  # Debug print

            # Perform left double-click if only middle finger is extended
            if middle_extended and not index_extended and not ring_extended and not pinky_extended and current_time - last_action_time > action_cooldown:
                pyautogui.doubleClick(button='left')
                last_action_time = current_time
                print("Left double-click (only middle finger extended)")  # Debug print

            # Perform scrolling when index and thumb tips touch
            finger_distance = math.dist(
                (index_tip.x, index_tip.y),
                (thumb_tip.x, thumb_tip.y)
            )
            if finger_distance < 0.03:
                if not scrolling:
                    scrolling = True
                    last_y_position = index_tip.y
                    print("Scrolling started")  # Debug print
                else:
                    scroll_amount = (index_tip.y - last_y_position) * frame_height
                    pyautogui.scroll(int(scroll_amount))
                    last_y_position = index_tip.y
                    print(f"Scrolling: {scroll_amount}")  # Debug print
            else:
                if scrolling:
                    scrolling = False
                    print("Scrolling stopped")  # Debug print

            # Update the state of the middle finger
            middle_finger_was_extended = middle_extended

            # Debug information
            cv2.putText(frame, f"Fist closed: {fist_closed}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Is dragging: {is_dragging}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display the frame
    cv2.imshow('Virtual Mouse', frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close all windows
cap.release()
cv2.destroyAllWindows()