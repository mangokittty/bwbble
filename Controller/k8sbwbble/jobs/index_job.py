from ..job import V1AlignJob, Job
from kubernetes.client import V1ResourceRequirements, V1Job


class IndexJob(Job):
    def __init__(self):
        super().__init__("index")

    def run(self, job: V1AlignJob):
        api_responses = self.create_job_resources(
            job,
            f"bwbble/mg-aligner:{job.spec.bwbble_version}",
            args=["index", f"/mg-ref-output/{job.spec.snp_file}"],
            resources=V1ResourceRequirements(
                limits={"memory": "2Gi", "cpu": "1"},
                requests={"memory": "2Gi", "cpu": "1"},
            ),
        )

        job.status.waiting_for.extend(
            [r.metadata.name for r in api_responses if isinstance(r, V1Job)]
        )
