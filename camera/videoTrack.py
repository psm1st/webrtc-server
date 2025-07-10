import av
import numpy as np
import asyncio
from aiortc import VideoStreamTrack
from camera.stereoManager import stereo_loop  

class CameraTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, camera_index: int):
        super().__init__()
        self.index = camera_index
        self.queue = asyncio.Queue(maxsize=2)
        stereo_loop.register(camera_index, self.queue)
        print(f" 카메라 {camera_index} 트랙 초기화 완료")

    async def recv(self):
        from av import VideoFrame
        pts, time_base = await self.next_timestamp()

        frame = await self.queue.get()
        video_frame = VideoFrame.from_ndarray(frame.copy(), format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self):
        print(f" 카메라 {self.index} 트랙 종료")
        stereo_loop.unregister(self.index, self.queue)
        super().stop()
