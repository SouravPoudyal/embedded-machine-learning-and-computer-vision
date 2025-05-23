import cv2
import time
import os

class CameraCapture:
    def __init__(self):
        # Settings from your parameters
        self.res_width = 96
        self.res_height = 96
        self.rotation = 0
        self.cam_format = "RGB888"
        self.draw_fps = False
        self.save_path = "./pictures/Class_1"
        self.file_num = 0
        self.file_suffix = ".png"
        self.precountdown = 2
        self.countdown = 5
        self.fps = 0
        self.cap = None

    def initialize_camera(self):
        """Initialize the camera device with specified settings"""
        self.cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L)
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.res_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.res_height)
        
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

    def get_filepath(self):
        """Generate sequential filename (0.png, 1.png, etc.)"""
        while True:
            filepath = os.path.join(self.save_path, f"{self.file_num}{self.file_suffix}")
            if not os.path.exists(filepath):
                return filepath
            self.file_num += 1

    def rotate_frame(self, frame):
        """Rotate frame according to settings"""
        if self.rotation == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif self.rotation == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame

    def capture_image(self):
        """Capture and save an image with countdown"""
        if self.cap is None:
            self.initialize_camera()

        filepath = self.get_filepath()
        
        try:
            # Precountdown
            print(f"Starting {self.precountdown} second precountdown...")
            precount_end = time.time() + self.precountdown
            while time.time() < precount_end:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Camera read error")
                
                remaining = precount_end - time.time()
                frame = self.rotate_frame(frame)
                cv2.putText(frame, f"Starting in: {remaining:.1f}", (5, 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
                cv2.imshow("Preview", frame)
                if cv2.waitKey(1) == ord('q'):
                    raise KeyboardInterrupt

            # Countdown
            print(f"Starting {self.countdown} second countdown...")
            countdown_end = time.time() + self.countdown
            last_second = int(self.countdown)

            while time.time() < countdown_end:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Camera read error")
                
                current_second = int(countdown_end - time.time())
                if current_second != last_second:
                    print(f"{current_second}...")
                    last_second = current_second
                
                frame = self.rotate_frame(frame)
                
                # Draw countdown (scaled for 96x96 resolution)
                remaining = countdown_end - time.time()
                cv2.putText(frame, f"{remaining:.1f}", (5, 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
                
                cv2.imshow("Preview", frame)
                if cv2.waitKey(1) == ord('q'):
                    raise KeyboardInterrupt

            # Capture final image
            ret, frame = self.cap.read()
            if ret:
                frame = self.rotate_frame(frame)
                cv2.imwrite(filepath, frame)
                print(f"Image successfully saved as {filepath}")
                
                # Show captured image briefly
                cv2.imshow("Captured", frame)
                cv2.waitKey(500)  # Show for 0.5 seconds
                
                # Increment file number for next capture
                self.file_num += 1
                return filepath
            else:
                raise RuntimeError("Failed to capture final image")

        except Exception as e:
            print(f"Error: {str(e)}")
            raise
        finally:
            cv2.destroyAllWindows()

    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __del__(self):
        """Destructor to ensure camera is released"""
        self.release()


def main():
    """Main application entry point"""
    try:
        camera = CameraCapture()
        
        print("\nCamera settings:")
        print(f"  Resolution: {camera.res_width}x{camera.res_height}")
        print(f"  Rotation: {camera.rotation}°")
        print(f"  Save location: {os.path.abspath(camera.save_path)}")
        print(f"  File format: {camera.file_suffix}")
        print(f"  Starting file number: {camera.file_num}")
        print(f"  Precountdown: {camera.precountdown}s")
        print(f"  Countdown: {camera.countdown}s")
        
        saved_path = camera.capture_image()
        print(f"\nCapture complete! Image saved as: {saved_path}")
        
    except Exception as e:
        print(f"\nError during capture: {str(e)}")
    finally:
        if 'camera' in locals():
            camera.release()

if __name__ == "__main__":
    main()
