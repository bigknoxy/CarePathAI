#!/usr/bin/env python3
"""Orchestrate endpoint for CarePathAI ML service."""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)


# Request/Response models
class OrchestrateRequest(BaseModel):
    patient_id: int = Field(..., description="Patient ID to retrieve data for", ge=1)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=100)


class PatientData(BaseModel):
    # Generic patient fields - will adapt based on actual C# API response
    id: int = Field(..., description="Patient ID")
    firstName: Optional[str] = Field(None, description="Patient first name")
    lastName: Optional[str] = Field(None, description="Patient last name")
    dateOfBirth: Optional[str] = Field(None, description="Patient date of birth")
    medicalRecordNumber: Optional[str] = Field(None, description="Patient MRN")
    conditions: Optional[List[str]] = Field(
        default_factory=list, description="Patient conditions"
    )
    notes: Optional[str] = Field(None, description="Patient notes")


class RetrieveResult(BaseModel):
    id: int = Field(..., description="Document ID")
    score: float = Field(..., description="Similarity score (L2 distance)")
    text: str = Field(..., description="Document text")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class OrchestrateResponse(BaseModel):
    patient: PatientData = Field(..., description="Patient information")
    retrieved: List[RetrieveResult] = Field(..., description="Retrieved documents")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")


router = APIRouter(prefix="/api/v1", tags=["orchestration"])


def get_api_base_url() -> str:
    """Get C# API base URL from environment or default."""
    return os.environ.get("API_BASE_URL", "http://localhost:5000")


async def fetch_patient_from_csharp_api(patient_id: int) -> Dict[str, Any]:
    """
    Fetch patient data from C# API.

    Args:
        patient_id: Patient ID to fetch

    Returns:
        Patient data dictionary

    Raises:
        RuntimeError: If API call fails
    """
    api_base = get_api_base_url()
    url = f"{api_base}/api/patients/{patient_id}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Fetching patient {patient_id} from {url}")
            response = await client.get(url)

            if response.status_code == 404:
                raise RuntimeError(f"Patient {patient_id} not found")
            elif response.status_code >= 400:
                raise RuntimeError(
                    f"C# API error: {response.status_code} - {response.text}"
                )

            return response.json()

    except httpx.TimeoutException:
        raise RuntimeError(f"Timeout fetching patient {patient_id} from C# API")
    except httpx.RequestError as e:
        raise RuntimeError(f"Request error fetching patient {patient_id}: {str(e)}")
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Invalid JSON response from C# API for patient {patient_id}"
        )


async def perform_retrieval(
    patient_id: int, top_k: int, request: Request
) -> List[RetrieveResult]:
    """
    Perform retrieval using existing ML retrieve functionality.

    Args:
        patient_id: Patient ID for context
        top_k: Number of results to return
        request: FastAPI Request object for app state access

    Returns:
        List of retrieval results
    """
    try:
        # Try to use existing retrieve endpoint functionality
        if hasattr(request.app.state, "index") and request.app.state.index is not None:
            # Use FAISS retrieval
            return await perform_faiss_retrieval(patient_id, top_k, request)
        else:
            # Fallback to existing retrieve endpoint
            return await call_retrieve_endpoint(patient_id, top_k, request)

    except Exception as e:
        logger.error(f"Retrieval failed for patient {patient_id}: {e}")
        return []


