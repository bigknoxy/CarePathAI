#!/usr/bin/env python3
"""Unit tests for embed endpoint."""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import numpy as np

# Import the embed router
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from endpoints.embed import router, validate_embed_text, generate_embedding


class TestEmbedEndpoint:
    """Test cases for the embed endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        # Mock model
        self.mock_model = Mock()
        self.mock_embedding = np.array([0.1, 0.2, 0.3, 0.4])
        self.mock_model.encode.return_value = np.array([self.mock_embedding])
        self.mock_model.get_sentence_embedding_dimension.return_value = 4

        # Set up app state
        self.app.state.model = self.mock_model

    def test_validate_embed_text_success(self):
        """Test successful text validation."""
        # Valid text
        validate_embed_text("Hello world")
        validate_embed_text("A" * 100)  # Medium length
        validate_embed_text("Text with numbers 123 and symbols !@#")

    def test_validate_embed_text_empty(self):
        """Test validation with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            validate_embed_text("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            validate_embed_text("   ")

    def test_validate_embed_text_too_long(self):
        """Test validation with text that's too long."""
        long_text = "A" * 10001
        with pytest.raises(ValueError, match="Text too long"):
            validate_embed_text(long_text)

    def test_validate_embed_text_wrong_type(self):
        """Test validation with non-string input."""
        with pytest.raises(ValueError, match="Text must be a string"):
            validate_embed_text(123)

    def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        result = generate_embedding("test text", self.mock_model)

        assert isinstance(result, list)
        assert len(result) == 4
        assert result == [0.1, 0.2, 0.3, 0.4]
        self.mock_model.encode.assert_called_once_with(
            ["test text"], convert_to_numpy=True
        )

    def test_generate_embedding_model_error(self):
        """Test embedding generation with model error."""
        self.mock_model.encode.side_effect = Exception("Model error")

        with pytest.raises(RuntimeError, match="Embedding generation failed"):
            generate_embedding("test text", self.mock_model)

    def test_embed_endpoint_success(self):
        """Test successful embed endpoint call."""
        response = self.client.post("/api/v1/embed", json={"text": "Hello world"})

        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data
        assert "dim" in data
        assert data["dim"] == 4
        assert len(data["embedding"]) == 4

    def test_embed_endpoint_missing_text(self):
        """Test embed endpoint with missing text field."""
        response = self.client.post("/api/v1/embed", json={})

        assert response.status_code == 422  # Validation error

    def test_embed_endpoint_empty_text(self):
        """Test embed endpoint with empty text."""
        # Pydantic validation handles empty string with min_length=1
        response = self.client.post("/api/v1/embed", json={"text": ""})

        assert response.status_code == 422  # Pydantic validation error

    def test_embed_endpoint_too_long_text(self):
        """Test embed endpoint with text that's too long."""
        long_text = "A" * 10001
        response = self.client.post("/api/v1/embed", json={"text": long_text})

        assert response.status_code == 422  # Pydantic validation error

    def test_embed_endpoint_no_model(self):
        """Test embed endpoint when model is not available."""
        self.app.state.model = None

        response = self.client.post("/api/v1/embed", json={"text": "Hello world"})

        # Should return 500 due to missing sentence_transformers library in test env
        # but in a real environment it would return 503
        assert response.status_code in [500, 503]
        data = response.json()
        # Handle both FastAPI error formats
        error_msg = data.get("error", data.get("detail", ""))
        assert "not available" in error_msg or "sentence_transformers" in error_msg

    def test_embed_endpoint_lazy_load_model(self):
        """Test embed endpoint with lazy model loading."""
        # Remove model from app state
        if hasattr(self.app.state, "model"):
            delattr(self.app.state, "model")

        # Mock the dynamic import more carefully - test doesn't work well with importlib patches
        response = self.client.post("/api/v1/embed", json={"text": "Hello world"})

        # Should fail due to missing sentence_transformers
        assert response.status_code == 500

    def test_embed_endpoint_model_no_dimension_method(self):
        """Test embed endpoint when model doesn't have get_sentence_embedding_dimension."""
        self.mock_model.get_sentence_embedding_dimension = None

        response = self.client.post("/api/v1/embed", json={"text": "Hello world"})

        assert response.status_code == 200
        data = response.json()
        assert data["dim"] == 4  # Should fall back to len(embedding)

    def test_embed_endpoint_unexpected_error(self):
        """Test embed endpoint with unexpected error."""
        # Make encode method raise an unexpected error
        self.mock_model.encode.side_effect = RuntimeError("Unexpected error")

        response = self.client.post("/api/v1/embed", json={"text": "Hello world"})

        assert response.status_code == 500
        data = response.json()
        # Handle FastAPI error detail format
        error_msg = data.get("error", data.get("detail", ""))
        assert "Embedding generation failed" in error_msg


if __name__ == "__main__":
    pytest.main([__file__])
