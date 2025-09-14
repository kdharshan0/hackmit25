import cv2
from ultralytics import YOLO
import time

# Load your trained model
model = YOLO("runs/pose/train/weights/best.pt")

# RTMP stream URL from MediaMTX
rtmp_url = "rtmp://localhost:1935/s/streamKey"
cap = cv2.VideoCapture(rtmp_url)

start_time = time.time()

frame_count = 0
print_interval = 30  # print every 30 frames

if not cap.isOpened():
    print("Error: Could not open RTMP stream")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Run YOLO on the frame
    results = model(frame)

    # Draw overlay
    annotated_frame = results[0].plot()

    # Compute elapsed time
    elapsed = time.time() - start_time

    # Print every N frames
    if frame_count % print_interval == 0:
        print(f"[{elapsed:.2f}s] Frame {frame_count}, Detections: {len(results[0].boxes)}")

    frame_count += 1

    # Display locally
    cv2.imshow("YOLO Overlay", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
