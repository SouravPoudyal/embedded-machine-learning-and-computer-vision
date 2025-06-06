import cv2
import numpy as np
import subprocess
import select

# GStreamer pipeline configuration
WIDTH, HEIGHT = 640, 480
FPS = 30

def run_gstreamer_pipeline():
    command = [
        'gst-launch-1.0',
        'v4l2src', 'device=/dev/video0', '!',
        f'video/x-raw,width={WIDTH},height={HEIGHT},framerate={FPS}/1', '!',
        'videoconvert', '!',
        'video/x-raw,format=BGR', '!',
        'fdsink', 'fd=1'
    ]
    
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=WIDTH*HEIGHT*3,  # Buffer size for BGR image
        universal_newlines=False
    )

def main():
    process = run_gstreamer_pipeline()
    
    try:
        while True:
            # Read raw frame data from pipe
            raw_frame = process.stdout.read(WIDTH*HEIGHT*3)
            if not raw_frame:
                break
                
            # Convert to numpy array
            frame = np.frombuffer(raw_frame, dtype=np.uint8)
            frame = frame.reshape((HEIGHT, WIDTH, 3))
            
            # Display with OpenCV
            cv2.imshow('GStreamer + OpenCV', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        process.terminate()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()