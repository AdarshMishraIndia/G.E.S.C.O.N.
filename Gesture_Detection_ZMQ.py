import cv2
import mediapipe as mp
import zmq
import pyautogui

# Initialize ZeroMQ for sending data
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.bind("tcp://127.0.0.1:5555")  # Server to send coordinates to C++

# Get native camera resolution and screen dimensions
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
VIDEO_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
VIDEO_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
screen_width, screen_height = pyautogui.size()
aspect_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

# Calculate box dimensions (60% of video feed size)
box_width = int(VIDEO_WIDTH * 0.6)
box_height = int(box_width / aspect_ratio)
x1, y1 = (VIDEO_WIDTH - box_width) // 2, (VIDEO_HEIGHT - box_height) // 2
x2, y2 = x1 + box_width, y1 + box_height

# Initialize Mediapipe for hand tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)

def map_to_screen(x, y):
    """Map coordinates within the box to the entire screen."""
    mapped_x = screen_width * (x - x1) / box_width
    mapped_y = screen_height * (y - y1) / box_height
    return int(mapped_x), int(mapped_y)

def is_palm_in_box(landmarks):
    """Check if wrist or MCP joints are inside the pink box."""
    palm_points = [
        landmarks[mp_hands.HandLandmark.WRIST],
        landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP],
        landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    ]
    for point in palm_points:
        px, py = int(point.x * VIDEO_WIDTH), int(point.y * VIDEO_HEIGHT)
        if x1 <= px <= x2 and y1 <= py <= y2:
            return True
    return False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    # Draw the pink box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 105, 180), 2)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            if is_palm_in_box(hand_landmarks.landmark):
                # Map index fingertip to screen coordinates
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                px, py = int(index_tip.x * VIDEO_WIDTH), int(index_tip.y * VIDEO_HEIGHT)
                screen_x, screen_y = map_to_screen(px, py)
                socket.send_json({"x": screen_x, "y": screen_y})  # Send data to C++
                print(f"Sending coordinates: ({screen_x}, {screen_y})")

    cv2.imshow("Camera Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
