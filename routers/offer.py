from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from aiortc import RTCPeerConnection, RTCSessionDescription
from camera.videoTrack import CameraTrack, picam1, picam2

router = APIRouter()

pcs = set()

class OfferRequest(BaseModel):
    sdp: str
    type: str
    camera: int = 0

@router.post("/offer")
async def offer(request: OfferRequest):
    print("요청 받은 내용:", request.dict())  

    offer = RTCSessionDescription(sdp=request.sdp, type=request.type)
    camera = request.camera

    print(" 카메라 번호:", camera)

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    print(" 카메라 객체 생성 시도")
    track = CameraTrack(picam1 if camera == 0 else picam2)
    print(" 트랙 추가됨")
    pc.addTrack(track)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return JSONResponse(content={
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })
