"""
Unit tests for retry decorator
"""
import pytest
from unittest.mock import MagicMock, call

from core.retry import retry


class TestRetryDecorator:
    """Tests for retry decorator."""
    
    def test_successful_first_attempt(self):
        """Test function succeeds on first attempt."""
        mock_func = MagicMock(return_value="success")
        
        @retry(max_attempts=3, delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_failure(self):
        """Test function retries on failure."""
        mock_func = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        @retry(max_attempts=3, delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test exception raised when max retries exceeded."""
        mock_func = MagicMock(side_effect=Exception("always fails"))
        
        @retry(max_attempts=3, delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception, match="always fails"):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_specific_exception_handling(self):
        """Test retry only catches specified exceptions."""
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def test_func():
            raise TypeError("not caught")
        
        with pytest.raises(TypeError):
            test_func()
    
    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        callback = MagicMock()
        
        @retry(max_attempts=3, delay=0.01, on_retry=callback)
        def test_func():
            raise Exception("fail")
        
        with pytest.raises(Exception):
            test_func()
        
        assert callback.call_count == 2  # Called on 1st and 2nd retry
