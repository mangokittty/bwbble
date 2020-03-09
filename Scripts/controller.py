#!/usr/bin/env python
import hashlib
import string
import random
import logging
import yaml
from pprint import pprint
import sys
import os
import time
from typing import List
import subprocess
from kubernetes import client, config, utils
import kubernetes.client
from kubernetes.client.rest import ApiException
from kubernetes.client.rest import ApiException
import re
from datetime import timedelta
from math import floor


class Range(object):
    def __init__(self, start: int, length: int = -1):
        self.start = start
        self.length = length

    @property
    def name(self) -> str:
        if self.length == -1:
            return f"{self.start}-end"
        return f"{self.start}-{self.start+self.length}"

    @staticmethod
    def generate(num_reads: int, parallelism: int = 1):
        rrange = floor(num_reads/parallelism)
        ranges = []
        for i in range(0, parallelism):
            ranges.append(Range(i * rrange, rrange))

        ranges[len(ranges)-1].length = -1

        return ranges


# Configuration
bwbble_container_image_version = "313"
reads_file = "dummy_reads.fastq"
bubble_file = "chr21_bubble.data"
snp_file = "chr21_ref_w_snp_and_bubble.fasta"
parallelism = 18
reads = 512000
file_ranges = Range.generate(reads, parallelism)


# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Setup K8 configs
config.load_kube_config()
configuration = kubernetes.client.Configuration()
api_client = kubernetes.client.ApiClient(configuration)
api_instance = kubernetes.client.BatchV1Api(api_client)


def execution_times(namespace: str, release: str, stage: str, align_logs: bool = False):
    # config.load_kube_config()
    # pod_name = "bwbble-align-dummylargereads1-range-0--1-799ms"
    try:
        if align_logs:
            # get execution time for pods
            api_response = kubernetes.client.CoreV1Api(api_client).list_namespaced_pod(
                namespace=namespace, label_selector=f"bwbble-release={release},bwbble-stage={stage}")
            for item in api_response.items:
                logs = kubernetes.client.CoreV1Api(api_client).read_namespaced_pod_log(
                    item.metadata.name, namespace, container='align', tail_lines=100)
                with open(f"{namespace}-{item.metadata.name}.log", "w+") as f:
                    if logs:
                        f.write(logs)
                        f.close()
                        rem = re.search(
                            r"read alignment time: (\d+\.?\d*) sec", logs, re.IGNORECASE)

                        if rem:
                            print(item.metadata.name, " (logs): ",
                                  timedelta(seconds=float(rem[1]))
                                  )
        # get execution time for pods
        api_response = api_instance.list_namespaced_job(
            namespace=namespace, label_selector=f"bwbble-release={release},bwbble-stage={stage}")
        for item in api_response.items:
            if item.status.completion_time:
                print(item.metadata.name, " (job): ",
                      item.status.completion_time - item.status.start_time)
            else:
                print(item.metadata.name, " (job): Not yet finished")

    except ApiException as e:
        print(e)


