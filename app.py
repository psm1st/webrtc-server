from flask import Flask, request, jsonify
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaBlackhole
from picamera2 import Picamera2
import av
import time

app = Flask(__name__)

# Picamera2 ??? ? ?? (1280x720, 30fps)
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "RGB888"},
    controls={"FrameDurationLimits": (33333, 33333)}  # 30fps
)
picam2.configure(video_config)
picam2.start()

# WebRTC ????? ??? ??? ?? ???
class CameraStreamTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self):
        super().__init__()
        self.start_time = time.time()

    async def recv(self):
        # Picamera2??? ??? ??
        frame = picam2.capture_array()
        video_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = int((time.time() - self.start_time) * 90000)
        video_frame.time_base = av.VideoFrame().time_base
        return video_frame

# WebRTC Offer? ??? Answer ??
@app.route("/offer", methods=["POST"])
def offer():
    params = request.get_json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # PeerConnection ?? ? ??? ?? ??
    pc = RTCPeerConnection()
    pc.addTrack(CameraStreamTrack())

    async def run():
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return pc.localDescription

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    answer = loop.run_until_complete(run())
    loop.close()

    return jsonify({
        "sdp": answer.sdp,
        "type": answer.type
    })

# ?? ?????? ?? ?? ??
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
