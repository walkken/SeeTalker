import io
import picamera
import logging

from threading import Condition
from Thread import Timer


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)
    
    
def cam_StartLiveCamera ():
    
    camera = picamera.PiCamera(resolution='640x480', framerate=24)

    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    camera.rotation = 270
    print ("start recording")
    camera.start_recording(output, format='mjpeg')
    
    camera.rotation = 90
    camera.vflip = 1
        
    return(camera, output)
