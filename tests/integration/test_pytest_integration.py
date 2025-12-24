"""
Integration tests for CarePathAI using pytest framework.

Run with: python -m pytest tests/integration/test_pytest_integration.py -v
"""

import urllib.request
import urllib.error
import json
import os
import time
import pytest


# Configuration
ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
DEFAULT_TIMEOUT = 30

pytestmark = pytest.mark.integration


def make_request(
    url: str, method: str = "GET", data: dict = None, headers: dict = None
):
    """Make HTTP request and return response data."""
    if headers is None:
        headers = {"Content-Type": "application/json"}

    req_data = None
    if data and method in ["POST", "PUT"]:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Length"] = str(len(req_data))

    try:
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            response_data = response.read().decode("utf-8")

            # Try to parse as JSON
            try:
                return json.loads(response_data), response.status
            except json.JSONDecodeError:
                return {"text": response_data}, response.status

    except urllib.error.HTTPError as e:
        try:
            error_data = e.read().decode("utf-8")
            return json.loads(error_data), e.code
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"error": f"HTTP {e.code}: {e.reason}"}, e.code
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {str(e)}"}, 0
    except Exception as e:
        return {"error": f"Request error: {str(e)}"}, 0


class TestMLServiceHealth:
    """Test ML service health endpoints."""

    def test_basic_health(self):
        """Test basic health endpoint."""
        data, status = make_request(f"{ML_BASE_URL}/health")

        assert status == 200, f"Expected 200, got {status}. Response: {data}"
        assert data.get("status") == "ok"
        assert isinstance(data, dict)

    def test_detailed_health(self):
        """Test detailed health endpoint with system state."""
        data, status = make_request(f"{ML_BASE_URL}/health/detailed")

        assert status == 200, f"Expected 200, got {status}. Response: {data}"

        # Verify structure
        required_fields = ["status", "service", "version", "indices", "model", "paths"]
        for field in required_fields:
            assert field in data, f"Missing field in health response: {field}"

        assert data["status"] == "ok"
        assert data["service"] == "CarePath ML Service"

        # Verify indices info
        indices = data["indices"]
        assert "faiss_available" in indices
        assert "metadata_count" in indices
        assert "mock_index_available" in indices
        assert isinstance(indices["metadata_count"], int)

        # Verify model info
        model = data["model"]
        assert "name" in model
        assert "loaded" in model


class TestMLRetrieveEndpoint:
    """Test ML retrieval endpoints."""

    def test_retrieve_basic(self):
        """Test basic retrieval functionality."""
        data, status = make_request(
            f"{ML_BASE_URL}/retrieve",
            method="POST",
            data={"query": "diabetes", "top_k": 3},
        )

        assert status == 200, f"Expected 200, got {status}. Response: {data}"

        # Verify response structure
        assert "results" in data
        results = data["results"]
        assert isinstance(results, list)
        assert len(results) <= 3  # Should respect top_k

    def test_retrieve_with_top_k(self):
        """Test retrieval with specific top_k parameter."""
        top_k = 5
        data, status = make_request(
            f"{ML_BASE_URL}/retrieve",
            method="POST",
            data={"query": "diabetes", "top_k": top_k},
        )

        assert status == 200, f"Expected 200, got {status}. Response: {data}"
        results = data["results"]

        assert len(results) <= top_k

    def test_retrieve_result_structure(self):
        """Test that retrieval results have expected structure."""
        data, status = make_request(
            f"{ML_BASE_URL}/retrieve",
            method="POST",
            data={"query": "diabetes", "top_k": 3},
        )

        assert status == 200, f"Expected 200, got {status}. Response: {data}"
        results = data["results"]

        if results:  # If any results returned
            for result in results[:1]:  # Check first result
                assert isinstance(result, dict)
                # Check for common fields (may vary by implementation)
                expected_fields = ["id", "score"]
                for field in expected_fields:
                    if field in result:
                        assert result[field] is not None

    def test_retrieve_empty_query(self):
        """Test retrieval behavior with empty query."""
        data, status = make_request(
            f"{ML_BASE_URL}/retrieve", method="POST", data={"query": "", "top_k": 3}
        )

        # Should handle empty query gracefully
        assert status in [200, 400], f"Unexpected status {status}: {data}"
        if status == 200:
            assert "results" in data


class TestMLEmbedEndpoint:
    """Test ML embedding endpoint - may not be available in basic service."""

    def test_embed_endpoint_availability(self):
        """Check if embed endpoint is available (may not exist in basic service)."""
        data, status = make_request(
            f"{ML_BASE_URL}/api/v1/embed",
            method="POST",
            data={"text": "test patient with diabetes"},
        )
        # If endpoint exists, it should return 200 or proper error
        assert status in [200, 404, 501], f"Unexpected status {status}: {data}"

    @pytest.mark.skip(
        reason="Embed endpoint not available in current basic service implementation"
    )
    def test_embed_single_text(self):
        """Test embedding generation for single text."""
        data, status = make_request(
            f"{ML_BASE_URL}/api/v1/embed",
            method="POST",
            data={"text": "test patient with diabetes"},
        )

        assert status == 200
        # Verify embedding structure
        assert "embeddings" in data or "embedding" in data
        embeddings = data.get("embeddings", [data.get("embedding")])
        assert len(embeddings) == 1

        embedding = embeddings[0]
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # Expected embedding dimension
        assert all(isinstance(x, (float, int)) for x in embedding)


