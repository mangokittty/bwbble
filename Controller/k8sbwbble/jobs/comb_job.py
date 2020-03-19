from ..job import V1AlignJob, Job
from kubernetes.client import V1Job


class CombJob(Job):
    def __init__(self):
        super().__init__("comb")

    def container_image(self):
        return "bwbble/mg-ref"

    def run(self, job: V1AlignJob):
        # Do the combine job
        api_responses = self.create_job_resources(
            job, f"bwbble/mg-ref:{job.spec.bwbble_version}"
        )

        job.status.waiting_for.extend(
            [r.metadata.name for r in api_responses if isinstance(r, V1Job)]
        )
