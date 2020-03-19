from ..job import V1AlignJob, Job
from kubernetes.client import V1Job


class Aln2SamJob(Job):
    def __init__(self):
        super().__init__("aln2sam")

    def run(self, job: V1AlignJob):
        api_responses = self.create_job_resources(
            job,
            f"bwbble/mg-aligner:{job.spec.bwbble_version}",
            args=[
                "aln2sam",
                f"/mg-ref-output/{job.spec.snp_file}",
                f"/input/{job.spec.reads_file}",
                f"/mg-align-output/{job.metadata.name}.aligned_reads.aln",
                f"/mg-align-output/{job.metadata.name}.aligned_reads.sam",
            ],
        )

        job.status.waiting_for.extend(
            [r.metadata.name for r in api_responses if isinstance(r, V1Job)]
        )
