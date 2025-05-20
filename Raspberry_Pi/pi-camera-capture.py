#!/usr/bin/env python
"""
Improved Raspberry Pi Camera Image Capture
Uses libcamera directly for best compatibility with Raspberry Pi OS Bullseye+
"""
import cv2
import time
import numpy as np
import subprocess
from pathlib import Path

class CameraCapture:
    def __init__(self):
        # Settings
        self.res_width = 640
        self.res_height = 480
        self.rotation = 0
        self.draw_fps = True
        self.save_path = "./"
        self.file_suffix = ".png"
        self.precountdown = 2
        self.countdown = 5
        self.cap = None

    def get_filepath(self):
        """Generate unique filename"""
        index = 0
        while True:
            filepath = Path(self.save_path) / f"capture_{index}{self.file_suffix}"
            if not filepath.exists():
                return str(filepath)
            index += 1

    def initialize_camera(self):
        """Initialize camera with GStreamer pipeline"""
        pipeline = (
            f"v4l2src device=/dev/video0 ! "
            f"video/x-raw,width={self.res_width},height={self.res_height},framerate=30/1 ! "
            "videoconvert ! "
            "appsink drop=true sync=false"
        )
        
        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            print("GStreamer pipeline failed, trying alternative methods...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Cannot open camera")

    def rotate_frame(self, frame):
        """Rotate frame according to settings"""
        if self.rotation == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotation == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame

    def run(self):
        try:
            self.initialize_camera()
            filepath = self.get_filepath()
            print(f"Image will be saved to: {filepath}")

            # Precountdown
            print(f"Starting {self.precountdown} second precountdown...")
            precount_end = time.time() + self.precountdown
            while time.time() < precount_end:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Camera read error")
                
                remaining = precount_end - time.time()
                frame = self.rotate_frame(frame)
                cv2.putText(frame, f"Starting in: {remaining:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow("Preview", frame)
                if cv2.waitKey(1) == ord('q'):
                    raise KeyboardInterrupt

            # Countdown
            print(f"Starting {self.countdown} second countdown...")
            last_second = time.time()
            fps_update = time.time()
            fps_count = 0
            fps = 0

            while self.countdown > 0:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Camera read error")

                frame = self.rotate_frame(frame)

                # Update countdown
                now = time.time()
                if now - last_second >= 1.0:
                    last_second = now
                    self.countdown -= 1

                # Draw UI elements
                cv2.putText(frame, str(self.countdown), 
                            (frame.shape[1]//2 - 30, frame.shape[0]//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

                if self.draw_fps:
                    fps_count += 1
                    if now - fps_update >= 1.0:
                        fps = fps_count / (now - fps_update)
                        fps_count = 0
                        fps_update = now
                    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                cv2.imshow("Preview", frame)
                if cv2.waitKey(1) == ord('q'):
                    raise KeyboardInterrupt

            # Capture final image
            ret, frame = self.cap.read()
            if ret:
                frame = self.rotate_frame(frame)
                cv2.imwrite(filepath, frame)
                print(f"Image successfully saved to {filepath}")
                
                # Show captured image
                cv2.imshow("Captured", frame)
                cv2.waitKey(2000)  # Show for 2 seconds

        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            if self.cap and self.cap.isOpened():
                self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    capture = CameraCapture()
    capture.run()
