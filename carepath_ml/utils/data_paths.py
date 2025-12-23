#!/usr/bin/env python3
"""Data path resolution utilities for CarePathAI ML package."""

import os
from pathlib import Path
from typing import Tuple


def get_data_paths(force_package_local: bool = False) -> Tuple[Path, Path]:
    """
    Resolve data directory paths with configurable fallback logic.

    Args:
        force_package_local: If True, always use package-local data directory
                           and ignore CAREPATH_DATA_DIR environment variable.

    Returns:
        Tuple of (DATA_DIR, INDEX_DIR) where:
        - DATA_DIR points to base / 'synthetic'
        - INDEX_DIR points to base / 'faiss' (created if needed)

    Raises:
        RuntimeError: If no suitable writable data directory can be found.
    """
    # Base package-local directory
    package_local_base = Path(__file__).resolve().parents[1] / "data"

    # Determine base directory to use
    if force_package_local:
        base = package_local_base
    else:
        # Check environment variable first
        env_dir = os.environ.get("CAREPATH_DATA_DIR")
        if env_dir:
            # Convert relative paths to absolute relative to repo root
            if not Path(env_dir).is_absolute():
                repo_root = Path(__file__).resolve().parents[2]
                env_base = repo_root / env_dir
            else:
                env_base = Path(env_dir)

            # Prefer env dir if it's writable
            if env_base.exists() and os.access(env_base, os.W_OK):
                base = env_base
            else:
                base = package_local_base
        else:
            base = package_local_base

        # Fallback logic: try package-local first, then /data
        if not (base.exists() and os.access(base, os.W_OK)):
            # Try /data as fallback
            data_fallback = Path("/data")
            if data_fallback.exists() and os.access(data_fallback, os.W_OK):
                base = data_fallback
            elif not (base.exists() and os.access(base, os.W_OK)):
                raise RuntimeError(
                    f"No writable data directory found. Tried:\n"
                    f"  - Package-local: {package_local_base}\n"
                    f"  - Environment: {os.environ.get('CAREPATH_DATA_DIR', 'Not set')}\n"
                    f"  - Fallback: /data\n"
                    f"Solution: Set CAREPATH_DATA_DIR environment variable to a writable path "
                    f"or ensure {package_local_base} is writable."
                )

    # Construct final paths
    data_dir = base / "synthetic"
    index_dir = base / "faiss"

    # Create index directory if needed
    try:
        index_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(
            f"Failed to create index directory {index_dir}: {e}\n"
            f"Please ensure the parent directory is writable."
        ) from e

    return data_dir, index_dir
