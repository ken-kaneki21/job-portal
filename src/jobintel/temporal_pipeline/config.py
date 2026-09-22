from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv(override=True)

TEMPORAL_ADDRESS = os.getenv(
    "JOBINTEL_TEMPORAL_ADDRESS",
    "localhost:7233",
)

TEMPORAL_NAMESPACE = os.getenv(
    "JOBINTEL_TEMPORAL_NAMESPACE",
    "default",
)

TASK_QUEUE = os.getenv(
    "JOBINTEL_TEMPORAL_TASK_QUEUE",
    "job-intelligence-pipeline-v2",
)
