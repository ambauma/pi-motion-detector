"""Test main.py"""
import io
import logging
import random
import os
import signal
import time
import threading
import pytest
from mockito import expect, mock, unstub, any_, patch
from picamera import PiCamera
import numpy as np
from numpy.random import SeedSequence, default_rng
from py_motion_detector import main as sut
from py_motion_detector import Watcher


@pytest.fixture(name="first_image", scope="module")
def generate_first_image():
    rng = default_rng(12345)
    ints = rng.integers(low=0, high=255, size=1440 * 1088 * 4)
    yield np.array(ints).tobytes()

@pytest.fixture(name="second_image", scope="module")
def generate_second_image():
    rng = default_rng(11111)
    ints = rng.integers(low=0, high=255, size=1440 * 1088 * 4)
    yield np.array(ints).tobytes()

def test_watcher_no_changes(unstub, caplog, first_image):
    """Test watching when nothing changes."""
    mock_camera = mock(PiCamera, strict=True)
    mock_bytes0 = mock(io.BytesIO, strict=True)
    mock_bytes1 = mock(io.BytesIO, strict=True)

    expect(sut, times=1).PiCamera().thenReturn(mock_camera)
    expect(sut.io, times=2).BytesIO().thenReturn(mock_bytes0, mock_bytes1)
    expect(mock_camera, times=1).capture(mock_bytes0, "rgba", True)
    expect(mock_camera, times=1).capture(mock_bytes1, "rgba", True)
    second_image = first_image
    expect(mock_bytes0).getvalue().thenReturn(first_image)
    expect(mock_bytes1).getvalue().thenReturn(second_image)
    expect(mock_camera, times=1).close()
    logger = "py_motion_detector.main"
    with caplog.at_level(logging.DEBUG, logger=logger):
        with Watcher() as watcher:
            watcher.watch()
            watcher.watch()
    logs = caplog.record_tuples
    assert len(logs) == 7
    assert logs[0] == (logger, logging.DEBUG, "Initializing...")
    assert logs[1] == (logger, logging.DEBUG, "Setting resolution to 1440, 1088")
    assert logs[2] == (logger, logging.DEBUG, "Capturing test image.")
    assert logs[3] == (logger, logging.DEBUG, "Setting resolution to 1440, 1088")
    assert logs[4] == (logger, logging.DEBUG, "Capturing test image.")
    assert logs[5] == (logger, logging.DEBUG, "Pixels Changed: 0, minimum: 31334.4")
    assert logs[6] == (logger, logging.DEBUG, "Closing camera...")


def test_watcher_with_changes(unstub, caplog, first_image, second_image):
    """Test watching with significant changes."""
    mock_camera = mock(PiCamera, strict=True)
    mock_bytes0 = mock(io.BytesIO, strict=True)
    mock_bytes1 = mock(io.BytesIO, strict=True)

    expect(sut, times=1).PiCamera().thenReturn(mock_camera)
    expect(sut.io, times=2).BytesIO().thenReturn(mock_bytes0, mock_bytes1)
    expect(mock_camera, times=1).capture(mock_bytes0, "rgba", True)
    expect(mock_camera, times=1).capture(mock_bytes1, "rgba", True)
    expect(mock_bytes0).getvalue().thenReturn(first_image)
    expect(mock_bytes1).getvalue().thenReturn(second_image)
    expect(mock_camera).capture(any_(str))
    expect(mock_camera, times=1).close()
    logger = "py_motion_detector.main"
    with caplog.at_level(logging.DEBUG, logger=logger):
        with Watcher() as watcher:
            watcher.watch()
            watcher.watch()
    logs = caplog.record_tuples
    assert len(logs) == 9
    assert logs[0] == (logger, logging.DEBUG, "Initializing...")
    assert logs[1] == (logger, logging.DEBUG, "Setting resolution to 1440, 1088")
    assert logs[2] == (logger, logging.DEBUG, "Capturing test image.")
    assert logs[3] == (logger, logging.DEBUG, "Setting resolution to 1440, 1088")
    assert logs[4] == (logger, logging.DEBUG, "Capturing test image.")
    assert logs[5] == (logger, logging.DEBUG, "Pixels Changed: 45897, minimum: 31334.4")
    assert logs[6] == (logger, logging.DEBUG, "Setting resolution to 2592, 1944")
    assert logs[7][0] == logger
    assert logs[7][1] == logging.INFO
    assert logs[7][2].startswith("Triggering capture")
    assert logs[8] == (logger, logging.DEBUG, "Closing camera...")


def test_watcher_sigint(unstub, caplog, first_image, second_image):
    """Test the watcher sigint behavior."""
    pid = os.getpid()

    def trigger_signal():
        time.sleep(2)
        logging.info("Killing pid %s", pid)
        os.kill(pid, signal.SIGINT)
    
    thread = threading.Thread(target=trigger_signal)
    thread.daemon = True
    thread.start()

    mock_camera = mock(PiCamera, strict=True)
    mock_bytes0 = mock(io.BytesIO, strict=True)
    mock_bytes1 = mock(io.BytesIO, strict=True)

    expect(sut).PiCamera().thenReturn(mock_camera)
    expect(sut.io).BytesIO().thenReturn(mock_bytes0, mock_bytes1)
    expect(mock_camera).capture(mock_bytes0, "rgba", True)
    expect(mock_camera).capture(mock_bytes1, "rgba", True)
    second_image = first_image
    expect(mock_bytes0).getvalue().thenReturn(first_image)
    expect(mock_bytes1).getvalue().thenReturn(second_image)
    expect(mock_camera).close()
    with Watcher() as watcher:
        while watcher.continue_looping:
            watcher.watch()
    assert watcher.continue_looping is False
