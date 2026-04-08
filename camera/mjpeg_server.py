#!/usr/bin/python3

import io
import logging
import socketserver
from http import server
from threading import Condition
import time
import numpy as np
import subprocess

from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder, MJPEGEncoder
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
        self.condition = Condition()
        self.frame = None

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

output = StreamingOutput()


raw_perspective = True
raw_perspective = False

show_polygon = True
#show_polygon = False

xf_is_no = '/hack/stream.mjpg?xf=no'

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global raw_perspective

        #print(f'GET: client_address: {self.client_address}')
        print(f'\nGET: headers:\n{str(self.headers).strip()}')
        #print(f'GET: headers as_string:\n{self.headers.as_string(unixfrom=True)}')
        print(f'GET: path: {repr(self.path)}')

        if self.path == '/hack/reBoot':
            subprocess.check_call(['sudo', '/usr/sbin/reboot'])
            content = 'OK'.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == '/':
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
        elif self.path == '/stream.mjpg' or self.path == '/hack/stream.mjpg' or self.path == xf_is_no:
            raw_perspective = self.path == xf_is_no

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


debug = False
#debug = True


"""
Available cameras
-----------------
0 : imx708 [4608x2592 10-bit RGGB] (/base/soc/i2c0mux/i2c@1/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [30.00 fps - (65535, 65535)/65535x65535 crop]
                             2304x1296 [30.00 fps - (65535, 65535)/65535x65535 crop]
                             4608x2592 [30.00 fps - (65535, 65535)/65535x65535 crop]
"""

frame_duration = 70000 if not debug else 200000
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={'size': (2304, 1296)},
    lores={'size': (640, 480)},
    controls={
        'AeEnable': False,  #  'AeEnable': (False, True, True),
        'AwbEnable': False,  #  'AwbEnable': (False, True, None),
        'FrameDurationLimits': (frame_duration, frame_duration),  #  'FrameDurationLimits': (33333, 250000000, (33333, 33333)),
        'ExposureTime': 30000,  #  'ExposureTime': (1, 66666, 20000),
        'AnalogueGain': 1.0,  #  'AnalogueGain': (1.0, 16.0, 1.0),
        'Brightness': 0.2,  #  'Brightness': (-1.0, 1.0, 0.0),
        'Contrast': 1.2,  #  'Contrast': (0.0, 32.0, 1.0),
        'Saturation': 1.5,  #  'Saturation': (0.0, 32.0, 1.0),
    }
#    controls={'FrameDurationLimits': (70000, 70000)},
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

pixel_dark = 4
pixel_bright = 251
colour_dark = (pixel_dark, pixel_dark, pixel_dark)
colour_bright = (pixel_bright, pixel_bright, pixel_bright)
#colour_bright = (240, 240, 240)
#colour_bright = (255, 255, 128)

timestamp_origin = (8, 472)
#timestamp_origin = (25, 460)
#timestamp_origin = (15, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 0.9
thickness = 1

#print(f'cv2.putText: {cv2.putText}')

# Locate points of the target object
pts1 = np.float32([
    [45,189], [241,260], [248,368], [29,405],
    #[87,188], [262,267], [265,381], [53,397],
    #[146,127], [295,233], [281,351], [99,318],
    #[113,20], [279,139], [266,253], [82,218],
])
#pts1 = np.float32([[137,27], [299,143],
#                   [112,229], [287,260]])
#pts1 = np.float32([[163, 41], [313, 151],
#                   [138, 233], [301, 264]])
polygon_inner = np.array(pts1, np.int32)
polygon_inner.reshape((-1,1,2))

def make_poly(pts, offset=1):
    # assumes points are clockwise from upper left...
    (p1x, p1y), (p2x, p2y), (p3x, p3y), (p4x, p4y) = pts
    # positive offset is outside existing
    return np.float32([
        [p1x-offset, p1y-offset], [p2x+offset, p2y-offset], [p3x+offset, p3y+offset], [p4x-offset, p4y+offset],
        ])

pts1x = make_poly(pts1, 3)
#pts1x = np.float32([
#    [112,5], [280,138],
#    [265,254], [83,219],
#])
polygon_outer = np.array(pts1x, np.int32)
polygon_outer.reshape((-1,1,2))


base_x = 14
base_y = 9
scale_xy = 48
offset_x, offset_y = 2,2
#offset_x, offset_y = 20, 20
# Points to which to move the target points
pts2 = np.float32([
    [int(0*scale_xy+offset_x), int(0*scale_xy+offset_y)], [int(base_x*scale_xy+offset_x), int(0*scale_xy+offset_y)],
    [int(base_x*scale_xy+offset_x), int(base_y*scale_xy+offset_y)], [int(0*scale_xy+offset_x), int(base_y*scale_xy+offset_y)],
])
#                   [0+x, 240+y], [320+x, 240+y]])
#pts2 = np.float32([[320, 240], [680, 240],
#                   [320, 480], [680, 480]])
#pts2 = np.float32([[0, 0], [320, 0],
#                   [0, 180], [320, 180]])
# Apply Perspective Transform Algorithm
matrix = cv2.getPerspectiveTransform(pts1, pts2)

