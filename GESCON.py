import cv2
import mediapipe as mp
import pyautogui
import time
import STT
import threading

# Set desired video resolution to 1080p
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)

# Screen and interaction zone setup
screen_width, screen_height = pyautogui.size()
screen_aspect_ratio = screen_width / screen_height

# Interaction and gesture zones
interaction_box_margin = 50  # Margin for smaller green box
gesture_box_margin = 200     # Margin for smaller yellow box

# Updated interaction box dimensions
box_width = VIDEO_WIDTH - interaction_box_margin
box_height = int(box_width / screen_aspect_ratio)
if box_height > (VIDEO_HEIGHT - interaction_box_margin):
    box_height = VIDEO_HEIGHT - interaction_box_margin
    box_width = int(box_height * screen_aspect_ratio)

x1, y1 = (VIDEO_WIDTH - box_width) // 2, (VIDEO_HEIGHT - box_height) // 2
x2, y2 = x1 + box_width, y1 + box_height

# Updated gesture box dimensions
gesture_x1 = max(0, x1 - gesture_box_margin)
gesture_y1 = max(0, y1 - gesture_box_margin)
gesture_x2 = min(VIDEO_WIDTH, x2 + gesture_box_margin)
gesture_y2 = min(VIDEO_HEIGHT, y2 + gesture_box_margin)

# Initialize Mediapipe for hand tracking
hand_detector = mp.solutions.hands.Hands(max_num_hands=1)
drawing_utils = mp.solutions.drawing_utils

# Variables for cursor movement and actions
smooth_x, smooth_y = 0, 0
smoothing_factor = 0.35
dragging = False
last_action_time = 0
recent_apps_open = False  # Flag to track the state of recent apps
action_delay = 1  # Delay between actions to prevent accidental gestures

# Timer for detecting long gesture
gesture_start_time = None  # To track when the index and middle fingers were extended

# Function to count raised fingers
def count_fingers(landmarks):
    fingers = []
    # Thumb
    fingers.append(landmarks[4].x < landmarks[3].x)
    # Fingers (index to pinky)
    fingers.extend([landmarks[i].y < landmarks[i - 2].y for i in [8, 12, 16, 20]])
    return fingers

# Function to perform action with cooldown
def perform_action(action_func, gesture_time):
    global last_action_time
    if time.time() - last_action_time > action_delay:
        action_func()
        last_action_time = gesture_time

while True:
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hand_detector.process(rgb_frame)
    hands = results.multi_hand_landmarks

    if hands:
        hand = hands[0]
        drawing_utils.draw_landmarks(frame, hand)
        landmarks = hand.landmark

        # Index fingertip position for cursor movement
        index_x, index_y = int(landmarks[8].x * VIDEO_WIDTH), int(landmarks[8].y * VIDEO_HEIGHT)

        # Check if the index finger is inside the interaction box
        if x1 <= index_x <= x2 and y1 <= index_y <= y2:
            target_x = (index_x - x1) * (screen_width / box_width)
            target_y = (index_y - y1) * (screen_height / box_height)
            smooth_x += (target_x - smooth_x) * smoothing_factor
            smooth_y += (target_y - smooth_y) * smoothing_factor
            pyautogui.moveTo(smooth_x, smooth_y)

        # Detect gesture based on finger count
        fingers = count_fingers(landmarks)
        gesture_time = time.time()

        # Detecting index and middle finger extension for single/double click
        if fingers[1] and fingers[2] and not fingers[3] and not fingers[4]:  # Index and middle extended
            if gesture_start_time is None:
                gesture_start_time = time.time()  # Start the timer
            elif time.time() - gesture_start_time > 1:  # If extended for more than 1 second
                # Perform double click
                perform_action(lambda: pyautogui.doubleClick(), gesture_time)
                gesture_start_time = None  # Reset timer
        else:
            # If fingers are no longer extended
            if gesture_start_time is not None and time.time() - gesture_start_time <= 1:
                # Perform single click if duration is less than 1 second
                perform_action(lambda: pyautogui.click(), gesture_time)
            gesture_start_time = None  # Reset timer

        if fingers.count(True) == 2 and fingers[1] and fingers[2]:
            pass  # Logic for the index and middle fingers was handled above

        elif fingers.count(True) == 1:  # Single finger gesture for cursor movement
            dragging = False

        elif fingers.count(True) == 3:  # Three fingers for right-clickhello how r u
            perform_action(lambda: pyautogui.rightClick(), gesture_time)

        elif fingers.count(True) == 4 and fingers[1] and fingers[2] and fingers[3] and fingers[4]:  # Four fingers for scroll
            if time.time() - last_action_time > 0.1:
                STT.main()
                last_action_time = time.time()

        elif fingers.count(True) == 5:  # Five fingers for recent apps toggle
            if recent_apps_open:
                perform_action(lambda: pyautogui.hotkey('win', 'tab'), gesture_time)
                recent_apps_open = False
                time.sleep(1)
            else:
                perform_action(lambda: pyautogui.hotkey('win', 'tab'), gesture_time)
                recent_apps_open = True
                time.sleep(1)

        elif fingers.count(True) == 0:  # Closed fist for dragging
            if not dragging:
                pyautogui.mouseDown()
                dragging = True
            else:
                if fingers.count(True) != 0:
                    pyautogui.mouseUp()
                    dragging = False

    # Draw interaction and gesture boxes on the frame
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box
    cv2.rectangle(frame, (gesture_x1, gesture_y1), (gesture_x2, gesture_y2), (0, 255, 255), 1)  # Yellow box

    # Display frame
    cv2.imshow("Gesture Controlled Mouse", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
