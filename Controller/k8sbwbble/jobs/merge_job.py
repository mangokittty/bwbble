from ..job import V1AlignJob, Job
from ..file_range import Range
from kubernetes.client import V1ResourceRequirements, V1Job


class MergeJob(Job):
    def __init__(self):
        super().__init__("merge")

    def run(self, job: V1AlignJob):

        file_ranges = Range.generate(job.spec.reads_count, job.spec.align_parallelism)
        merge_command = [
            "cat",
            *[
                f"/mg-align-output/{job.metadata.name}.aligned_reads.{range.name}.aln"
                for range in file_ranges
            ],
            ">",
            f"/mg-align-output/{job.metadata.name}.aligned_reads.aln",
        ]

        api_responses = self.create_job_resources(
            job,
            "busybox:latest",
            use_config_map_args=False,
            use_aci=False,
            args=[
                "sh",
                "-c",
                " ".join([f"'{p}'" if " " in p else p for p in merge_command]),
            ],
            resources=V1ResourceRequirements(
                limits={"memory": "128Mi", "cpu": "1"},
                requests={"memory": "128Mi", "cpu": "50m"},
            ),
        )

        job.status.waiting_for.extend(
            [r.metadata.name for r in api_responses if isinstance(r, V1Job)]
        )
