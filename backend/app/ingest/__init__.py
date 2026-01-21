"""
Ingestion worker and scheduler package.
"""

from .pipeline import run_full_ingestion_pipeline

__all__ = ["run_full_ingestion_pipeline"]
