"""Test cli.py"""
import logging
import pytest
from mockito import expect, patch, mock, unstub, any_
from py_motion_detector import cli as sut

def test_get_args():
    """Test get_args."""
    args = sut.get_args()
    assert args

def test_init(unstub):
    """Test the init function."""
    mock_watcher = mock(sut.Watcher, strict=True)
    setattr(mock_watcher, "continue_looping", True)
    def stop_looping():
        mock_watcher.continue_looping = False
    setattr(mock_watcher, "watch", stop_looping)
    expect(sut).get_args().thenReturn([])
    expect(sut.logging).basicConfig(level=logging.INFO)
    expect(sut).Watcher().thenReturn(mock_watcher)
    expect(mock_watcher).__enter__().thenReturn(mock_watcher)
    expect(mock_watcher).__exit__(any_(), any_(), any_())
    sut.init()