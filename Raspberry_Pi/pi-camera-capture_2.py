import cv2
import argparse
from pathlib import Path
import time
import os

class CameraCapture:
    def __init__(self, save_path="./captures", file_suffix=".jpg", 
                 res_width=640, res_height=480, rotation=0, 
                 draw_fps=True, precountdown=2, countdown=3):
        """
        Initialize camera capture with default or provided parameters
        
        Args:
            save_path: Directory to save captures (will be created if doesn't exist)
            file_suffix: Image file extension (.jpg, .png, etc.)
            res_width: Camera resolution width
            res_height: Camera resolution height
            rotation: Image rotation (0, 90, 180, or 270 degrees)
            draw_fps: Whether to display FPS in preview
            precountdown: Seconds before countdown begins
            countdown: Countdown duration in seconds
        """
        self.res_width = res_width
        self.res_height = res_height
        self.rotation = rotation
        self.draw_fps = draw_fps
        self.save_path = save_path
        self.file_suffix = file_suffix.lower()  # Ensure lowercase
        self.precountdown = precountdown
        self.countdown = countdown
        self.cap = None
        
        # Create save directory if it doesn't exist
        os.makedirs(self.save_path, exist_ok=True)

    def initialize_camera(self):
        """Initialize the camera device"""
        self.cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.res_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.res_height)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

    def get_filepath(self):
        """Generate unique filename with timestamp"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = Path(self.save_path) / f"capture_{timestamp}{self.file_suffix}"
        return str(filepath)

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
        """Capture and save an image with countdown and preview"""
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
                cv2.putText(frame, f"Starting in: {remaining:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow("Preview", frame)
                if cv2.waitKey(1) == ord('q'):
                    raise KeyboardInterrupt

            # Countdown
            print(f"Starting {self.countdown} second countdown...")
            countdown_end = time.time() + self.countdown
            last_second = int(self.countdown)
            fps_update = time.time()
            fps_count = 0
            fps = 0

            while time.time() < countdown_end:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Camera read error")
                
                current_second = int(countdown_end - time.time())
                if current_second != last_second:
                    print(f"{current_second}...")
                    last_second = current_second
                
                # Calculate FPS
                fps_count += 1
                if time.time() - fps_update >= 1.0:
                    fps = fps_count
                    fps_count = 0
                    fps_update = time.time()
                
                frame = self.rotate_frame(frame)
                
                # Draw countdown
                remaining = countdown_end - time.time()
                cv2.putText(frame, f"Capturing in: {remaining:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Draw FPS if enabled
                if self.draw_fps:
                    cv2.putText(frame, f"FPS: {fps}", (10, 60),
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


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Camera Capture Application")
    parser.add_argument("--save-path", type=str, default="./captures",
                        help="Directory to save images (default: ./captures)")
    parser.add_argument("--file-suffix", type=str, default=".jpg",
                        choices=['.jpg', '.png', '.jpeg'],
                        help="Image file extension (default: .jpg)")
    parser.add_argument("--width", type=int, default=640,
                        help="Camera resolution width (default: 640)")
    parser.add_argument("--height", type=int, default=480,
                        help="Camera resolution height (default: 480)")
    parser.add_argument("--rotation", type=int, default=0,
                        choices=[0, 90, 180, 270],
                        help="Image rotation in degrees (default: 0)")
    parser.add_argument("--no-fps", action="store_false", dest="draw_fps",
                        help="Disable FPS display in preview")
    parser.add_argument("--precountdown", type=int, default=2,
                        help="Precountdown duration in seconds (default: 2)")
    parser.add_argument("--countdown", type=int, default=3,
                        help="Countdown duration in seconds (default: 3)")
    return parser.parse_args()


def main():
    """Main application entry point"""
    args = parse_arguments()
    
    try:
        camera = CameraCapture(
            save_path=args.save_path,
            file_suffix=args.file_suffix,
            res_width=args.width,
            res_height=args.height,
            rotation=args.rotation,
            draw_fps=args.draw_fps,
            precountdown=args.precountdown,
            countdown=args.countdown
        )
        
        print("\nCamera settings:")
        print(f"  Resolution: {camera.res_width}x{camera.res_height}")
        print(f"  Rotation: {camera.rotation}°")
        print(f"  Save location: {os.path.abspath(camera.save_path)}")
        print(f"  File format: {camera.file_suffix}")
        print(f"  Precountdown: {camera.precountdown}s")
        print(f"  Countdown: {camera.countdown}s")
        print(f"  Show FPS: {'Yes' if camera.draw_fps else 'No'}")
        
        saved_path = camera.capture_image()
        print(f"\nCapture complete! Image saved to: {saved_path}")
        
    except Exception as e:
        print(f"\nError during capture: {str(e)}")
    finally:
        if 'camera' in locals():
            camera.release()

if __name__ == "__main__":
    main()
