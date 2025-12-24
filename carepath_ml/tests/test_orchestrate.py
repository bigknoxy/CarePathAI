#!/usr/bin/env python3
"""Unit tests for orchestrate endpoint."""

import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
import numpy as np

# Import the orchestrate router
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from endpoints.orchestrate import (
    router,
    get_api_base_url,
    fetch_patient_from_csharp_api,
    perform_retrieval,
    perform_faiss_retrieval,
    call_retrieve_endpoint,
)


class TestOrchestrateEndpoint:
    """Test cases for the orchestrate endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        # Mock model and index
        self.mock_model = Mock()
        self.mock_index = Mock()
        self.mock_metadata = [
            {"text": "Document 1", "id": 1},
            {"text": "Document 2", "id": 2},
        ]
        self.mock_query_embedding = np.array([[0.1, 0.2, 0.3]])
        self.mock_distances = np.array([[0.5, 0.7]])
        self.mock_indices = np.array([[0, 1]])

        self.mock_model.encode.return_value = self.mock_query_embedding
        self.mock_index.search.return_value = (self.mock_distances, self.mock_indices)

        # Set up app state
        self.app.state.model = self.mock_model
        self.app.state.index = self.mock_index
        self.app.state.metadata = self.mock_metadata

    def test_get_api_base_url_default(self):
        """Test get_api_base_url with default value."""
        # Clear environment variable
        if "API_BASE_URL" in os.environ:
            del os.environ["API_BASE_URL"]

        result = get_api_base_url()
        assert result == "http://localhost:5000"

    def test_get_api_base_url_env_var(self):
        """Test get_api_base_url with environment variable."""
        os.environ["API_BASE_URL"] = "http://api:5000"
        try:
            result = get_api_base_url()
            assert result == "http://api:5000"
        finally:
            del os.environ["API_BASE_URL"]

    @pytest.mark.asyncio
    async def test_fetch_patient_success(self):
        """Test successful patient fetch from C# API."""
        mock_patient_data = {
            "id": 123,
            "firstName": "John",
            "lastName": "Doe",
            "dateOfBirth": "1980-01-01",
            "medicalRecordNumber": "MRN123",
            "conditions": ["Hypertension"],
            "notes": "Patient has high blood pressure",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_patient_data
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await fetch_patient_from_csharp_api(123)
            assert result == mock_patient_data

    @pytest.mark.asyncio
    async def test_fetch_patient_not_found(self):
        """Test patient fetch when patient not found."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            with pytest.raises(RuntimeError, match="Patient 123 not found"):
                await fetch_patient_from_csharp_api(123)

    @pytest.mark.asyncio
    async def test_fetch_patient_api_error(self):
        """Test patient fetch when C# API returns error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            with pytest.raises(RuntimeError, match="C# API error: 500"):
                await fetch_patient_from_csharp_api(123)

    @pytest.mark.asyncio
    async def test_fetch_patient_timeout(self):
        """Test patient fetch when C# API times out."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = patch(
                "httpx.TimeoutException"
            )

            with pytest.raises(RuntimeError, match="Timeout fetching patient"):
                await fetch_patient_from_csharp_api(123)

    @pytest.mark.asyncio
    async def test_perform_faiss_retrieval_success(self):
        """Test successful FAISS retrieval."""
        mock_patient_data = {
            "notes": "Test patient notes",
            "conditions": ["Condition1"],
        }

        with patch(
            "endpoints.orchestrate.fetch_patient_from_csharp_api",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_patient_data

            # Create a mock request object
            request = Mock()
            request.app.state.model = self.mock_model
            request.app.state.index = self.mock_index
            request.app.state.metadata = self.mock_metadata

            results = await perform_faiss_retrieval(123, 5, request)

            assert len(results) == 2
            assert results[0].id == 0
            assert results[0].score == 0.5
            assert results[0].text == "Document 1"

    @pytest.mark.asyncio
    async def test_perform_retrieval_with_index(self):
        """Test perform_retrieval when index is available."""
        request = Mock()
        request.app.state.index = self.mock_index

        with patch(
            "endpoints.orchestrate.perform_faiss_retrieval", new_callable=AsyncMock
        ) as mock_faiss:
            mock_faiss.return_value = []

            results = await perform_retrieval(123, 5, request)
            mock_faiss.assert_called_once_with(123, 5, request)

    @pytest.mark.asyncio
    async def test_perform_retrieval_fallback(self):
        """Test perform_retrieval when index is not available."""
        request = Mock()
        request.app.state.index = None

        with patch(
            "endpoints.orchestrate.call_retrieve_endpoint", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = []

            results = await perform_retrieval(123, 5, request)
            mock_call.assert_called_once_with(123, 5, request)

    def test_orchestrate_endpoint_success(self):
        """Test successful orchestrate endpoint call."""
        mock_patient_data = {
            "id": 123,
            "firstName": "John",
            "lastName": "Doe",
            "dateOfBirth": "1980-01-01",
            "medicalRecordNumber": "MRN123",
            "conditions": ["Hypertension"],
            "notes": "Patient has high blood pressure",
        }

        with (
            patch(
                "endpoints.orchestrate.fetch_patient_from_csharp_api",
                new_callable=AsyncMock,
            ) as mock_fetch,
            patch(
                "endpoints.orchestrate.perform_retrieval", new_callable=AsyncMock
            ) as mock_retrieve,
        ):
            mock_fetch.return_value = mock_patient_data
            mock_retrieve.return_value = []

            response = self.client.post(
                "/api/v1/orchestrate", json={"patient_id": 123, "top_k": 5}
            )

            assert response.status_code == 200
            data = response.json()
            assert "patient" in data
            assert "retrieved" in data
            assert data["patient"]["id"] == 123

    def test_orchestrate_endpoint_missing_patient_id(self):
        """Test orchestrate endpoint with missing patient_id."""
        response = self.client.post("/api/v1/orchestrate", json={"top_k": 5})

        assert response.status_code == 422  # Validation error

    def test_orchestrate_endpoint_invalid_patient_id(self):
        """Test orchestrate endpoint with invalid patient_id."""
        response = self.client.post(
            "/api/v1/orchestrate", json={"patient_id": 0, "top_k": 5}
        )

        assert response.status_code == 422  # Validation error

    def test_orchestrate_endpoint_invalid_top_k(self):
        """Test orchestrate endpoint with invalid top_k."""
        response = self.client.post(
            "/api/v1/orchestrate", json={"patient_id": 123, "top_k": 0}
        )

        assert response.status_code == 422  # Validation error

    def test_orchestrate_endpoint_patient_not_found(self):
        """Test orchestrate endpoint when patient not found."""
        with patch(
            "endpoints.orchestrate.fetch_patient_from_csharp_api",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.side_effect = RuntimeError("Patient 123 not found")

            response = self.client.post(
                "/api/v1/orchestrate", json={"patient_id": 123, "top_k": 5}
            )

            assert response.status_code == 404
            data = response.json()
            # Handle nested FastAPI error format
            if "detail" in data and isinstance(data["detail"], dict):
                error_msg = data["detail"].get("error", "")
            else:
                error_msg = data.get("error", "")
            assert "not found" in error_msg

    def test_orchestrate_endpoint_downstream_error(self):
        """Test orchestrate endpoint when C# API has downstream error."""
        with patch(
            "endpoints.orchestrate.fetch_patient_from_csharp_api",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.side_effect = RuntimeError("C# API error: 500")

            response = self.client.post(
                "/api/v1/orchestrate", json={"patient_id": 123, "top_k": 5}
            )

            assert response.status_code == 502
            data = response.json()
            error_msg = data.get("error", data.get("detail", ""))
            assert "Downstream service error" in error_msg

    def test_orchestrate_endpoint_default_values(self):
        """Test orchestrate endpoint with default values."""
        mock_patient_data = {"id": 123, "firstName": "John", "lastName": "Doe"}

        with (
            patch(
                "endpoints.orchestrate.fetch_patient_from_csharp_api",
                new_callable=AsyncMock,
            ) as mock_fetch,
            patch(
                "endpoints.orchestrate.perform_retrieval", new_callable=AsyncMock
            ) as mock_retrieve,
        ):
            mock_fetch.return_value = mock_patient_data
            mock_retrieve.return_value = []

            # Only provide patient_id, should use default top_k=5
            response = self.client.post("/api/v1/orchestrate", json={"patient_id": 123})

            assert response.status_code == 200
            # Check that perform_retrieval was called with correct args
            mock_retrieve.assert_called_once()
            call_args = mock_retrieve.call_args[0]
            assert call_args[0] == 123  # patient_id
            assert call_args[1] == 5  # top_k

    def test_orchestrate_endpoint_flexible_patient_mapping(self):
        """Test orchestrate endpoint with flexible patient field mapping."""
        # Test with underscore naming convention
        mock_patient_data = {
            "id": 123,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-01",
            "mrn": "MRN123",
            "conditions": ["Hypertension"],
            "notes": "Patient notes",
        }

        with (
            patch(
                "endpoints.orchestrate.fetch_patient_from_csharp_api",
                new_callable=AsyncMock,
            ) as mock_fetch,
            patch(
                "endpoints.orchestrate.perform_retrieval", new_callable=AsyncMock
            ) as mock_retrieve,
        ):
            mock_fetch.return_value = mock_patient_data
            mock_retrieve.return_value = []

            response = self.client.post(
                "/api/v1/orchestrate", json={"patient_id": 123, "top_k": 5}
            )

            assert response.status_code == 200
            data = response.json()
            patient = data["patient"]
            assert patient["firstName"] == "John"
            assert patient["lastName"] == "Doe"


if __name__ == "__main__":
    pytest.main([__file__])
