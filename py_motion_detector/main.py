"""Main module."""
from datetime import datetime
import io
import logging
import signal
import time
import numpy as np
from picamera import PiCamera


logger = logging.getLogger(__name__)

class Watcher:
    """Class to watch for movement."""

    def __init__(self):
        """Initialize the object."""
        logger.debug("Initializing...")
        self.continue_looping = True
        self.streams = []
        self.camera = None
        self.threshold = 30
        self.test_width = 1440
        self.test_height = 1088
        self.capture_width = 2592
        self.capture_height = 1944
        self.minimum_pixels_changed = self.test_width * self.test_height * 2 / 100

        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, _1=None, _2=None):
        logger.info("Shutting down...")
        self.continue_looping = False

    def __enter__(self):
        """Initialize the camera."""
        self.camera = PiCamera()
        time.sleep(1)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Close the camera."""
        logger.debug("Closing camera...")
        self.camera.close()

    def capture(self):
        """Capture a high-res image."""
        logger.debug("Setting resolution to %s, %s", self.capture_width, self.capture_height)
        self.camera.resolution = (self.capture_width, self.capture_height)
        filename = datetime.now().strftime("capture%Y%m%d%H%M%S.jpg")
        logger.info("Triggering capture %s", filename)
        self.camera.capture(filename)

    def compare(self):
        """Compare low res images for differences."""
        if len(self.streams) == 2:
            data0 = np.frombuffer(self.streams[0].getvalue(), dtype=np.uint8)
            data1 = np.frombuffer(self.streams[1].getvalue(), dtype=np.uint8)
            difference = np.abs(data0 - data1)
            num_triggers = (
                np.count_nonzero(difference > self.threshold) / 4 / self.threshold
            )
            logger.debug(
                "Pixels Changed: %s, minimum: %s",
                int(num_triggers),
                self.minimum_pixels_changed,
            )
            if num_triggers > self.minimum_pixels_changed:
                self.capture()

    def watch(self):
        """Watch for movement."""
        logger.debug("Setting resolution to %s, %s", self.test_width, self.test_height)
        self.camera.resolution = (self.test_width, self.test_height)
        if len(self.streams) == 2:
            logger.debug("Removing oldest image.")
            self.streams.pop(0)
        new_img = io.BytesIO()
        logger.debug("Capturing test image.")
        self.camera.capture(new_img, "rgba", True)  # use video port for high speed
        self.streams.append(new_img)
        self.compare()
