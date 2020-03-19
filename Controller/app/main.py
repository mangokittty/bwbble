from k8sbwbble.job_spec import V1AlignJob, V1AlignJobSpec
from k8sbwbble.controller import Controller
from kubernetes.client import V1ObjectMeta
from kubernetes.config import load_kube_config
import time

if __name__ == "__main__":
    # Load the Kubernetes config file
    load_kube_config()

    controller = Controller()

    parallelism = 10

    time_stamp = time.strftime("%H-%M", time.localtime())
    release = f"test-t{time_stamp}-p{parallelism}-flarge"

    controller.run(
        V1AlignJob(
            metadata=V1ObjectMeta(namespace="bwbble-dev", name=release),
            spec=V1AlignJobSpec(
                align_parallelism=parallelism,
                reads_count=512000,
                reads_file="dummy_reads.fastq",
                bubble_file="chr21_bubble.data",
                snp_file="chr21_ref_w_snp_and_bubble.fasta",
                bwbble_version="313",
            ),
        )
    )
