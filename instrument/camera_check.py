import cv2
import time

CAMERA_INDEX = 4 # Use the confirmed index for your /dev/video5

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Error: Could not open camera with index {CAMERA_INDEX}. Exiting.")
    exit()

print(f"Camera opened successfully at index {CAMERA_INDEX}. Attempting to display video.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame. Exiting.")
            break

        cv2.imshow('Simple Camera Test', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except Exception as e:
    print(f"An error occurred during video display: {e}")
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Camera test finished.")