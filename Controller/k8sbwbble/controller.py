from .job_spec import V1AlignJob
from .jobs.align_job import AlignJob
from .jobs.merge_job import MergeJob
from .jobs.aln2sam_job import Aln2SamJob
from .jobs.sampad_job import SampadJob
from .jobs.execution_time_job import ExecutionTimeJob

from kubernetes.watch import Watch
from kubernetes.client import ApiClient, BatchV1Api, Configuration
from typing import List


class Controller(object):
    def run(self, job: V1AlignJob):
        stages = [
            AlignJob(),
            ExecutionTimeJob("align"),
            MergeJob(),
            ExecutionTimeJob("merge"),
            Aln2SamJob(),
            ExecutionTimeJob("aln2sam"),
            SampadJob(),
            ExecutionTimeJob("sampad"),
        ]

        for stage in stages:
            job.status.stage = self.stage
            print(f"Starting {stage.stage}")
            stage.run(job)
            print(f"Started {stage.stage}, waiting for jobs to complete")
            # TODO: Save this state to Kubernetes

            self.wait_until_complete(job)
            print(f"Finished all jobs for {stage.stage}")

    def wait_until_complete(self, job: V1AlignJob):
        if len(job.status.waiting_for) == 0:
            return

        configuration = Configuration()
        api_client = ApiClient(configuration)

        watcher = Watch()
        for event in watcher.stream(
            BatchV1Api(api_client).list_namespaced_job,
            job.metadata.namespace,
            label_selector=f"bwbble-alignjob-name={job.metadata.name}",
        ):

            if event["object"].status.completion_time:
                name = event["object"].metadata.name
                if name in job.status.waiting_for:
                    job.status.waiting_for.remove(name)

                if len(job.status.waiting_for) == 0:
                    watcher.stop()
                    return
