#!/usr/bin/python3

# This is the same as mjpeg_server.py, but uses the h/w MJPEG encoder.

import io
import logging
import socketserver
from http import server
from threading import Condition
import time
import numpy as np

from picamera2 import Picamera2, MappedArray
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from libcamera import Transform, Rectangle, Size

import cv2
#print(f'dir(cv2): {tuple(c for c in dir(cv2) if c.startswith("COLOR_"))}')
#1/0

PAGE = """\
<html>
  <head>
    <title>Picamera2 MJPEG streaming demo</title>
  </head>
  <body>
    <h1>Picamera2 MJPEG Streaming Demo</h1>
    <img src='http://192.168.58.114:8001/stream.mjpg' />
    <!--<img src="stream.mjpg" />-->
    <!--<img src="stream.mjpg" width="320" height="240" />-->
    <!--<img src="stream.mjpg" width="640" height="480" />-->
  </body>
</html>
"""


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg' or self.path == '/hack/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME_NNZADxNpMGgEGziw')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME_NNZADxNpMGgEGziw\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


"""
Available cameras
-----------------
0 : imx708 [4608x2592 10-bit RGGB] (/base/soc/i2c0mux/i2c@1/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [30.00 fps - (65535, 65535)/65535x65535 crop]
                             2304x1296 [30.00 fps - (65535, 65535)/65535x65535 crop]
                             4608x2592 [30.00 fps - (65535, 65535)/65535x65535 crop]
"""

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={'size': (2304, 1296)},
    lores={'size': (640, 480)},
    controls={'FrameDurationLimits': (70000, 70000)},
#    controls={'FrameDurationLimits': (100000, 100000)},
#    controls={'FrameDurationLimits': (200000, 200000)},
    ))
#picam2.configure(picam2.create_video_configuration(main={'size': (1536, 864)}, lores={'size': (640, 480)}, controls={'FrameDurationLimits': (70000, 70000)}))
# (33333, 250000000)
#picam2.configure(picam2.create_video_configuration(lores={'size': (320, 240)}, transform=Transform(hflip=True, vflip=True), controls={'FrameDurationLimits': (200000, 200000)}))
#picam2.configure(picam2.create_video_configuration(main={'size': (320, 240)}, transform=Transform(hflip=True, vflip=True), controls={'FrameDurationLimits': (100000, 100000)}))
#picam2.configure(picam2.create_video_configuration(main={'size': (1536, 864)}, lores={'size': (320, 240)}, transform=Transform(hflip=True, vflip=True), controls={'FrameDurationLimits': (75000, 75000)}))
#picam2.configure(picam2.create_video_configuration(main={'size': (2304, 1296)}, lores={'size': (640, 480)}, transform=Transform(hflip=True, vflip=True), controls={'FrameDurationLimits': (75000, 75000)}))
#picam2.configure(picam2.create_video_configuration(main={'size': (320, 240)}, transform=Transform(hflip=True, vflip=True), controls={'FrameDurationLimits': (66666, 66666)}))
#picam2.configure(picam2.create_video_configuration(main={'size': (320, 240)}, transform=Transform(hflip=True, vflip=True)))
#picam2.configure(picam2.create_video_configuration(main={'size': (640, 480)}))


#rect = Rectangle(100, 100, 300, 200)
#print(f'rect: {rect}')
#print(f'Rectangle(100, 100, Size(300, 200)): {Rectangle(100, 100, Size(300, 200))}')

#picam2.set_controls({'ScalerCrop': (0, 330, 4608, 2020)})

#picam2.set_controls({'ScalerCrop': Rectangle(100, 100, Size(300, 200))})

"""
ScalerCrop
A libcamera.Rectangle consisting of:
x_offset
y_offset
width
height
"""

output = StreamingOutput()

colour = (240, 240, 240)
#colour = (255, 255, 128)
origin = (15, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 0.7
thickness = 2

#print(f'cv2.putText: {cv2.putText}')

# Locate points of the documents
# or object which you want to transform
pts1 = np.float32([[163, 41], [313, 151],
                   [138, 233], [301, 264]])
x, y = 20, 40
pts2 = np.float32([[0+x, 0+y], [320+x, 0+y],
                   [0+x, 180+y], [320+x, 180+y]])
#                   [0+x, 240+y], [320+x, 240+y]])
#pts2 = np.float32([[320, 240], [680, 240],
#                   [320, 480], [680, 480]])
#pts2 = np.float32([[0, 0], [320, 0],
#                   [0, 180], [320, 180]])
# Apply Perspective Transform Algorithm
matrix = cv2.getPerspectiveTransform(pts1, pts2)

debug = False
#debug = True

use_res = 'lores'
#use_res = 'main'
def apply_timestamp(request):
  timestamp = time.strftime('%Y-%m-%d-%H%M-%S')
  with MappedArray(request, use_res) as cvstuff:
    debug and print(f'cvstuff.array: shape: {cvstuff.array.shape}, dtype: {cvstuff.array.dtype}, strides: {cvstuff.array.strides}')
    bgr = cv2.cvtColor(cvstuff.array, cv2.COLOR_YUV420p2RGB)
    debug and print(f'bgr: shape: {bgr.shape}, dtype: {bgr.dtype}, strides: {bgr.strides}')

    unwarped = cv2.warpPerspective(bgr, matrix,
    #unwarped = cv2.warpPerspective(cvstuff.array, matrix,
                                   tuple(reversed(bgr.shape[:2])),
                                   #tuple(reversed(cvstuff.array.shape[:2])),
                                   #(720, 640),
                                   #flags=cv2.INTER_LINEAR,
                                   flags=cv2.INTER_NEAREST,
                                   )
    #unwarped = cv2.warpPerspective(cvstuff.array, matrix, cvstuff.array.shape)
    #unwarped = cv2.warpPerspective(cvstuff.array, matrix, (500, 600))
    debug and print(f'unwarped: shape: {unwarped.shape}, dtype: {unwarped.dtype}, strides: {unwarped.strides}')


    yuv = cv2.cvtColor(unwarped, cv2.COLOR_BGR2YUV_I420)
    #yuv = cv2.cvtColor(unwarped, cv2.COLOR_RGB2YUV_I420)
    debug and print(f'yuv: shape: {yuv.shape}, dtype: {yuv.dtype}, strides: {yuv.strides}')

    np.copyto(cvstuff.array, yuv)
    #np.copyto(cvstuff.array, unwarped)
    cv2.putText(cvstuff.array, timestamp, origin, font, scale, colour, thickness)
    unwarped = rgb = yuv = None

picam2.pre_callback = apply_timestamp
#picam2.start(show_preview=True)

picam2.start_recording(MJPEGEncoder(), FileOutput(output), name=use_res)
#picam2.start_recording(MJPEGEncoder(), FileOutput(output), name='lores')
# 2304x1296
#picam2.set_controls({'ScalerCrop': rect})

try:
    address = ('', 8001)
    server = StreamingServer(address, StreamingHandler)
    print(f'serving at (address, port): {address}')
    server.serve_forever()
finally:
    picam2.stop_recording()


"""

from picamera2 import Picamera2, MappedArray
import cv2

picam2 = Picamera2()
colour = (0, 255, 0)
origin = (0, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2

def apply_timestamp(request):
  timestamp = time.strftime("%Y-%m-%d %X")
  with MappedArray(request, "main") as m:
    cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)

picam2.pre_callback = apply_timestamp
picam2.start(show_preview=True)

"""