def create_job_resources(namespace: str, release: str, stage: str, container_image: str, args: List[str], use_config_map_args: bool = True, resources: client.V1ResourceRequirements = None, env: List[client.V1EnvVar] = None, name_suffix: str = "", use_aci: bool = True):
    labels = {
        "app.kubernetes.io/managed-by": "faaideen",
        "bwbble-release": release,
        "bwbble-stage": stage,
    }

    resources = resources or client.V1ResourceRequirements(
        limits={
            "memory": "2Gi",
            "cpu": "1"
        },
        requests={
            "memory": "2Gi",
            "cpu": "1"

        })
    created_resources = []
    env_array = []

    if use_aci and not use_config_map_args:
        raise Exception(
            "Azure Container Instances require that arguments are passed using a file")

    if use_config_map_args:
        env_array.append(client.V1EnvVar(
            name="ARGS_FILE", value="/var/run/args/container_args"))

        created_resources.append(kubernetes.client.CoreV1Api(api_client).create_namespaced_config_map(namespace, kubernetes.client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(
                name=f"bwbble-{release}-{stage}{name_suffix}", labels=labels
            ),
            data={
                "container_args": " ".join([f"'{a}'" if " " in a else a for a in args]),
            }
        )))

    if env is not None:
        env_array.extend(env)

    job_spec = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name=f"bwbble-{release}-{stage}{name_suffix}", labels=labels),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(
                name=stage,
                labels=labels
            ), spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[
                    client.V1Container(
                        name=stage,
                        image=container_image,
                        image_pull_policy="IfNotPresent",
                        args=args,
                        env=env_array,
                        resources=resources,
                        volume_mounts=[
                            client.V1VolumeMount(
                                mount_path="/input",
                                name="input"
                            ),
                            client.V1VolumeMount(
                                mount_path="/mg-ref-output",
                                name="ref-output"
                            ),
                            client.V1VolumeMount(
                                mount_path="/mg-align-output",
                                name="align-output"
                            )
                        ])
                ],
                volumes=[
                    client.V1Volume(
                        name="input",
                        azure_file=client.V1AzureFileVolumeSource(
                            secret_name="azure-secret",
                            share_name="input",
                            read_only=True
                        )
                    ),
                    client.V1Volume(
                        name="ref-output",
                        azure_file=client.V1AzureFileVolumeSource(
                            secret_name="azure-secret",
                            share_name="ref-output",
                            read_only=False
                        )
                    ),
                    client.V1Volume(
                        name="align-output",
                        azure_file=client.V1AzureFileVolumeSource(
                            secret_name="azure-secret",
                            share_name="align-output",
                            read_only=False
                        )
                    )
                ])
            )
        )
    )

    if use_aci:
        job_spec.spec.template.spec.node_selector = {
            "kubernetes.io/role": "agent",
            "beta.kubernetes.io/os": "linux",
            "type": "virtual-kubelet"
        }

        job_spec.spec.template.spec.tolerations = [
            client.V1Toleration(
                key="virtual-kubelet.io/provider", operator="Exists"),
            client.V1Toleration(key="azure.com/aci", effect="NoSchedule"),
        ]

    if use_config_map_args:

        job_spec.spec.template.spec.volumes.append(client.V1Volume(
            name="args",
            config_map=client.V1ConfigMapVolumeSource(
                name=f"bwbble-{release}-{stage}{name_suffix}")
        ))

        job_spec.spec.template.spec.containers[0].args = []
        job_spec.spec.template.spec.containers[0].volume_mounts.append(client.V1VolumeMount(
            mount_path="/var/run/args",
            name="args"
        ))

    created_resources.append(kubernetes.client.BatchV1Api(
        api_client).create_namespaced_job(namespace, job_spec))

    return created_resources


def wait_for_all_jobs(namespace: str, release: str, stage: str, resources: List[kubernetes.client.V1Job]):
    watcher = kubernetes.watch.Watch()

    pending_jobs = set([r.metadata.name for r in resources])

    for event in watcher.stream(
            kubernetes.client.BatchV1Api(api_client).list_namespaced_job, namespace, label_selector=f"bwbble-release={release},bwbble-stage={stage}"):

        if event['object'].status.completion_time:
            pending_jobs.remove(event['object'].metadata.name)

            if len(pending_jobs) == 0:
                watcher.stop()
                return


def run_data_prep(namespace: str, release: str):
    # Do the dataprep job
    api_responses = create_job_resources(
        namespace, release, "data-prep", f"bwbble/mg-ref:{bwbble_container_image_version}")

    # Wait for the data-prep job to complete
    wait_for_all_jobs(namespace, release, "data-prep",
                      [r for r in api_responses if isinstance(r, kubernetes.client.V1Job)])
    print("**** All Jobs completed for dataprep phase of mg-ref ****")

    # Do the combine job
    api_responses = create_job_resources(
        namespace, release, "comb", f"bwbble/mg-ref:{bwbble_container_image_version}")

    # Wait for the data-prep job to complete
    wait_for_all_jobs(
        namespace, [r for r in api_responses if isinstance(r, kubernetes.client.V1Job)])
    print("**** All Jobs completed for comb phase of mg-ref ****")

    return api_responses


def run_index(namespace: str, release: str):
    api_responses = create_job_resources(namespace, release, "index", f"bwbble/mg-aligner:{bwbble_container_image_version}", args=["index",
                                                                                                                                   f"/mg-ref-output/{snp_file}"], resources=client.V1ResourceRequirements(
        limits={
            "memory": "2Gi",
            "cpu": "1"
        },
        requests={
            "memory": "2Gi",
            "cpu": "1"
        }))

    # Wait for the index job to complete
    wait_for_all_jobs(namespace, release, "index", [
                      r for r in api_responses if isinstance(r, kubernetes.client.V1Job)])
    print("**** All Jobs completed for index phase of mg-aligner ****")


