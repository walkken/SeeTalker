import threading 
import time


def al_StartAlertTriggers (interval_secs, AlertHandler, fRepeat=True):
    if fRepeat: # repeat timer
        tmr = RepeatedTimer(interval_secs, AlertHandler)
    else:  # one-time timer
        tmr = threading.Timer(interval_secs, AlertHandler)
        tmr.start() # start the timer
          
    return (tmr)
    
    
def al_CancelAlertTriggers (tmr):
    #tmr.cancel()
    tmr.stop()


def CheckAlertTriggers ():
    print ("Check Alert Triggers")
    return (True)


class RepeatedTimer(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False