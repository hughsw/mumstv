#!/usr/bin/python3

# needs: sudo /bin/dash -c 'DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-numpy python3-picamera2 python3-opencv'

import io
import logging
from http import server
from threading import Condition
import time

use_np = False
if use_np:
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
    <title>MumsTV demo</title>
  </head>
  <body>
    <h1>MumsTV Streaming Demo</h1>
    <img src='/hack/stream.mjpg?xf=no' />
    <!--<img src='http://192.168.58.114:8001/stream.mjpg' />-->
    <!--<img src="stream.mjpg" />-->
    <!--<img src="stream.mjpg" width="320" height="240" />-->
    <!--<img src="stream.mjpg" width="640" height="480" />-->
  </body>
</html>
"""


class FramePubSubIO(io.BufferedIOBase):
    def __init__(self):
        self.condition = Condition()
        self.frame = None

    def write(self, buf):
        with self.condition:
            # copy since we can't control when self.frame will be used;
            # yes, there's still a race if write is called again before the notify_all clients have used the current frame...
            self.frame = bytes(buf)
            self.condition.notify_all()
        return len(self.frame)

    def __iter__(self):
        while True:
            with self.condition:
                self.condition.wait()
                yield self.frame


class ThreadedReuseServer(server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


output = FramePubSubIO()


raw_perspective = True
#raw_perspective = False

show_polygon = True
show_polygon = False

xf_is_no = '/hack/stream.mjpg?xf=no'

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global raw_perspective, show_polygon

        print(f'\nGET: client_address: {self.client_address}')
        print(f'GET: path: {repr(self.path)}')
        #print(f'GET: headers as_string:\n{self.headers.as_string(unixfrom=True)}')

        if self.path == '/hack/reBoot':
            subprocess.check_call(['sudo', '/usr/sbin/reboot'])
            content = 'reboot: OK'.encode('utf-8')
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
            print(f'GET: headers:\n{str(self.headers).strip()}')

            raw_perspective = self.path == xf_is_no
            boundary = 'FRAME_NNZADxNpMGgEGziw'

            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-Type', f'multipart/x-mixed-replace; boundary={boundary}')
            self.end_headers()
            try:
#                while True:
#                    with output.condition:
#                        output.condition.wait()
#                        frame = output.frame
                for frame in output:
                    self.wfile.write(f'--{boundary}\r\n'.encode('utf-8'))
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


debug = False
#debug = True


"""
Available cameras
-----------------
0 : imx219 [3280x2464 10-bit RGGB] (/base/soc/i2c0mux/i2c@1/imx219@10)
    Modes: 'SRGGB10_CSI2P' : 640x480 [103.33 fps - (1000, 752)/1280x960 crop]
                             1640x1232 [41.85 fps - (0, 0)/3280x2464 crop]
                             1920x1080 [47.57 fps - (680, 692)/1920x1080 crop]
                             3280x2464 [21.19 fps - (0, 0)/3280x2464 crop]
           'SRGGB8' : 640x480 [103.33 fps - (1000, 752)/1280x960 crop]
                      1640x1232 [41.85 fps - (0, 0)/3280x2464 crop]
                      1920x1080 [47.57 fps - (680, 692)/1920x1080 crop]
                      3280x2464 [21.19 fps - (0, 0)/3280x2464 crop]
[{'bit_depth': 10,
  'crop_limits': (1000, 752, 1280, 960),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 103.33,
  'size': (640, 480),
  'unpacked': 'SRGGB10'},
 {'bit_depth': 10,
  'crop_limits': (0, 0, 3280, 2464),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 41.85,
  'size': (1640, 1232),
  'unpacked': 'SRGGB10'},
 {'bit_depth': 10,
  'crop_limits': (680, 692, 1920, 1080),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 47.57,
  'size': (1920, 1080),
  'unpacked': 'SRGGB10'},
 {'bit_depth': 10,
  'crop_limits': (0, 0, 3280, 2464),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 21.19,
  'size': (3280, 2464),
  'unpacked': 'SRGGB10'},
 {'bit_depth': 8,
  'crop_limits': (1000, 752, 1280, 960),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB8,
  'fps': 103.33,
  'size': (640, 480),
  'unpacked': 'SRGGB8'},
 {'bit_depth': 8,
  'crop_limits': (0, 0, 3280, 2464),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB8,
  'fps': 41.85,
  'size': (1640, 1232),
  'unpacked': 'SRGGB8'},
 {'bit_depth': 8,
  'crop_limits': (680, 692, 1920, 1080),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB8,
  'fps': 47.57,
  'size': (1920, 1080),
  'unpacked': 'SRGGB8'},
 {'bit_depth': 8,
  'crop_limits': (0, 0, 3280, 2464),
  'exposure_limits': (75, 11766829, 20000),
  'format': SRGGB8,
  'fps': 21.19,
  'size': (3280, 2464),
  'unpacked': 'SRGGB8'}]


