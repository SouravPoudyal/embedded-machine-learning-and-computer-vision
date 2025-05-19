#!/usr/bin/env python
"""
Raspberry Pi Camera Image Capture with GStreamer
Displays image preview on screen. Counts down and saves image.
Press 'q' to quit early.
"""
import cv2
import time
import numpy as np

# Settings
res_width = 640                         # Resolution of camera (width)
res_height = 480                        # Resolution of camera (height)
rotation = 0                            # Camera rotation (0, 90, 180, or 270)
draw_fps = True                         # Draw FPS on screen
save_path = "./"                        # Save images to current directory
file_num = 0                            # Starting point for filename
file_suffix = ".png"                    # Extension for image file
precountdown = 2                        # Seconds before starting countdown
countdown = 5                           # Seconds to count down from

# GStreamer pipeline for Raspberry Pi Camera
pipeline = (
    "v4l2src device=/dev/video0 ! "
    f"video/x-raw,width={res_width},height={res_height},framerate=30/1 ! "
    "videoconvert ! "
    "appsink drop=true sync=false"
)

# Open capture
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Error: Could not open camera using GStreamer pipeline.")
    exit()

###########################################################################
# Functions

def file_exists(filepath):
    """Returns true if file exists, false otherwise"""
    try:
        with open(filepath, 'r') as f:
            return True
    except:
        return False

def get_filepath():
    """Returns the next available full path to image file"""
    global file_num
    filepath = save_path + str(file_num) + file_suffix
    while file_exists(filepath):
        file_num += 1
        filepath = save_path + str(file_num) + file_suffix
    return filepath

################################################################################
# Main

filepath = get_filepath()
print(f"Image will be saved to: {filepath}")
print(f"Starting {precountdown} second precountdown...")

# Initial timing
start_time = time.time()
last_count = time.time()
fps_count = 0
fps = 0

# Precountdown
while (time.time() - start_time) < precountdown:
    ret, img = cap.read()
    if not ret:
        print("Error: Could not read frame during precountdown.")
        break
    
    # Show countdown message
    remaining = precountdown - (time.time() - start_time)
    cv2.putText(img, f"Starting in: {remaining:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow("Camera", img)
    if cv2.waitKey(1) == ord('q'):
        cap.release()
        cv2.destroyAllWindows()
        exit()

print(f"Starting {countdown} second countdown...")

# Countdown loop
last_count = time.time()
while countdown > 0:
    frame_start = time.time()
    ret, img = cap.read()
    if not ret:
        print("Error: Could not read frame during countdown.")
        break

    # Rotate if needed
    if rotation == 90:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rotation == 270:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Update countdown every second
    if (time.time() - last_count) >= 1.0:
        last_count = time.time()
        countdown -= 1

    # Draw countdown
    cv2.putText(img, str(countdown), 
                (img.shape[1]//2 - 30, img.shape[0]//2),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

    # Calculate and draw FPS
    if draw_fps:
        fps_count += 1
        if fps_count >= 10:  # Update FPS every 10 frames
            fps = fps_count / (time.time() - frame_start)
            fps_count = 0
        cv2.putText(img, f"FPS: {fps:.1f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Camera", img)
    if cv2.waitKey(1) == ord('q'):
        break

# Capture final image
if countdown <= 0:
    ret, img = cap.read()
    if ret:
        # Rotate final image if needed
        if rotation == 90:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == 180:
            img = cv2.rotate(img, cv2.ROTATE_180)
        elif rotation == 270:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        cv2.imwrite(filepath, img)
        print(f"Image successfully saved to: {filepath}")
        
        # Show saved image briefly
        cv2.imshow("Captured Image", img)
        cv2.waitKey(1000)
    else:
        print("Error: Could not capture final image")

# Clean up
cap.release()
cv2.destroyAllWindows()
