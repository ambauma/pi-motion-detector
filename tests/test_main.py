"""Test main.py"""
import io
import logging
from mockito import expect, mock, unstub, any_, patch
from picamera import PiCamera
from py_motion_detector import main as sut
from py_motion_detector import Watcher

def test_watcher(unstub, caplog):
    """Test watching."""
    mock_camera = mock(PiCamera, strict=True)
    mock_bytes1 = mock(io.By)

    expect(sut, times=1).PiCamera().thenReturn(mock_camera)
    expect(mock_camera, times=1).capture(any_(io.BytesIO), "rgba", True)
    expect(mock_camera, times=1).close()
    logger = "py_motion_detector.main"
    with caplog.at_level(logging.DEBUG, logger=logger):
        with Watcher() as watcher:
            watcher.watch()
    logs = caplog.record_tuples
    print(f"logs: {logs}")
    assert logs[0] == (logger, logging.DEBUG, "Initializing...")
    assert logs[1] == (logger, logging.DEBUG, "Setting resolution to 1440, 1088")
    assert logs[2] == (logger, logging.DEBUG, "Capturing test image.")
    assert logs[3] == (logger, logging.DEBUG, "Closing camera...")