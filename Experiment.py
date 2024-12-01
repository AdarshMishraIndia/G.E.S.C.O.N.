import cv2
import mediapipe as mp
import pyautogui
import time

# Set desired video resolution
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)

# Screen dimensions
screen_width, screen_height = pyautogui.size()

# Initialize Mediapipe for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Cursor smoothing variables
smooth_x, smooth_y = 0, 0
smoothing_factor = 0.35  # Adjust for smoothness (lower = smoother but slower)

while True:
    # Read and process video frame
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get index fingertip position
            index_finger_tip = hand_landmarks.landmark[8]  # Index finger tip
            index_x = int(index_finger_tip.x * VIDEO_WIDTH)
            index_y = int(index_finger_tip.y * VIDEO_HEIGHT)

            # Map to screen dimensions
            screen_x = int(index_finger_tip.x * screen_width)
            screen_y = int(index_finger_tip.y * screen_height)

            # Smooth cursor movement
            smooth_x += (screen_x - smooth_x) * smoothing_factor
            smooth_y += (screen_y - smooth_y) * smoothing_factor

            # Move cursor
            pyautogui.moveTo(smooth_x, smooth_y)

            # Draw hand landmarks (optional, for visualization)
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Display frame
    cv2.imshow("Index Finger Tracking", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
