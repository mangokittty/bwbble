from ..job import V1AlignJob, Job
from ..file_range import Range
from kubernetes.client import V1Job, V1ResourceRequirements


class AlignJob(Job):
    def __init__(self):
        super().__init__("align")

    def run(self, job: V1AlignJob):
        file_ranges = Range.generate(job.spec.reads_count, job.spec.align_parallelism)

        for range in file_ranges:
            api_responses = self.create_job_resources(
                job,
                f"bwbble/mg-aligner:{job.spec.bwbble_version}",
                args=[
                    "align",
                    "-s",
                    f"{range.start}",
                    "-p",
                    f"{range.length}",
                    f"/mg-ref-output/{job.spec.snp_file}",
                    f"/input/{job.spec.reads_file}",
                    f"/mg-align-output/{job.metadata.name}.aligned_reads.{range.name}.aln",
                ],
                name_suffix=f"-{range.name}",
                resources=V1ResourceRequirements(
                    limits={"cpu": "1", "memory": "2Gi"},
                    requests={"cpu": "1", "memory": "2Gi"},
                ),
            )

            job.status.waiting_for.extend(
                [r.metadata.name for r in api_responses if isinstance(r, V1Job)]
            )