async def perform_faiss_retrieval(
    patient_id: int, top_k: int, request: Request
) -> List[RetrieveResult]:
    """Perform retrieval using FAISS index."""
    try:
        # Get patient data to use as query
        patient_data = await fetch_patient_from_csharp_api(patient_id)

        # Use patient notes as query, or concatenate available text
        query_parts = []
        if patient_data.get("notes"):
            query_parts.append(patient_data["notes"])
        if patient_data.get("conditions"):
            query_parts.extend(patient_data["conditions"])

        query_text = " ".join(query_parts) if query_parts else f"Patient {patient_id}"

        # Get model and index from app state
        model = request.app.state.model
        index = request.app.state.index
        metadata = getattr(request.app.state, "metadata", [])

        if model is None or index is None:
            logger.warning("Model or index not available for FAISS retrieval")
            return []

        # Generate query embedding
        query_embedding = model.encode([query_text], convert_to_numpy=True)

        # Search index
        distances, indices = index.search(query_embedding, min(top_k, len(metadata)))

        # Build results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx >= 0 and idx < len(metadata):
                meta_entry = metadata[idx] if metadata else {}
                result = RetrieveResult(
                    id=int(idx),
                    score=float(dist),
                    text=meta_entry.get("text", f"Document {idx}"),
                    metadata=meta_entry,
                )
                results.append(result)

        logger.info(
            f"FAISS retrieval returned {len(results)} results for patient {patient_id}"
        )
        return results

    except Exception as e:
        logger.error(f"FAISS retrieval failed for patient {patient_id}: {e}")
        return []


async def call_retrieve_endpoint(
    patient_id: int, top_k: int, request: Request
) -> List[RetrieveResult]:
    """Call existing retrieve endpoint."""
    try:
        # Get patient data to use as query
        patient_data = await fetch_patient_from_csharp_api(patient_id)

        # Use patient notes as query
        query_text = patient_data.get("notes", f"Patient {patient_id}")

        # Call retrieve endpoint internally
        # This is a simplified approach - in production you might want to call the actual endpoint
        query_request = {"query": query_text, "top_k": top_k}

        # For now, return empty results - this would need the actual retrieval implementation
        logger.warning(
            "Using empty retrieval fallback - implement actual retrieve endpoint call"
        )
        return []

    except Exception as e:
        logger.error(f"Retrieve endpoint call failed for patient {patient_id}: {e}")
        return []


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_care(request: Request, orchestrate_request: OrchestrateRequest):
    """
    Orchestrate patient care guidance.

    Accepts JSON body: {"patient_id": int, "top_k": int}
    Returns consolidated JSON: {"patient": {...patient fields...}, "retrieved": [{"id":..., "score":..., "text":...}, ...]}

    Handles errors:
    - patient not found -> 404
    - downstream errors -> 502
    """
    try:
        logger.info(
            f"Orchestrating care for patient {orchestrate_request.patient_id}, top_k={orchestrate_request.top_k}"
        )

        # Fetch patient data from C# API
        try:
            patient_data = await fetch_patient_from_csharp_api(
                orchestrate_request.patient_id
            )
        except RuntimeError as e:
            if "not found" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": f"Patient {orchestrate_request.patient_id} not found"
                    },
                )
            else:
                # C# API downstream error
                logger.error(
                    f"C# API error for patient {orchestrate_request.patient_id}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Downstream service error: {str(e)}",
                )

        # Create patient object (flexible mapping from C# API response)
        patient = PatientData(
            id=orchestrate_request.patient_id,
            firstName=patient_data.get("firstName") or patient_data.get("first_name"),
            lastName=patient_data.get("lastName") or patient_data.get("last_name"),
            dateOfBirth=patient_data.get("dateOfBirth")
            or patient_data.get("date_of_birth"),
            medicalRecordNumber=patient_data.get("medicalRecordNumber")
            or patient_data.get("mrn"),
            conditions=patient_data.get("conditions", []),
            notes=patient_data.get("notes", ""),
        )

        # Perform retrieval
        retrieved = await perform_retrieval(
            orchestrate_request.patient_id, orchestrate_request.top_k, request
        )

        logger.info(
            f"Orchestration completed for patient {orchestrate_request.patient_id}: {len(retrieved)} retrieved items"
        )

        return OrchestrateResponse(patient=patient, retrieved=retrieved)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in orchestrate_care: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Internal server error: {str(e)}"},
        )