scale_blue = 0.4
scale_green = 1
scale_red = 0.9
scale_colors = np.array((scale_blue, scale_green, scale_red), dtype=np.float32)
np.reshape(scale_colors, (1,1,3))

use_res = 'lores'
#use_res = 'main'

def apply_timestamp(request):
  global raw_perspective
  timestamp = time.strftime('%Y-%m-%d-%H%M-%S')
  with MappedArray(request, use_res) as cvstuff:
    debug and print(f'cvstuff.array: shape: {cvstuff.array.shape}, dtype: {cvstuff.array.dtype}, strides: {cvstuff.array.strides}')
    bgr = cv2.cvtColor(cvstuff.array, cv2.COLOR_YUV420p2RGB)
    debug and print(f'bgr: shape: {bgr.shape}, dtype: {bgr.dtype}, strides: {bgr.strides}')

    if raw_perspective:
        unwarped = bgr
        if show_polygon:
            cv2.polylines(unwarped, [polygon_inner], True, colour_bright, 1)
            cv2.polylines(unwarped, [polygon_outer], True, colour_dark, 1)
    else:
        unwarped = cv2.warpPerspective(bgr, matrix,
        #unwarped = cv2.warpPerspective(cvstuff.array, matrix,
                                       tuple(reversed(bgr.shape[:2])),
                                       #tuple(reversed(cvstuff.array.shape[:2])),
                                       #(720, 640),
                                       flags=cv2.INTER_LINEAR,
                                       #flags=cv2.INTER_NEAREST,
                                       )
        #unwarped = cv2.warpPerspective(cvstuff.array, matrix, cvstuff.array.shape)
        #unwarped = cv2.warpPerspective(cvstuff.array, matrix, (500, 600))
    debug and print(f'unwarped 1: shape: {unwarped.shape}, dtype: {unwarped.dtype}, strides: {unwarped.strides}')
    #raw_perspective = not raw_perspective

    # Try to compensate for very blue TV image
    #np.multiply(unwarped, scale_colors, out=unwarped, casting='unsafe')
    #np.multiply(unwarped[:,:,:], scale_colors, out=unwarped[:,:,:], casting='unsafe')
    # Note: doing these individually is faster than the whole-cloth version using scale_colors; perhaps it gets done in-place without a big allocation?
    if False:
        if scale_blue != 1 :
            np.multiply(unwarped[:,:,0], np.float32(scale_blue), out=unwarped[:,:,0], casting='unsafe')
        if scale_green != 1 :
            np.multiply(unwarped[:,:,1], np.float32(scale_green), out=unwarped[:,:,1], casting='unsafe')
        if scale_red != 1 :
            np.multiply(unwarped[:,:,2], np.float32(scale_red), out=unwarped[:,:,2], casting='unsafe')
            #unwarped[:,:,0] *= 0.7
    debug and print(f'unwarped 2: shape: {unwarped.shape}, dtype: {unwarped.dtype}, strides: {unwarped.strides}')

    if False:
        normed = cv2.normalize(unwarped, None, 0, 250, cv2.NORM_MINMAX)
    else:
        normed = unwarped
    #normed = cv2.normalize(unwarped, None, 0, 255, cv2.NORM_MINMAX)
    debug and print(f'normed: shape: {normed.shape}, dtype: {normed.dtype}, strides: {normed.strides}')

    cv2.putText(normed, timestamp, timestamp_origin, font, scale, colour_dark, thickness+4)
    cv2.putText(normed, timestamp, timestamp_origin, font, scale, colour_bright, thickness)
    #cv2.putText(unwarped, timestamp, origin, font, scale, colour_bright, thickness)

    yuv = cv2.cvtColor(normed, cv2.COLOR_BGR2YUV_I420)
    #yuv = cv2.cvtColor(unwarped, cv2.COLOR_BGR2YUV_I420)
    #yuv = cv2.cvtColor(unwarped, cv2.COLOR_RGB2YUV_I420)
    debug and print(f'yuv: shape: {yuv.shape}, dtype: {yuv.dtype}, strides: {yuv.strides}')

    np.copyto(cvstuff.array, yuv)
    #cv2.putText(cvstuff.array, timestamp, origin, font, scale, colour_bright, thickness)

"""
image = cv2.imread('path_to_your_image.jpg')
2. Convert to Float for Precision
Convert the image to a floating-point format to allow for precise adjustments.

python

image_float = image.astype('float32')
3. Adjust Color Channels
You can adjust the blue channel to reduce the bluish tint. This can be done by multiplying the blue channel by a constant factor.

python

# Assuming the image is in BGR format
image_float[:,:,0] *= 0.8  # Reduce blue channel
4. Normalize the Image
After adjusting the blue channel, normalize the pixel values back to the range of 0-255.

python

image_corrected = cv2.normalize(image_float, None, 0, 255, cv2.NORM_MINMAX)
"""

picam2.pre_callback = apply_timestamp
#picam2.start(show_preview=True)

H264Encoder(repeat=True, iperiod=20)
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
