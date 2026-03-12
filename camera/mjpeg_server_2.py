#!/usr/bin/python3

# This is the same as mjpeg_server.py, but uses the h/w MJPEG encoder.

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from libcamera import Transform, Rectangle, Size

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
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
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
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
picam2.configure(picam2.create_video_configuration(main={'size': (2304, 1296)}, lores={'size': (640, 480)}, controls={'FrameDurationLimits': (70000, 70000)}))
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
picam2.set_controls({'ScalerCrop': (0, 330, 4608, 2020)})
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
picam2.start_recording(MJPEGEncoder(), FileOutput(output), name='lores')
# 2304x1296
#picam2.set_controls({'ScalerCrop': rect})

try:
    address = ('', 8001)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
