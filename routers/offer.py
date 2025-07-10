from fastapi import APIRouter, Request
from aiortc import RTCPeerConnection, RTCSessionDescription
from camera.videoTrack import CameraTrack

router = APIRouter()
pcs = set()

@router.post("/offer")
async def offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    camera_index = int(params.get("camera_index", 0))

    pc = RTCPeerConnection()
    pcs.add(pc)

    print(f" Offer received for camera: {camera_index}")
    print(" Creating new CameraTrack")
    video_track = CameraTrack(camera_index)
    pc.addTrack(video_track)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(" Connection state is", pc.connectionState)
        if pc.connectionState in ["failed", "closed", "disconnected"]:
            await video_track.stop()  
            await pc.close()
            pcs.discard(pc)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
