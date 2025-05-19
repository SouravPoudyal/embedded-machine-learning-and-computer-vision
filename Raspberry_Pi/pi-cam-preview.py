
"""
Raspberry Pi Camera Test

Capture frame from Pi Camera and display it to the screen using OpenCV (cv2).
Also display the framerate (fps) to the screen. Use this to adjust the camera's
focus. Press ctrl + c in the console or 'q' on the preview window to stop.
"""

import cv2
import subprocess
import numpy as np

# GStreamer pipeline string (identical to terminal command)
pipeline = (
    "v4l2src device=/dev/video0 ! "
    "video/x-raw,width=640,height=480,framerate=30/1 ! "
    "videoconvert ! "
    "appsink drop=true sync=false"
)

# Open capture
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
print(cap)

if not cap.isOpened():
    # Fallback to terminal command if OpenCV fails
    print("OpenCV GStreamer failed, using subprocess fallback")
    proc = subprocess.Popen(
        ['gst-launch-1.0', 'v4l2src', 'device=/dev/video0', '!',
         'video/x-raw,width=640,height=480,framerate=30/1', '!',
         'videoconvert', '!', 'autovideosink'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
else:
    print("Streaming - Press 'q' to quit")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame read error")
            break
            
        cv2.imshow("Camera", frame)
        if cv2.waitKey(1) == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

