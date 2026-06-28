"""
Job scheduler with retry logic and rate limiting.
"""

import time
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor, Future
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Job:
    """Evaluation job."""
    id: str
    model: str
    scenario_id: str
    scenario_data: dict
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'model': self.model,
            'scenario_id': self.scenario_id,
            'status': self.status.value,
            'attempts': self.attempts,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float):
        """
        Args:
            rate: Requests per second
        """
        self.rate = rate
        self.tokens = rate
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

            time.sleep(0.01)


class JobScheduler:
    """
    Manages job execution with:
    - Concurrent worker pool
    - Rate limiting
    - Automatic retries
    - Progress tracking
    """

    def __init__(
        self,
        num_workers: int = 4,
        rate_limit_rps: float = 10.0,
        max_retries: int = 3
    ):
        self.num_workers = num_workers
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter(rate_limit_rps)

        self.job_queue: queue.Queue[Job] = queue.Queue()
        self.results: dict[str, Job] = {}
        self.lock = threading.Lock()

        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: list[Future] = []

    def submit(self, job: Job) -> None:
        """Submit a job for execution."""
        with self.lock:
            self.results[job.id] = job
        self.job_queue.put(job)
        logger.debug(f"Job {job.id} submitted")

    def submit_batch(self, jobs: list[Job]) -> None:
        """Submit multiple jobs."""
        for job in jobs:
            self.submit(job)
        logger.info(f"Submitted {len(jobs)} jobs")

    def run(self, worker_fn: Callable[[Job], dict]) -> list[Job]:
        """
        Execute all queued jobs.

        Args:
            worker_fn: Function that takes a Job and returns result dict

        Returns:
            List of completed jobs
        """
        self._executor = ThreadPoolExecutor(max_workers=self.num_workers)

        def process_job(job: Job) -> None:
            while job.attempts < self.max_retries:
                try:
                    # Rate limit
                    self.rate_limiter.acquire()

                    # Update status
                    job.status = JobStatus.RUNNING
                    job.attempts += 1

                    logger.info(f"Processing job {job.id} (attempt {job.attempts})")

                    # Execute
                    result = worker_fn(job)

                    # Success
                    job.status = JobStatus.COMPLETED
                    job.result = result
                    job.completed_at = datetime.now().isoformat()

                    logger.info(f"Job {job.id} completed")
                    return

                except Exception as e:
                    logger.warning(f"Job {job.id} failed: {e}")
                    job.error = str(e)

                    if job.attempts < self.max_retries:
                        job.status = JobStatus.RETRYING
                        time.sleep(1)  # Backoff
                    else:
                        job.status = JobStatus.FAILED
                        job.completed_at = datetime.now().isoformat()

        # Submit all jobs to executor
        while not self.job_queue.empty():
            try:
                job = self.job_queue.get_nowait()
                future = self._executor.submit(process_job, job)
                self._futures.append(future)
            except queue.Empty:
                break

        # Wait for completion
        for future in self._futures:
            future.result()

        self._executor.shutdown(wait=True)

        return list(self.results.values())

    def get_status(self) -> dict:
        """Get current job status summary."""
        with self.lock:
            status_counts = {}
            for job in self.results.values():
                status = job.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                'total': len(self.results),
                'queued': self.job_queue.qsize(),
                'by_status': status_counts
            }

    def get_results(self) -> list[Job]:
        """Get all job results."""
        with self.lock:
            return list(self.results.values())
