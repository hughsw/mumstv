from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

"""
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
"""

class CameraControls(BaseModel):

    AeConstraintMode: int = 0  # (0, 3, 0)
    AeEnable: bool = True  # (False, True, True)

    AeExposureMode: int = 0  # (0, 3, 0)
    AeFlickerMode: int = 0  # (0, 1, 0)
    AeFlickerPeriod: int | None = None  # (100, 1000000, None)
    #AeFlickerPeriod: Optional[int] = None  # = None  # (100, 1000000, None)
    AeMeteringMode: int = 0  # (0, 3, 0)
    AfMetering: int = 0  # (0, 1, 0)
    AfMode: int = 0  # (0, 2, 0)
    AfPause: int = 0  # (0, 2, 0)
    AfRange: int = 0  # (0, 2, 0)
    AfSpeed: int = 0  # (0, 1, 0)
    AfTrigger: int = 0  # (0, 1, 0)

    AfWindows: list = [(0, 0, 0, 0)]  # ((0, 0, 0, 0), (65535, 65535, 65535, 65535), [(0, 0, 0, 0)])
    AnalogueGain: float = 1.0  # (1.1228070259094238, 16.0, 1.0)
    AnalogueGainMode: int = 0  # (0, 1, 0)
    AwbEnable: bool = None  # (False, True, None)
    AwbMode: int = 0  # (0, 7, 0)
    Brightness: float = 0.0  # (-1.0, 1.0, 0.0)
    CnnEnableInputTensor: bool = False  # (False, True, False)
    ColourCorrectionMatrix: float | None = None  # (0.0, 8.0, None)
    ColourGains: float | None = None  # (0.0, 32.0, None)
    ColourTemperature: int | None = None  # (100, 100000, None)
    Contrast: float = 1.0  # (0.0, 32.0, 1.0)
    ExposureTime: int = 20000  # (26, 220416802, 20000)
    ExposureTimeMode: int = 0  # (0, 1, 0)
    ExposureValue: float = 0.0  # (-8.0, 8.0, 0.0)
    FrameDurationLimits: tuple = (33333, 33333)  # (69669, 220535845, (33333, 33333))
    HdrMode: int = 0  # (0, 4, 0)
    LensPosition: float = 1.0  # (0.0, 15.0, 1.0)
    NoiseReductionMode: int = 0  # (0, 4, 0)
    Saturation: float = 1.0  # (0.0, 32.0, 1.0)
    ScalerCrop: tuple = (576, 0, 3456, 2592)  # ((0, 0, 64, 64), (0, 0, 4608, 2592), (576, 0, 3456, 2592))
    Sharpness: float = 1.0  # (0.0, 16.0, 1.0)
    StatsOutputEnable: bool = False  # (False, True, False)
    SyncFrames: int = 1000  # (100, 100000, 1000)
    SyncMode: int = 0  # (0, 2, 0)



@app.get('/')
async def root():
    return {
        'message': 'Hello World !!',
    }

@app.post('/camera')
async def post_camera(controls: CameraControls):
    return {
        'controls': controls,
    }
