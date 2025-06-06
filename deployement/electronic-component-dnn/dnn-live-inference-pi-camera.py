import os
import sys
import time
import cv2
import numpy as np
import subprocess
import select
from edge_impulse_linux.runner import ImpulseRunner

# Settings
model_file = "modefied.eim"            # Trained ML model from Edge Impulse
draw_fps = True                        # Draw FPS on screen
res_width = 96                         # Resolution for ML model (width)
res_height = 96                        # Resolution for ML model (height)
capture_width = 640                    # Camera capture width
capture_height = 480                   # Camera capture height
rotation = 0                           # Camera rotation (0, 90, 180, or 270)
img_width = 28                         # Resize width to this for inference
img_height = 28                        # Resize height to this for inference
fps = 30                               # Camera frames per second

def run_gstreamer_pipeline():
    command = [
        'gst-launch-1.0',
        'v4l2src', 'device=/dev/video0', '!',
        f'video/x-raw,width=96,height=96,framerate={fps}/1', '!',
        'videoconvert', '!',
        'video/x-raw,format=BGR', '!',
        'fdsink', 'fd=1'
    ]
    
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=capture_width*capture_height*3,
        universal_newlines=False
    )

# Initialize the model runner
dir_path = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(dir_path, model_file)
runner = ImpulseRunner(model_path)

try:
    # Print model information
    model_info = runner.init()
    print("Model name:", model_info['project']['name'])
    print("Model owner:", model_info['project']['owner'])
except Exception as e:
    print("ERROR: Could not initialize model")
    print("Exception:", e)
    if runner:
        runner.stop()
    sys.exit(1)

# Initialize GStreamer pipeline
process = run_gstreamer_pipeline()
poller = select.poll()
poller.register(process.stdout, select.POLLIN)

print("Streaming - Press 'q' to quit")
current_fps = 0

try:
    while True:
        # Get timestamp for calculating actual framerate
        timestamp = cv2.getTickCount()
        
        # Check if frame is available
        if not poller.poll(100):  # 100ms timeout
            continue
            
        # Read raw frame data
        raw_frame = process.stdout.read(capture_width*capture_height*3)
        if not raw_frame or len(raw_frame) != capture_width*capture_height*3:
            print("Frame read error")
            break

        # Convert to numpy array and reshape
        img = np.frombuffer(raw_frame, dtype=np.uint8)
        img = img.reshape((capture_height, capture_width, 3)).copy()


        # Rotate image if needed
        if rotation == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif rotation == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rotation != 0:
            print("ERROR: rotation not supported. Must be 0, 90, 180, or 270.")
            break

        # Convert image to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize captured image for model
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
                        (10, capture_height - 10),
                        cv2.FONT_HERSHEY_PLAIN,
                        1,
                        (255, 255, 255),
                        1)
        
        # Draw framerate
        if draw_fps:
            cv2.putText(img, f"FPS: {current_fps:.1f}",
                        (10, 20),
                        cv2.FONT_HERSHEY_PLAIN,
                        1,
                        (255, 255, 255),
                        1)
        
        # Show the frame
        cv2.imshow("Edge Impulse Classification", img)
        
        # Calculate framerate
        frame_time = (cv2.getTickCount() - timestamp) / cv2.getTickFrequency()
        current_fps = 1 / frame_time
        
        # Exit on 'q' key
        if cv2.waitKey(1) == ord('q'):
            break

finally:
    # Clean up
    process.terminate()
    cv2.destroyAllWindows()
    runner.stop()