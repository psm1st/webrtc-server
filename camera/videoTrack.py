import av
from aiortc import VideoStreamTrack
from camera.distortion import apply_barrel_distortion
from picamera2 import Picamera2
from libcamera import Transform

picam1 = Picamera2(0)
picam1.configure(picam1.create_video_configuration(
    main={"size": (640, 480)}, transform=Transform(rotation=90)))
picam1.start()

picam2 = Picamera2(1)
picam2.configure(picam2.create_video_configuration(
    main={"size": (640, 480)}, transform=Transform(rotation=270)))
picam2.start()

distorted = False  

class CameraTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, camera):
        super().__init__()
        self.camera = camera

    async def recv(self):
        frame = self.camera.capture_array()
        print("📸 Captured frame shape:", frame.shape)
        if distorted:
            frame = apply_barrel_distortion(frame)
        frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        frame.pts, frame.time_base = await self.next_timestamp()
        return frame
