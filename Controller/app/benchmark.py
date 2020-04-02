#!/usr/bin/env python
import csv
import statistics
from k8sbwbble.controller import Controller
from k8sbwbble.job_spec import V1AlignJob, V1AlignJobSpec
from kubernetes.client import V1ObjectMeta, CustomObjectsApi
from kubernetes.config import load_kube_config, load_incluster_config
from kubernetes.watch import Watch
from datetime import timedelta
import re

parse_timedelta_regex = re.compile(
    r"(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)(.(?P<microseconds>\d+))?"
)


def parse_timedelta(input: str) -> timedelta:
    parts = parse_timedelta_regex.match(input)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


def main():
    print("Configuring bwbble controller for access to K8s API")

    # Load the Kubernetes config file
    try:
        load_incluster_config()
    except:
        load_kube_config()

    controller = Controller()
    with open("benchmarking_large.csv", mode="w", buffering=1) as bench_file:
        bench_writer = csv.writer(
            bench_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        fields = [
            "total_runtime",
            "align_time",
            "align_job",
            "merge_job",
            "aln2sam_job",
            "sampad_job",
        ]

        bench_writer.writerow(
            [
                "no_containers",
                *[f"{field}_mean" for field in fields],
                *[f"{field}_median" for field in fields],
                *[f"{field}_min" for field in fields],
                *[f"{field}_max" for field in fields],
            ]
        )

        # TODO: Use argparse to provide the namespace as an argument

        # TODO: store some overall stats for the runs

        run_stats = {}
        for parallelism in range(1, 17):

            align_times = []
            align_job_times = []
            merge_job_times = []
            aln2sam_job_times = []
            sampad_job_times = []
            runtimes = []

            for run_index in range(1, 6):
                print(f"Running index {run_index} with parallelism {parallelism}")
                job = V1AlignJob(
                    metadata=V1ObjectMeta(
                        name=f"bench-large-p{parallelism}-r{run_index}",
                        namespace="bwbble-dev",
                    ),
                    spec=V1AlignJobSpec(
                        align_parallelism=parallelism,
                        reads_count=2048000,
                        reads_file="dummy_reads_large.fastq",
                        bubble_file="chr21_bubble.data",
                        snp_file="chr21_ref_w_snp_and_bubble.fasta",
                        bwbble_version="313",
                    ),
                )

                try:
                    controller.create_align_job(job)
                except Exception as ex:
                    print(
                        f"Failed to create V1AlignJob for parallelism={parallelism}, iteration={run_index}"
                    )

                watcher = Watch(return_type=V1AlignJob)
                for event in watcher.stream(
                    CustomObjectsApi(
                        controller.api_client
                    ).list_namespaced_custom_object,
                    "bwbble.aideen.dev",
                    "v1",
                    job.metadata.namespace,
                    "alignjobs",
                ):
                    if event["object"].metadata.name == job.metadata.name:
                        if event["object"].status.end_time is not None:
                            watcher.stop()
                            run_stats[job.metadata.name] = event["object"].status

                            runtimes.append(
                                (
                                    event["object"].status.end_time
                                    - event["object"].status.start_time
                                ).total_seconds()
                            )

                            for tag, stats in {
                                "align": align_job_times,
                                "merge": merge_job_times,
                                "aln2sam": aln2sam_job_times,
                                "sampad": sampad_job_times,
                            }.items():
                                for job_id, times in (
                                    event["object"].status.execution_times[tag].items()
                                ):
                                    stats.append(
                                        parse_timedelta(times["total"]).total_seconds()
                                    )

                            for job_id, times in (
                                event["object"].status.execution_times["align"].items()
                            ):
                                align_times.append(
                                    parse_timedelta(times["internal"]).total_seconds()
                                )

            stats = [
                runtimes,
                align_times,
                align_job_times,
                merge_job_times,
                aln2sam_job_times,
                sampad_job_times,
            ]

            bench_writer.writerow(
                [
                    parallelism,
                    *[timedelta(seconds=statistics.mean(s)) for s in stats],
                    *[timedelta(seconds=statistics.median(s)) for s in stats],
                    *[timedelta(seconds=min(s)) for s in stats],
                    *[timedelta(seconds=max(s)) for s in stats],
                ]
            )


if __name__ == "__main__":
    main()
