import os
import sys
import time
import cv2
import numpy as np
import subprocess
from edge_impulse_linux.runner import ImpulseRunner

# Settings
model_file = "modefied.eim"
draw_fps = True
res_width = 96
res_height = 96
rotation = 0
img_width = 28
img_height = 28
fps = 0

def print_available_controls():
    """Print all available camera controls"""
    try:
        result = subprocess.run([
            "v4l2-ctl",
            "-d", "/dev/video0",
            "--list-ctrls"
        ], capture_output=True, text=True, check=True)
        print("\nAvailable Camera Controls:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get camera controls: {e}")

def set_control(control_name, value):
    """Set a camera control value"""
    try:
        subprocess.run([
            "v4l2-ctl",
            "-d", "/dev/video0",
            "-c", f"{control_name}={value}"
        ], check=True)
        print(f"Set {control_name} to {value}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set {control_name}: {e}")

# Initialize camera with GStreamer
pipeline = (
    f"v4l2src device=/dev/video0 ! "
    f"video/x-raw,width={res_width},height={res_height},framerate=30/1 ! "
    "videoconvert ! "
    "video/x-raw,format=BGR ! "
    "appsink drop=1"
)

# Initialize Edge Impulse
dir_path = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(dir_path, model_file)
runner = ImpulseRunner(model_path)

try:
    model_info = runner.init()
    print("Model name:", model_info['project']['name'])
    print("Model owner:", model_info['project']['owner'])
except Exception as e:
    print("ERROR: Could not initialize model")
    print("Exception:", e)
    if runner:
        runner.stop()
    sys.exit(1)

# Initialize camera
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
if not cap.isOpened():
    print("ERROR: Could not open camera with GStreamer pipeline")
    runner.stop()
    sys.exit(1)

# Print available controls at startup
print_available_controls()

print("\nStreaming - Press 'q' to quit")
print("Available controls:")
print("1. Brightness: 'b'/'B' (decrease/increase)")
print("2. Contrast: 'c'/'C'")
print("3. Saturation: 's'/'S'")
print("4. Sharpness: 'h'/'H'")
print("5. Exposure: 'e'/'E'")

# Initial values
brightness = 50
contrast = 0
saturation = 0
sharpness = 0
exposure = 1000

try:
    while True:
        # Handle key presses
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('b'):  # Decrease brightness
            brightness = max(brightness - 5, 0)
            set_control("brightness", brightness)
        elif key == ord('B'):  # Increase brightness
            brightness = min(brightness + 5, 100)
            set_control("brightness", brightness)
        elif key == ord('c'):  # Decrease contrast
            contrast = max(contrast - 5, -100)
            set_control("contrast", contrast)
        elif key == ord('C'):  # Increase contrast
            contrast = min(contrast + 5, 100)
            set_control("contrast", contrast)
        elif key == ord('s'):  # Decrease saturation
            saturation = max(saturation - 5, -100)
            set_control("saturation", saturation)
        elif key == ord('S'):  # Increase saturation
            saturation = min(saturation + 5, 100)
            set_control("saturation", saturation)
        elif key == ord('h'):  # Decrease sharpness
            sharpness = max(sharpness - 5, -100)
            set_control("sharpness", sharpness)
        elif key == ord('H'):  # Increase sharpness
            sharpness = min(sharpness + 5, 100)
            set_control("sharpness", sharpness)
        elif key == ord('e'):  # Decrease exposure
            exposure = max(exposure - 100, 1)
            set_control("exposure_time_absolute", exposure)
        elif key == ord('E'):  # Increase exposure
            exposure = min(exposure + 100, 10000)
            set_control("exposure_time_absolute", exposure)

        # Capture frame
        ret, img = cap.read()
        if not ret:
            print("Frame read error")
            break

        # Rotate image if needed
        if rotation == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif rotation == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Convert image to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize captured image
        img_resize = cv2.resize(img_gray, (img_width, img_height))
        
        # Prepare features for Edge Impulse
        features = np.reshape(img_resize, (img_width * img_height)) / 255.0
        features = features.tolist()
        
        # Perform inference
        res = None
        try:
            res = runner.classify(features)
        except Exception as e:
            print("ERROR: Could not perform inference")
            print("Exception:", e)
            continue
            
        # Display predictions
        if res is not None:
            predictions = res['result']['classification']
            max_label = max(predictions, key=predictions.get)
            max_val = predictions[max_label]
            
            # Draw prediction on frame
            cv2.putText(img, f"{max_label}: {max_val:.2f}",
                        (10, res_height - 10),
                        cv2.FONT_HERSHEY_PLAIN,
                        1,
                        (255, 255, 255),
                        1)
        
        # Draw framerate
        if draw_fps:
            cv2.putText(img, f"FPS: {fps:.1f}",
                        (10, 20),
                        cv2.FONT_HERSHEY_PLAIN,
                        1,
                        (255, 255, 255),
                        1)
        
        # Show the frame
        cv2.imshow("Edge Impulse Classification", img)

finally:
    cap.release()
    cv2.destroyAllWindows()
    runner.stop()