class TestMLOrchestrateEndpoint:
    """Test ML orchestrate endpoint - may not be available in basic service."""

    def test_orchestrate_endpoint_availability(self):
        """Check if orchestrate endpoint is available."""
        data, status = make_request(
            f"{ML_BASE_URL}/api/v1/orchestrate",
            method="POST",
            data={"patient_id": 1, "top_k": 3},
        )
        # If endpoint exists, it should return 200 or proper error
        assert status in [200, 404, 501], f"Unexpected status {status}: {data}"

    @pytest.mark.skip(
        reason="Orchestrate endpoint not available in current basic service implementation"
    )
    def test_orchestrate_patient_flow(self):
        """Test full orchestration flow with patient data."""
        data, status = make_request(
            f"{ML_BASE_URL}/api/v1/orchestrate",
            method="POST",
            data={
                "patient_id": 37,
                "top_k": 3,
            },  # Use known patient ID from synthetic data
        )

        assert status == 200
        # Verify orchestration response structure
        assert "patient" in data
        assert "retrieved" in data
        assert "summary" in data

        # Check patient data structure
        patient = data["patient"]
        assert "id" in patient
        assert "firstName" in patient or "first_name" in patient
        assert "lastName" in patient or "last_name" in patient

        # Check retrieved results
        retrieved = data["retrieved"]
        assert isinstance(retrieved, list)
        assert len(retrieved) <= 3  # Should respect top_k

        # Check summary
        summary = data["summary"]
        assert "summary_text" in summary or "text" in summary


class TestAPIServiceHealth:
    """Test C# API service health endpoints."""

    def test_api_health(self):
        """Test API health endpoint."""
        data, status = make_request(f"{API_BASE_URL}/health")

        assert status == 200, f"Expected 200, got {status}. Response: {data}"
        assert data.get("status") == "ok"
        assert isinstance(data, dict)


class TestAPIPatientEndpoints:
    """Test C# API patient endpoints."""

    def test_get_all_patients(self):
        """Test getting all patients."""
        data, status = make_request(f"{API_BASE_URL}/api/patients")

        assert status == 200, f"Expected 200, got {status}. Response: {data}"
        assert isinstance(data, list)

        # If patients exist, verify structure
        if data:
            for patient in data[:1]:  # Check first patient
                assert isinstance(patient, dict)
                expected_fields = ["id", "firstName", "lastName"]
                for field in expected_fields:
                    if field in patient:
                        assert patient[field] is not None

    def test_get_specific_patient_not_found(self):
        """Test getting specific patient that doesn't exist."""
        data, status = make_request(f"{API_BASE_URL}/api/patients/99999")

        # Should return 404 for non-existent patient
        assert status == 404, f"Expected 404, got {status}. Response: {data}"

    def test_get_specific_patient_exists(self):
        """Test getting specific patient that may exist."""
        # Try patient ID 1 (common in test data)
        data, status = make_request(f"{API_BASE_URL}/api/patients/1")

        if status == 200:
            patient = data
            assert isinstance(patient, dict)
            assert "id" in patient
            assert patient["id"] == 1
        elif status == 404:
            # Patient doesn't exist - that's ok for integration test
            assert "not found" in str(data).lower()
        else:
            # Other status codes indicate issues
            assert False, f"Unexpected status code: {status}, data: {data}"


class TestCrossServiceIntegration:
    """Test integration between ML and API services."""

    def test_both_services_healthy(self):
        """Verify both services are healthy and accessible."""
        ml_data, ml_status = make_request(f"{ML_BASE_URL}/health")
        api_data, api_status = make_request(f"{API_BASE_URL}/health")

        assert ml_status == 200, f"ML service unhealthy: {ml_status}, {ml_data}"
        assert api_status == 200, f"API service unhealthy: {api_status}, {api_data}"

        assert ml_data["status"] == "ok"
        assert api_data["status"] == "ok"

    def test_service_connectivity(self):
        """Test basic network connectivity to both services."""
        # Test ML service
        try:
            ml_data, ml_status = make_request(f"{ML_BASE_URL}/health")
            ml_accessible = ml_status == 200
        except Exception:
            ml_accessible = False

        # Test API service
        try:
            api_data, api_status = make_request(f"{API_BASE_URL}/health")
            api_accessible = api_status == 200
        except Exception:
            api_accessible = False

        # At least one service should be accessible for meaningful integration testing
        assert ml_accessible or api_accessible, "Neither service is accessible"


class TestPerformanceBaseline:
    """Basic performance tests to establish baselines."""

    def test_ml_health_response_time(self):
        """Test ML health endpoint response time is reasonable."""
        start_time = time.time()
        data, status = make_request(f"{ML_BASE_URL}/health")
        end_time = time.time()

        assert status == 200
        response_time = end_time - start_time

        # Health check should be fast (< 2 seconds)
        assert response_time < 2.0, f"Health check too slow: {response_time}s"

    def test_retrieve_response_time(self):
        """Test retrieve endpoint response time is reasonable."""
        start_time = time.time()
        data, status = make_request(
            f"{ML_BASE_URL}/retrieve",
            method="POST",
            data={"query": "diabetes", "top_k": 3},
        )
        end_time = time.time()

        assert status == 200
        response_time = end_time - start_time

        # Retrieval should be reasonably fast (< 5 seconds for basic service)
        assert response_time < 5.0, f"Retrieval too slow: {response_time}s"
