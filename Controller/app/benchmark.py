#!/usr/bin/env python

from k8sbwbble.controller import Controller
from k8sbwbble.job_spec import V1AlignJob, V1AlignJobSpec
from kubernetes.client import V1ObjectMeta, CustomObjectsApi
from kubernetes.config import load_kube_config, load_incluster_config
from kubernetes.watch import Watch

if __name__ == "__main__":
    print("Configuring bwbble controller for access to K8s API")

    # Load the Kubernetes config file
    try:
        load_incluster_config()
    except:
        load_kube_config()

    controller = Controller()

    # TODO: Use argparse to provide the namespace as an argument

    # TODO: store some overall stats for the runs

    for parallelism in range(1, 16):
        # TODO: store some aggregated stats for this run
        run_stats = {}

        for run_index in range(1, 5):
            job = V1AlignJob(
                metadata=V1ObjectMeta(
                    name=f"bench-p{parallelism}-r{run_index}", namespace="bwbble-dev"
                ),
                spec=V1AlignJobSpec(
                    # TODO: fill this in
                ),
            )
            controller.create_align_job(job)

            watcher = Watch(return_type=V1AlignJob)
            for event in watcher.stream(
                CustomObjectsApi(controller.api_client).list_namespaced_custom_object,
                "bwbble.aideen.dev",
                "v1",
                job.metadata.namespace,
                "alignjobs",
            ):
                if event["object"].metadata.name == job.metadata.name:
                    if event["object"].status.end_time is not None:
                        watcher.stop()
                        # TODO: print out the stats from this run (using event['object'].status)
