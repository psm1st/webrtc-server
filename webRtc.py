import io
import asyncio
import logging
import numpy as np
import cv2
import av
from flask import Flask, request, jsonify, render_template_string
from threading import Condition
from urllib.parse import parse_qs

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay

from picamera2 import Picamera2
from libcamera import Transform

app = Flask(__name__)
pcs = set()
relay = MediaRelay()

left_value = 17
right_value = 17
distorted = False

PAGE_TEMPLATE = """\
<html>
<head><title>Mand.ro WebRTC Streaming</title>
<style>
  body {{
    background: black;
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
  }}
  .case {{
    display: flex;
  }}
  .box {{
    overflow: hidden;
    position: relative;
    border: 0px solid grey;
  }}
  .hori_1 {{
    width: 400px;
    height: 400px;
  }}
  .hori_2 {{
    width: 400px;
    height: 400px;
  }}
  video {{
    position: absolute;
    width: auto;
    height: 100%;
  }}
  #video1 {{
    left: {left_value}%;
    transform: rotate(90deg);
  }}
  #video2 {{
    right: {right_value}%;
    transform: rotate(270deg);
  }}
</style>
</head>
<body>
<div class="case">
<h1>change WebRtc</h1>
    <div class="box hori_1">
        <video id="video1" autoplay playsinline></video>
    </div>
    <div class="box hori_2">
        <video id="video2" autoplay playsinline></video>
    </div>
</div>
<script>
  async function start(camera, videoElementId) {{
    const pc = new RTCPeerConnection();

    pc.ontrack = (event) => {{
      document.getElementById(videoElementId).srcObject = event.streams[0];
    }};

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const response = await fetch("/offer", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type,
        camera: camera
      }})
    }});

    const answer = await response.json();
    await pc.setRemoteDescription(answer);
  }}

  start(0, "video1");
  start(1, "video2");
</script>
</body>
</html>
"""

def crop_to_square(image):
    height, width = image.shape[:2]
    size = min(width, height)
    x_center, y_center = width // 2, height // 2
    x_start = max(0, x_center - size // 2)
    y_start = max(0, y_center - size // 2)
    return image[y_start:y_start + size, x_start:x_start + size]

def apply_barrel_distortion(image):
    square_image = crop_to_square(image)
    height, width = square_image.shape[:2]

    camera_matrix = np.array([[width, 0, width / 2],
                              [0, height, height / 2],
                              [0, 0, 1]], dtype=np.float32)
    distortion_coefficients = np.array([0.3, 0.1, 0, 0], dtype=np.float32)

    new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coefficients, (width, height), 1)
    map1, map2 = cv2.initUndistortRectifyMap(camera_matrix, distortion_coefficients, None, new_camera_matrix,
                                             (width, height), cv2.CV_32FC1)
    distorted_image = cv2.remap(square_image, map1, map2, cv2.INTER_LINEAR)
    return distorted_image

picam1 = Picamera2(0)
picam1.configure(picam1.create_video_configuration(
    main={"size": (640, 480)}, transform=Transform(rotation=90)))
picam1.start()

picam2 = Picamera2(1)
picam2.configure(picam2.create_video_configuration(
    main={"size": (640, 480)}, transform=Transform(rotation=270)))
picam2.start()

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

@app.route("/")
def index():
    adjusted_left = -left_value + (17 if distorted else 0)
    adjusted_right = -right_value + (17 if distorted else 0)
    return render_template_string(PAGE_TEMPLATE.format(
        left_value=adjusted_left,
        right_value=adjusted_right
    ))

@app.route("/offer", methods=["POST"])
async def offer():
    params = await request.get_json()
    camera = int(params.get("camera", 0))
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    track = CameraTrack(picam1 if camera == 0 else picam2)
    pc.addTrack(track)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return jsonify({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

@app.route("/update", methods=["POST"])
def update():
    global left_value, right_value, distorted
    content_length = int(request.headers['Content-Length'])
    post_data = request.get_data().decode('utf-8')
    params = parse_qs(post_data)

    left_value = int(params.get('left', [left_value])[0])
    right_value = int(params.get('right', [right_value])[0])
    distorted = params.get('distorted', ['false'])[0].lower() == 'true'

    print(f"Updated: left={left_value}, right={right_value}, distorted={distorted}")
    return "Values updated"

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8000)
    finally:
        print("Shutting down cameras...")
        picam1.stop()
        picam2.stop()