Available cameras
-----------------
0 : imx708 [4608x2592 10-bit RGGB] (/base/soc/i2c0mux/i2c@1/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [30.00 fps - (65535, 65535)/65535x65535 crop]
                             2304x1296 [30.00 fps - (65535, 65535)/65535x65535 crop]
                             4608x2592 [30.00 fps - (65535, 65535)/65535x65535 crop]

len(sensor_modes): 3
[{'bit_depth': 10,
  'crop_limits': (768, 432, 3072, 1728),
  'exposure_limits': (9, 77208145, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 120.13,
  'size': (1536, 864),
  'unpacked': 'SRGGB10'},
 {'bit_depth': 10,
  'crop_limits': (0, 0, 4608, 2592),
  'exposure_limits': (13, 112015096, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 56.03,
  'size': (2304, 1296),
  'unpacked': 'SRGGB10'},
 {'bit_depth': 10,
  'crop_limits': (0, 0, 4608, 2592),
  'exposure_limits': (26, 220416802, 20000),
  'format': SRGGB10_CSI2P,
  'fps': 14.35,
  'size': (4608, 2592),
  'unpacked': 'SRGGB10'}]

camera_controls:
{'AeConstraintMode': (0, 3, 0),
 'AeEnable': (False, True, True),
 'AeExposureMode': (0, 3, 0),
 'AeFlickerMode': (0, 1, 0),
 'AeFlickerPeriod': (100, 1000000, None),
 'AeMeteringMode': (0, 3, 0),
 'AfMetering': (0, 1, 0),
 'AfMode': (0, 2, 0),
 'AfPause': (0, 2, 0),
 'AfRange': (0, 2, 0),
 'AfSpeed': (0, 1, 0),
 'AfTrigger': (0, 1, 0),
 'AfWindows': ((0, 0, 0, 0), (65535, 65535, 65535, 65535), [(0, 0, 0, 0)]),
 'AnalogueGain': (1.1228070259094238, 16.0, 1.0),
 'AnalogueGainMode': (0, 1, 0),
 'AwbEnable': (False, True, None),
 'AwbMode': (0, 7, 0),
 'Brightness': (-1.0, 1.0, 0.0),
 'CnnEnableInputTensor': (False, True, False),
 'ColourCorrectionMatrix': (0.0, 8.0, None),
 'ColourGains': (0.0, 32.0, None),
 'ColourTemperature': (100, 100000, None),
 'Contrast': (0.0, 32.0, 1.0),
 'ExposureTime': (26, 220416802, 20000),
 'ExposureTimeMode': (0, 1, 0),
 'ExposureValue': (-8.0, 8.0, 0.0),
 'FrameDurationLimits': (69669, 220535845, (33333, 33333)),
 'HdrMode': (0, 4, 0),
 'LensPosition': (0.0, 15.0, 1.0),
 'NoiseReductionMode': (0, 4, 0),
 'Saturation': (0.0, 32.0, 1.0),
 'ScalerCrop': ((0, 0, 64, 64), (0, 0, 4608, 2592), (576, 0, 3456, 2592)),
 'Sharpness': (0.0, 16.0, 1.0),
 'StatsOutputEnable': (False, True, False),
 'SyncFrames': (100, 100000, 1000),
 'SyncMode': (0, 2, 0)}


"""

frame_duration = 100000 if not debug else 200000
#frame_duration = 70000 if not debug else 200000
picam2 = Picamera2()


from pprint import pprint
print()

sensor_modes = picam2.sensor_modes
print()
print(f'len(sensor_modes): {len(sensor_modes)}')
print('sensor_modes:')
pprint(sensor_modes)

print()
print('camera_controls:')
pprint(picam2.camera_controls)

print()
print('create_still_configuration: (default)')
pprint(picam2.create_still_configuration())

print()
print('create_preview_configuration: (default)')
pprint(picam2.create_preview_configuration())

print()
print('create_video_configuration: (default)')
pprint(picam2.create_video_configuration())

controls_default = {
    'FrameDurationLimits': (frame_duration, frame_duration),  #  'FrameDurationLimits': (33333, 250000000, (33333, 33333)),
    'AfMode': 2 ,
    'AfTrigger': 0,
    #'LensPosition': 3.0,  #      'LensPosition': (0.0, 15.0, 1.0),

}

controls_dark = {
    'AeEnable': False,  #  'AeEnable': (False, True, True),
    'AwbEnable': False,  #  'AwbEnable': (False, True, None),
    'FrameDurationLimits': (frame_duration, frame_duration),  #  'FrameDurationLimits': (33333, 250000000, (33333, 33333)),
    'ExposureTime': 60000,  #  'ExposureTime': (1, 66666, 20000),
    'AnalogueGain': 16.0,  #  'AnalogueGain': (1.0, 16.0, 1.0),
    'Brightness': 0.0,  #  'Brightness': (-1.0, 1.0, 0.0),
    'Contrast': 1.0,  #  'Contrast': (0.0, 32.0, 1.0),
    'Saturation': 1.0,  #  'Saturation': (0.0, 32.0, 1.0),
}

video_configuration = picam2.create_video_configuration(
    buffer_count=6,

    #main={ 'size': (4608, 2592), 'format': 'BGR888', },
    #main={'size': (3280, 2464), 'format': 'BGR888', },
    main={'size': (2304, 1296),
          'format': 'BGR888',
          #'format': 'XBGR8888',
          },
    #main={'size': (1920, 1080)},
    #main={'size': (1536, 864)},

    lores=None,
    #lores={'size': (2304, 1296)},
    #lores={'size': (1920, 1080)},
    #lores={'size': (1536, 864)},
    #lores={'size': (1280, 960)},
    #lores={'size': (1152, 648)},
    #lores={'size': (640, 480)},
    #lores={'size': (320, 240)},

    #controls=controls_dark,
    controls=controls_default,
)
print()
print('video_configuration:')
pprint(video_configuration)

picam2.configure(video_configuration)

print()
print('camera_configuration():')
pprint(picam2.camera_configuration())
if False:
    print(f'configuration_sensor: {picam2.camera_configuration()["sensor"]}')
    print(f'configuration_raw: {picam2.camera_configuration()["raw"]}')
    print(f'configuration_main: {picam2.camera_configuration()["main"]}')
    print(f'configuration_lores: {picam2.camera_configuration()["lores"]}')

print()
print('camera_config:')
pprint(picam2.camera_config)

if False:
    print()
    print('dir(picam2):')
    pprint(dir(picam2))
    for attr in dir(picam2):
        print()
        print(attr)
        try:
            pprint(getattr(picam2,attr))
        except TypeError:
            pprint(type(getattr(picam2,attr)))

if False:
    pass
    controls={
        'AeEnable': False,  #  'AeEnable': (False, True, True),
        'AwbEnable': False,  #  'AwbEnable': (False, True, None),
        'FrameDurationLimits': (frame_duration, frame_duration),  #  'FrameDurationLimits': (33333, 250000000, (33333, 33333)),
        'ExposureTime': 60000,  #  'ExposureTime': (1, 66666, 20000),
        'AnalogueGain': 1.0,  #  'AnalogueGain': (1.0, 16.0, 1.0),
        'Brightness': 0.2,  #  'Brightness': (-1.0, 1.0, 0.0),
        'Contrast': 1.2,  #  'Contrast': (0.0, 32.0, 1.0),
        'Saturation': 1.5,  #  'Saturation': (0.0, 32.0, 1.0),
    }

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

if use_np:
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

use_res = 'main'
#use_res = 'lores'

def apply_timestamp(request):
  global raw_perspective
  timestamp = time.strftime('%Y-%m-%d-%H%M-%S')
  with MappedArray(request, use_res) as cvstuff:
    debug and print(f'cvstuff.array: shape: {cvstuff.array.shape}, dtype: {cvstuff.array.dtype}, strides: {cvstuff.array.strides}')
    if use_res == 'main':
        bgr = cvstuff.array
    elif use_res == 'lores':
        bgr = cv2.cvtColor(cvstuff.array, cv2.COLOR_YUV420p2RGB)
    else:
        assert False, 'unreachable'

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

    if use_res == 'main':
        yuv = normed
    elif use_res == 'lores':
        yuv = cv2.cvtColor(normed, cv2.COLOR_BGR2YUV_I420)
    else:
        assert False, 'unreachable'

    #yuv = cv2.cvtColor(unwarped, cv2.COLOR_BGR2YUV_I420)
    #yuv = cv2.cvtColor(unwarped, cv2.COLOR_RGB2YUV_I420)
    debug and print(f'yuv: shape: {yuv.shape}, dtype: {yuv.dtype}, strides: {yuv.strides}')

    if yuv is not cvstuff.array:
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
    server = ThreadedReuseServer(address, StreamingHandler)
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
