import io

import pygame.camera
import pygame.image
from PIL import Image

class Camera:

    def __init__(self, index, width, height, quality, stopdelay):
        print("[state] Initializing camera...")
        pygame.camera.init()
        camera_name = pygame.camera.list_cameras()[index]
        self._cam = pygame.camera.Camera(camera_name, (width, height))
        print("[state] Camera " + camera_name +" initialized")
        self.is_started = False
        self.stop_requested = False
        self.quality = quality
        self.stopdelay = stopdelay

    def request_start(self):
        if self.stop_requested:
            print("[state] Camera continues to be in use")
            self.stop_requested = False
        if not self.is_started:
            self._start()

    def request_stop(self):
        if self.is_started and not self.stop_requested:
            self.stop_requested = True
            self._stop()
            print("[state] Stopping camera in " + str(self.stopdelay) + " seconds...")
            #tornado.ioloop.IOLoop.current().call_later(self.stopdelay, self._stop)

    def _start(self):
        print("[state] Starting camera...")
        self._cam.start()
        print("[state] Camera started")
        self.is_started = True

    def _stop(self):
        if self.stop_requested:
            print("[state] Stopping camera now...")
            self._cam.stop()
            print("[state] Camera stopped")
            self.is_started = False
            self.stop_requested = False

    def get_jpeg_image_bytes(self):
        img = self._cam.get_image()
        imgstr = pygame.image.tostring(img, "RGB", False)
        pimg = Image.frombytes("RGB", img.get_size(), imgstr)
        with io.BytesIO() as bytesIO:
            pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
            return bytesIO.getvalue()

