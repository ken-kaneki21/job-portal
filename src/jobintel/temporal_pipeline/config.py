import os

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
    "job-intelligence-pipeline",
)
