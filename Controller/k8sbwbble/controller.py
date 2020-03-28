from .job_spec import V1AlignJob, add_to_api_client
from .jobs.align_job import AlignJob
from .jobs.merge_job import MergeJob
from .jobs.aln2sam_job import Aln2SamJob
from .jobs.sampad_job import SampadJob
from .jobs.execution_time_job import ExecutionTimeJob
from threading import Thread
from json import dumps
import datetime

from kubernetes.watch import Watch
from kubernetes.client import (
    ApiClient,
    BatchV1Api,
    Configuration,
    V1Job,
    CustomObjectsApi,
)
from kubernetes.client.rest import RESTResponse
from typing import List


class AlignJobWatcherThread(Thread):
    def __init__(self, controller: "Controller", namespace: str):
        super().__init__()

        self.controller = controller
        self.namespace = namespace

    def run(self):
        print("Starting AlignJob watcher thread")
        watcher = Watch(return_type=V1AlignJob)
        for event in watcher.stream(
            CustomObjectsApi(self.controller.api_client).list_namespaced_custom_object,
            "bwbble.aideen.dev",
            "v1",
            self.namespace,
            "alignjobs",
        ):
            self.controller.on_align_job_updated(event["object"])


class BatchJobWatcherThread(Thread):
    def __init__(self, controller: "Controller", namespace: str):
        super().__init__()

        self.controller = controller
        self.namespace = namespace

    def run(self):
        print("Starting BatchJob watcher thread")
        watcher = Watch(return_type=V1Job)
        for event in watcher.stream(
            BatchV1Api(self.controller.api_client).list_namespaced_job, self.namespace,
        ):
            # TODO: Ignore deletion and creation events (only trigger on updates)
            self.controller.on_job_updated(event["object"])


class MockResponse(object):
    def __init__(self, response):
        super().__init__()
        self.data = dumps(response)


class Controller(object):
    def __init__(self):
        super().__init__()

        self.config = Configuration()
        self.api_client = ApiClient(self.config)
        add_to_api_client(self.api_client)

    def run(self, namespace: str):
        align_job_watcher = AlignJobWatcherThread(self, namespace)
        batch_job_watcher = BatchJobWatcherThread(self, namespace)

        align_job_watcher.start()
        batch_job_watcher.start()

        align_job_watcher.join()
        batch_job_watcher.join()

    def create_align_job(self, job: V1AlignJob):
        return CustomObjectsApi(self.api_client).create_namespaced_custom_object(
            "bwbble.aideen.dev", "v1", job.metadata.namespace, "alignjobs", job,
        )

    def get_align_job(self, namespace: str, name: str) -> V1AlignJob:
        response = CustomObjectsApi(self.api_client).get_namespaced_custom_object(
            "bwbble.aideen.dev", "v1", namespace, "alignjobs", name,
        )

        return self.api_client.deserialize(MockResponse(response), V1AlignJob)

    def save_align_job_state(self, job: V1AlignJob):
        return CustomObjectsApi(self.api_client).replace_namespaced_custom_object(
            "bwbble.aideen.dev",
            "v1",
            job.metadata.namespace,
            "alignjobs",
            job.metadata.name,
            job,
        )

    def on_job_updated(self, job: V1Job):
        """
        Handles the change of state in a Kubernetes Batch V1 job (the unit of execution
        we work with in K8s).
        """
        print(f"Job {job.metadata.name} updated")

        try:
            if job.status.completion_time is None:
                return

            if "bwbble-alignjob-name" not in job.metadata.labels:
                return

            align_job_id = job.metadata.labels["bwbble-alignjob-name"]
            align_job = self.get_align_job(job.metadata.namespace, align_job_id)
            if not align_job:
                return

            if job.metadata.name in align_job.status.waiting_for:
                align_job.status.waiting_for.remove(job.metadata.name)

                self.save_align_job_state(align_job)
        except Exception as ex:
            # TODO: If this fails for an unrecoverable reason, update the alignjob to reflect that
            #       e.g. if a job fails permanently/is deleted
            print(ex)

    def on_align_job_updated(self, job: V1AlignJob):
        """
        Handles the change of state in one of our high-level AlignJobs (a custom resource).
        """
        print(f"AlignJob {job.metadata.name} updated")

        try:
            if len(job.status.waiting_for) > 0:
                print(
                    f"Waiting for {len(job.status.waiting_for)} jobs to complete for {job.status.stage}"
                )
                return

            if job.status.stage is not None:
                print(f"Finished all jobs for {job.status.stage}")
                ExecutionTimeJob(job.status.stage).run(job)

            if job.status.stage is None:
                # Execute the align job
                job.status.start_time = datetime.datetime.utcnow()
                job.status.stage = "align"
                AlignJob().run(job)
            elif job.status.stage == "align":
                job.status.stage = "merge"
                MergeJob().run(job)
            elif job.status.stage == "merge":

                job.status.stage = "aln2sam"
                Aln2SamJob().run(job)
            elif job.status.stage == "aln2sam":
                job.status.stage = "sampad"
                SampadJob().run(job)
            elif job.status.stage == "sampad":
                job.status.stage = "completed"
                job.status.end_time = datetime.datetime.utcnow()

            # TODO: Add a cleanup phase (to remove all jobs and configmaps)

            elif job.status.stage == "completed":
                print(
                    f"Finished full alignment of {job.spec.reads_file} with parallelism of {job.spec.align_parallelism}"
                )
                return

            print(f"Started stage {job.status.stage}")

            self.save_align_job_state(job)
        except Exception as ex:
            print(ex)

            # TODO: If we can't schedule the next phase of work, mark the job as failed with a reason
            #       e.g. there is another job with the same name and conflicting resources (we get a 409)
