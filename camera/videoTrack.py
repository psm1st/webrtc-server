import av
import numpy as np
import asyncio
from aiortc import VideoStreamTrack
from av.frame import Frame
from camera.cameraManager import CameraManager

track_registry = {}

frame_lock = asyncio.Lock()


class CameraTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int):
        super().__init__()
        self.index = camera_index

        if camera_index in track_registry:
            print(f"⚠️ Closing previous CameraTrack for camera {camera_index}")
            old_track = track_registry[camera_index]

            async def safe_stop(track):
                try:
                    await track.stop()
                except Exception as e:
                    print(f"⚠️ Error while stopping old track: {e}")

            asyncio.create_task(safe_stop(old_track))

        self.camera = CameraManager.get_camera(self.index)
        track_registry[self.index] = self
        print(f" CameraTrack initialized for camera {self.index}")

    async def recv(self) -> Frame:
        from av import VideoFrame

        pts, time_base = await self.next_timestamp()

        try:
            async with frame_lock:
                frame = self.camera.capture_array()
                print(f"Captured frame from camera {self.index} - shape: {frame.shape}, dtype: {frame.dtype}")

            if not isinstance(frame, np.ndarray) or frame.size == 0:
                print("❌ Invalid frame received!")
                return None

            video_frame = VideoFrame.from_ndarray(frame.copy(), format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base
            print(" Frame ready and timestamped")
            return video_frame

        except Exception as e:
            print(f" Error during frame processing: {e}")
            return None

    async def stop(self):
        print(f"Stopping CameraTrack for camera {self.index}")
        CameraManager.release_camera(self.index)

        if self.index in track_registry and track_registry[self.index] is self:
            del track_registry[self.index]

        super().stop()