def run_align(namespace: str, release: str):
    alignment_jobs = []

    for range in file_ranges:
        api_responses = create_job_resources(namespace, release, "align", f"bwbble/mg-aligner:{bwbble_container_image_version}",
                                             args=[
                                                 "align",
                                                 "-s",
                                                 f"{range.start}",
                                                 "-p",
                                                 f"{range.length}",
                                                 f"/mg-ref-output/{snp_file}",
                                                 f"/input/{reads_file}",
                                                 f"/mg-align-output/{release}.aligned_reads.{range.name}.aln"
                                             ], name_suffix=f"-{range.name}")

        alignment_jobs.extend([
            r for r in api_responses if isinstance(r, kubernetes.client.V1Job)
        ])

    # Wait for the align job to complete
    wait_for_all_jobs(namespace, release, "align", alignment_jobs)
    print("All Jobs completed for align phase of mg-aligner")

    print("**** Starting the merge job ****")
    run_merge(namespace, release)

    print("**** Starting the aln2sam job ****")
    run_aln2sam(namespace, release)

    print("**** Starting the sam_pad job ****")
    run_sam_pad(namespace, release)


def run_merge(namespace: str, release: str):
    merge_command = [
        "cat",
        *[f"/mg-align-output/{release}.aligned_reads.{range.name}.aln" for range in file_ranges],
        ">",
        f"/mg-align-output/{release}.aligned_reads.aln"
    ]

    api_responses = create_job_resources(namespace, release, "merge", "busybox:latest", use_config_map_args=False, use_aci=False,
                                         args=[
                                             "sh",
                                             "-c",
                                             " ".join(
                                                 [f"'{p}'" if " " in p else p for p in merge_command])
                                         ], resources=client.V1ResourceRequirements(
                                             limits={
                                                 "memory": "128Mi",
                                                 "cpu": "1"
                                             },
                                             requests={
                                                 "memory": "128Mi",
                                                 "cpu": "50m"

                                             }))

    # Wait for the merge job to complete
    wait_for_all_jobs(namespace, release, "merge", api_responses)
    print("All Jobs completed for merge phase")


def run_aln2sam(namespace: str, release: str):
    api_responses = create_job_resources(namespace, release, "aln2sam", f"bwbble/mg-aligner:{bwbble_container_image_version}", args=[
        "aln2sam",
        f"/mg-ref-output/{snp_file }",
        f"/input/{reads_file}",
        f"/mg-align-output/{release}.aligned_reads.aln",
        f"/mg-align-output/{release}.aligned_reads.sam"

    ])

    # Wait for the aln2sam job to complete
    wait_for_all_jobs(namespace, release, "aln2sam", [
                      r for r in api_responses if isinstance(r, kubernetes.client.V1Job)])
    print("**** All Jobs completed for aln2sam phase of mg-aligner ****")


def run_sam_pad(namespace: str, release: str):
    api_responses = create_job_resources(namespace, release, "sam-pad", f"bwbble/mg-ref:{bwbble_container_image_version}", args=[
        f"/mg-ref-output/{bubble_file}",
        f"/mg-align-output/{release}.aligned_reads.sam",
        f"/mg-align-output/{release}.output.sam"
    ],
        env=[
        kubernetes.client.V1EnvVar(name="APPLICATION", value="sam_pad"),
    ])

    # Wait for the sam_pad job to complete
    wait_for_all_jobs(namespace, release, "sam-pad",
                      [r for r in api_responses if isinstance(r, kubernetes.client.V1Job)])
    print("All Jobs completed for sam_pad phase of mg-ref")


def kube_test_credentials():

    try:
        api_response = api_instance.get_api_resources()
    except ApiException as e:
        print("Exception when calling API: %s\n" % e)
        sys.exit(0)


def main():
    kube_test_credentials()
    print("**** Done testing credentials ****")
    time_stamp = time.strftime("%H-%M", time.localtime())

    release = f"test-t{time_stamp}-p{parallelism}-fshort"

    # run_index("bwbble-dev", "test-"+time_stamp)
    run_align("bwbble-dev", release)
    execution_times("bwbble-dev", release, "align", align_logs=True)
    execution_times("bwbble-dev", release, "merge")
    execution_times("bwbble-dev", release, "aln2sam")
    execution_times("bwbble-dev", release, "sam-pad")


if __name__ == '__main__':
    main()
