"""Configuration settings for Member 2 experiment engine.

Author: P. Satya Mani Shraavanth (Member 2)
Course: BCSE303L - Operating Systems
"""

from typing import List

# Experiment timeouts and scheduling
DEFAULT_OVERALL_TIMEOUT_SECONDS: float = 5.0
VULNERABLE_LOCK_TIMEOUT_SECONDS: float = 0.8
VULNERABLE_OBSERVATION_WINDOW_SECONDS: float = 0.12
PROTECTED_LOCK_TIMEOUT_SECONDS: float = 2.0
THREAD_CRITICAL_SECTION_DELAY_SECONDS: float = 0.05
INTERLEAVING_DELAY_SECONDS: float = 0.02

# Configurable N-thread resource-ring experiment
MULTI_THREAD_MIN: int = 2
MULTI_THREAD_MAX: int = 32
MULTI_THREAD_HOLD_SECONDS: float = 0.03

# Lock ordering definition
COMMON_LOCK_ORDER: List[str] = ["A", "B"]
DEFAULT_RESOURCES: List[str] = ["A", "B"]
DEFAULT_THREADS: List[str] = ["T1", "T2"]

# Server defaults
API_HOST: str = "127.0.0.1"
API_PORT: int = 8000
