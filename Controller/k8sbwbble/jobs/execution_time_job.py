from ..job import V1AlignJob, Job
from _datetime import timedelta
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
import re


class ExecutionTimeJob(Job):
    def __init__(self, stage: str):
        super().__init__(stage)

    def run(self, job: V1AlignJob):
        job.status.execution_times[self.stage] = {}

        # config.load_kube_config()
        # pod_name = "bwbble-align-dummylargereads1-range-0--1-799ms"
        try:

            # get execution time for pods
            api_response = self.api_instance.list_namespaced_job(
                namespace=job.metadata.namespace,
                label_selector=f"bwbble-release={job.metadata.name},bwbble-stage={self.stage}",
            )

            for item in api_response.items:
                job.status.execution_times[self.stage][item.metadata.name] = {
                    "total": -1
                }

                if item.status.completion_time:
                    execution_time = (
                        item.status.completion_time - item.status.start_time
                    )
                    print(
                        item.metadata.name, " (job): ", execution_time,
                    )

                    job.status.execution_times[self.stage][item.metadata.name][
                        "total"
                    ] = str(execution_time)
                else:
                    print(item.metadata.name, " (job): Not yet finished")

            if self.stage == "align":
                # get execution time for pods
                api_response = CoreV1Api(self.api_client).list_namespaced_pod(
                    namespace=job.metadata.namespace,
                    label_selector=f"bwbble-release={job.metadata.name},bwbble-stage={self.stage}",
                )
                for item in api_response.items:
                    logs = CoreV1Api(self.api_client).read_namespaced_pod_log(
                        item.metadata.name,
                        job.metadata.namespace,
                        container="align",
                        tail_lines=100,
                    )
                    with open(
                        f"{job.metadata.namespace}-{item.metadata.name}.log", "w+"
                    ) as f:
                        if logs:
                            f.write(logs)
                            f.close()
                            rem = re.search(
                                r"read alignment time: (\d+\.?\d*) sec",
                                logs,
                                re.IGNORECASE,
                            )

                            if rem:
                                print(
                                    item.metadata.name,
                                    " (logs): ",
                                    timedelta(seconds=float(rem[1])),
                                )

                                job.status.execution_times[self.stage][
                                    item.metadata.labels["job-name"]
                                ]["internal"] = str(timedelta(seconds=float(rem[1])))
        except ApiException as e:
            print(e)
