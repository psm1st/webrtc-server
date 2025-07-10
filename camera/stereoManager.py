import asyncio
from picamera2 import Picamera2
from collections import defaultdict

class StereoCaptureLoop:
    def __init__(self):
        self.cam0 = Picamera2(0)
        self.cam1 = Picamera2(1)

        self.cam0.configure(self.cam0.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        ))
        self.cam1.configure(self.cam1.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        ))

        self.cam0.start()
        self.cam1.start()

        self.queues = defaultdict(list)
        self.running = False

    def register(self, index, queue: asyncio.Queue):
        self.queues[index].append(queue)

    def unregister(self, index, queue: asyncio.Queue):
        if queue in self.queues[index]:
            self.queues[index].remove(queue)

    async def start_loop(self):
        self.running = True
        while self.running:
            frame0 = self.cam0.capture_array()
            frame1 = self.cam1.capture_array()

            for q in self.queues[0]:
                if not q.full():
                    await q.put(frame0)

            for q in self.queues[1]:
                if not q.full():
                    await q.put(frame1)

            await asyncio.sleep(0.033) 

    def stop(self):
        self.running = False
        self.cam0.stop()
        self.cam1.stop()
        self.cam0.close()
        self.cam1.close()

stereo_loop = StereoCaptureLoop()