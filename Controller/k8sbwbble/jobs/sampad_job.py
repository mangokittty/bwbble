from ..job import V1AlignJob, Job
from kubernetes.client import V1EnvVar, V1Job


class SampadJob(Job):
    def __init__(self):
        super().__init__("sampad")

    def run(self, job: V1AlignJob):
        api_responses = self.create_job_resources(
            job,
            f"bwbble/mg-ref:{job.spec.bwbble_version}",
            args=[
                f"/mg-ref-output/{job.spec.bubble_file}",
                f"/mg-align-output/{job.metadata.name}.aligned_reads.sam",
                f"/mg-align-output/{job.metadata.name}.output.sam",
            ],
            env=[V1EnvVar(name="APPLICATION", value="sam_pad"),],
        )

        job.status.waiting_for.extend(
            [r.metadata.name for r in api_responses if isinstance(r, V1Job)]
        )
