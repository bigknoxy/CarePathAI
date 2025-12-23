#!/usr/bin/env python3
"""CarePathAI ML Service Entrypoint

Bootstrap script for CarePathAI ML service that initializes data
indices, ensures proper directory structure, and starts the FastAPI service.

Author: CarePathAI Architecture Team
"""

import logging
import os
import sys
from pathlib import Path

# Add the carepath_ml package to the Python path
carepath_ml_path = Path(__file__).parent.parent
if str(carepath_ml_path) not in sys.path:
    sys.path.insert(0, str(carepath_ml_path))

# Import data paths utility
try:
    from carepath_ml.utils.data_paths import get_data_paths
except ImportError as e:
    print(f"ERROR: Could not import data_paths utility: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def ensure_data_structure():
    """Ensure required data directories exist."""
    try:
        data_dir, index_dir = get_data_paths()
        
        # Create synthetic data directory if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured data directory exists: {data_dir}")
        
        # Create index directory if it doesn't exist
        index_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured index directory exists: {index_dir}")
        
        return data_dir, index_dir
    except Exception as e:
        logger.error(f"Failed to ensure data structure: {e}")
        raise

def initialize_indices():
    """Initialize FAISS or TF-IDF indices if needed."""
    try:
        data_dir, index_dir = get_data_paths()
        
        # Check if FAISS index exists
        faiss_path = index_dir / "patient_index.faiss"
        metadata_path = index_dir / "metadata.json"
        
        if not (faiss_path.exists() and metadata_path.exists()):
            logger.info("FAISS index not found, running ingest.py...")
            
            # Run the ingest script
            ingest_script = Path(__file__).parent / "ingest.py"
            if not ingest_script.exists():
                logger.error(f"ingest.py not found at {ingest_script}")
                return False
                
            import subprocess
            result = subprocess.run([sys.executable, str(ingest_script)], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to run ingest.py: {result.stderr}")
                return False
            else:
                logger.info("Successfully initialized FAISS index")
                logger.info(result.stdout)
        else:
            logger.info("FAISS index already exists")
            
        return True
    except Exception as e:
        logger.error(f"Failed to initialize indices: {e}")
        return False

def main():
    """Main entrypoint function."""
    try:
        logger.info("Starting CarePathAI ML Service...")
        
        # Ensure data directory structure exists
        data_dir, index_dir = ensure_data_structure()
        
        # Initialize indices if needed
        if not initialize_indices():
            logger.error("Failed to initialize indices, exiting...")
            sys.exit(1)
        
        # Start the FastAPI application
        logger.info("Starting FastAPI application...")
        import uvicorn
        from carepath_ml.main import app
        
        # Configure uvicorn
        uvicorn.run(
            app,
            host=os.environ.get("CAREPATH_HOST", "0.0.0.0"),
            port=int(os.environ.get("CAREPATH_PORT", 8000)),
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start CarePathAI ML Service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()