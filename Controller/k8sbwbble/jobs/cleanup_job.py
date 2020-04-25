from ..job import V1AlignJob, Job
from kubernetes.client import V1Job, CoreV1Api
import time


class CleanupJob(Job):
    def __init__(self):
        super().__init__("cleanup")

    def run(self, job: V1AlignJob):
        self.api_instance.delete_collection_namespaced_job(
            job.metadata.namespace,
            label_selector=f"bwbble-alignjob-name={job.metadata.name}",
            propagation_policy="Foreground",
        )

        CoreV1Api(self.api_client).delete_collection_namespaced_config_map(
            job.metadata.namespace,
            label_selector=f"bwbble-alignjob-name={job.metadata.name}",
        )
