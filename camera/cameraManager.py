from picamera2 import Picamera2
from libcamera import Transform

class CameraManager:
    _instances = {}
    _active_flags = {}

    @classmethod
    def get_camera(cls, index=0):
        if index not in cls._instances:
            cam = Picamera2(index)
            cam.configure(cam.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                transform=Transform(rotation=90 if index == 0 else 270)
            ))
            cam.start()
            cls._instances[index] = cam
            cls._active_flags[index] = True
        return cls._instances[index]

    @classmethod
    def release_camera(cls, index=0):
        if index in cls._instances:
            try:
                cls._instances[index].stop()
                cls._instances[index].close()
                print(f"🧹 Released camera {index}")
            except Exception as e:
                print(f"⚠️ Error releasing camera {index}: {e}")
            del cls._instances[index]
            del cls._active_flags[index]

    @classmethod
    def is_active(cls, index=0):
        return cls._active_flags.get(index, False)
