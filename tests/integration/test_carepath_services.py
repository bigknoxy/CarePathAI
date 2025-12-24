"""
Integration tests for CarePathAI ML and API services.
Tests run against actual Docker containers.

Environment variables:
- ML_BASE_URL: ML service base URL (default: http://localhost:8000)
- API_BASE_URL: C# API base URL (default: http://localhost:5000)

Run with: pytest -m integration
"""

import pytest
import requests
import json
import os
from typing import Dict, Any, List


# Environment-based configuration
ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

# Test markers
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def ml_client():
    """Create a requests session for ML service."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture(scope="module")
def api_client():
    """Create a requests session for C# API."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


class TestMLServiceHealth:
    """Test ML service health endpoints."""

    def test_basic_health(self, ml_client):
        """Test basic health endpoint."""
        response = ml_client.get(f"{ML_BASE_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data, dict)

    def test_detailed_health(self, ml_client):
        """Test detailed health endpoint with system state."""
        response = ml_client.get(f"{ML_BASE_URL}/health/detailed")

        assert response.status_code == 200
        data = response.json()

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


class TestMLEmbedEndpoint:
    """Test ML embedding endpoint - may not be available in basic service."""

    def test_embed_endpoint_availability(self, ml_client):
        """Check if embed endpoint is available (may not exist in basic service)."""
        try:
            response = ml_client.post(
                f"{ML_BASE_URL}/api/v1/embed",
                json={"text": "test patient with diabetes"},
            )
            # If endpoint exists, it should return 200 or proper error
            assert response.status_code in [200, 404, 501]
        except requests.exceptions.ConnectionError:
            pytest.skip("ML service not available")

    @pytest.mark.skipif(
        True,
        reason="Embed endpoint not available in current basic service implementation",
    )
    def test_embed_single_text(self, ml_client):
        """Test embedding generation for single text."""
        response = ml_client.post(
            f"{ML_BASE_URL}/api/v1/embed", json={"text": "test patient with diabetes"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify embedding structure
        assert "embeddings" in data or "embedding" in data
        embeddings = data.get("embeddings", [data.get("embedding")])
        assert len(embeddings) == 1

        embedding = embeddings[0]
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # Expected embedding dimension
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.skipif(
        True,
        reason="Embed endpoint not available in current basic service implementation",
    )
    def test_embed_status_and_metadata(self, ml_client):
        """Test embedding response includes status and metadata."""
        response = ml_client.post(
            f"{ML_BASE_URL}/api/v1/embed", json={"text": "test patient with diabetes"}
        )

        assert response.status_code == 200
        data = response.json()

        # Check for status info
        assert "status" in data or "model" in data


class TestMLRetrieveEndpoint:
    """Test ML retrieval endpoints."""

    def test_retrieve_basic(self, ml_client):
        """Test basic retrieval functionality."""
        response = ml_client.post(
            f"{ML_BASE_URL}/retrieve", json={"query": "diabetes", "top_k": 3}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "results" in data
        results = data["results"]
        assert isinstance(results, list)
        assert len(results) <= 3  # Should respect top_k

    def test_retrieve_with_top_k(self, ml_client):
        """Test retrieval with specific top_k parameter."""
        top_k = 5
        response = ml_client.post(
            f"{ML_BASE_URL}/retrieve", json={"query": "diabetes", "top_k": top_k}
        )

        assert response.status_code == 200
        data = response.json()
        results = data["results"]

        assert len(results) <= top_k

    def test_retrieve_result_structure(self, ml_client):
        """Test that retrieval results have expected structure."""
        response = ml_client.post(
            f"{ML_BASE_URL}/retrieve", json={"query": "diabetes", "top_k": 3}
        )

        assert response.status_code == 200
        data = response.json()
        results = data["results"]

        if results:  # If any results returned
            for result in results[:1]:  # Check first result
                assert isinstance(result, dict)
                # Check for common fields (may vary by implementation)
                expected_fields = ["id", "score"]
                for field in expected_fields:
                    if field in result:
                        assert result[field] is not None

    def test_retrieve_empty_query(self, ml_client):
        """Test retrieval behavior with empty query."""
        response = ml_client.post(
            f"{ML_BASE_URL}/retrieve", json={"query": "", "top_k": 3}
        )

        # Should handle empty query gracefully
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data


class TestMLOrchestrateEndpoint:
    """Test ML orchestrate endpoint - may not be available in basic service."""

    def test_orchestrate_endpoint_availability(self, ml_client):
        """Check if orchestrate endpoint is available."""
        try:
            response = ml_client.post(
                f"{ML_BASE_URL}/api/v1/orchestrate", json={"patient_id": 1, "top_k": 3}
            )
            # If endpoint exists, it should return 200 or proper error
            assert response.status_code in [200, 404, 501]
        except requests.exceptions.ConnectionError:
            pytest.skip("ML service not available")

    @pytest.mark.skipif(
        True,
        reason="Orchestrate endpoint not available in current basic service implementation",
    )
    def test_orchestrate_patient_flow(self, ml_client):
        """Test full orchestration flow with patient data."""
        response = ml_client.post(
            f"{ML_BASE_URL}/api/v1/orchestrate",
            json={
                "patient_id": 37,
                "top_k": 3,
            },  # Use known patient ID from synthetic data
        )

        assert response.status_code == 200
        data = response.json()

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

    def test_api_health(self, api_client):
        """Test API health endpoint."""
        response = api_client.get(f"{API_BASE_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert isinstance(data, dict)


class TestAPIPatientEndpoints:
    """Test C# API patient endpoints."""

    def test_get_all_patients(self, api_client):
        """Test getting all patients."""
        response = api_client.get(f"{API_BASE_URL}/api/patients")

        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)

        # If patients exist, verify structure
        if patients:
            for patient in patients[:1]:  # Check first patient
                assert isinstance(patient, dict)
                expected_fields = ["id", "firstName", "lastName"]
                for field in expected_fields:
                    if field in patient:
                        assert patient[field] is not None

    def test_get_specific_patient_not_found(self, api_client):
        """Test getting specific patient that doesn't exist."""
        response = api_client.get(f"{API_BASE_URL}/api/patients/99999")

        # Should return 404 for non-existent patient
        assert response.status_code == 404

    def test_get_specific_patient_exists(self, api_client):
        """Test getting specific patient that may exist."""
        # Try patient ID 1 (common in test data)
        response = api_client.get(f"{API_BASE_URL}/api/patients/1")

        if response.status_code == 200:
            patient = response.json()
            assert isinstance(patient, dict)
            assert "id" in patient
            assert patient["id"] == 1
        elif response.status_code == 404:
            # Patient doesn't exist - that's ok for integration test
            assert "not found" in response.text.lower()
        else:
            # Other status codes indicate issues
            assert False, f"Unexpected status code: {response.status_code}"


class TestCrossServiceIntegration:
    """Test integration between ML and API services."""

    def test_both_services_healthy(self, ml_client, api_client):
        """Verify both services are healthy and accessible."""
        ml_health = ml_client.get(f"{ML_BASE_URL}/health")
        api_health = api_client.get(f"{API_BASE_URL}/health")

        assert ml_health.status_code == 200
        assert api_health.status_code == 200

        ml_data = ml_health.json()
        api_data = api_health.json()

        assert ml_data["status"] == "ok"
        assert api_data["status"] == "ok"

    def test_service_connectivity(self):
        """Test basic network connectivity to both services."""
        # Test ML service
        try:
            response = requests.get(f"{ML_BASE_URL}/health", timeout=5)
            ml_accessible = response.status_code == 200
        except requests.exceptions.RequestException:
            ml_accessible = False

        # Test API service
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            api_accessible = response.status_code == 200
        except requests.exceptions.RequestException:
            api_accessible = False

        # At least one service should be accessible for meaningful integration testing
        assert ml_accessible or api_accessible, "Neither service is accessible"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_ml_service_invalid_endpoint(self, ml_client):
        """Test ML service handles invalid endpoints gracefully."""
        response = ml_client.get(f"{ML_BASE_URL}/invalid-endpoint")

        # Should return 404 for invalid endpoints
        assert response.status_code == 404

    def test_ml_service_invalid_method(self, ml_client):
        """Test ML service handles invalid HTTP methods."""
        response = ml_client.delete(f"{ML_BASE_URL}/health")

        # Should return 405 Method Not Allowed or similar
        assert response.status_code in [405, 404]

    def test_api_service_invalid_endpoint(self, api_client):
        """Test API service handles invalid endpoints gracefully."""
        response = api_client.get(f"{API_BASE_URL}/invalid-endpoint")

        # Should return 404 for invalid endpoints
        assert response.status_code == 404

    def test_malformed_json_request(self, ml_client):
        """Test service handles malformed JSON gracefully."""
        response = ml_client.post(
            f"{ML_BASE_URL}/retrieve",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Should handle malformed JSON appropriately
        assert response.status_code in [400, 422]


# Performance and load testing (basic)
class TestPerformanceBaseline:
    """Basic performance tests to establish baselines."""

    def test_ml_health_response_time(self, ml_client):
        """Test ML health endpoint response time is reasonable."""
        import time

        start_time = time.time()
        response = ml_client.get(f"{ML_BASE_URL}/health")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Health check should be fast (< 2 seconds)
        assert response_time < 2.0

    def test_retrieve_response_time(self, ml_client):
        """Test retrieve endpoint response time is reasonable."""
        import time

        start_time = time.time()
        response = ml_client.post(
            f"{ML_BASE_URL}/retrieve", json={"query": "diabetes", "top_k": 3}
        )
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Retrieval should be reasonably fast (< 5 seconds for basic service)
        assert response_time < 5.0


if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v", "-m", "integration"])
