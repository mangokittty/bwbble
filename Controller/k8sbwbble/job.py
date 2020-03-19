from .job_spec import V1AlignJob
from kubernetes import client, config, utils
from kubernetes.client import (
    ApiClient,
    BatchV1Api,
    Configuration,
    CoreV1Api,
    V1AzureFileVolumeSource,
    V1ConfigMap,
    V1ConfigMapVolumeSource,
    V1Container,
    V1EnvVar,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplate,
    V1PodTemplateSpec,
    V1ResourceRequirements,
    V1Toleration,
    V1Volume,
    V1VolumeMount,
)
from kubernetes.watch import Watch
from typing import List


class Job(object):
    def __init__(self, stage: str):
        super().__init__()
        self.stage = stage

        configuration = Configuration()
        self.api_client = ApiClient(configuration)
        self.api_instance = BatchV1Api(self.api_client)

    def get_job_name(self, job: V1AlignJob, name_suffix: str = "") -> str:
        return f"bwbble-{job.metadata.name}-{self.stage}{name_suffix}"

    def create_job_resources(
        self,
        job: V1AlignJob,
        container_image: str,
        args: List[str],
        use_config_map_args: bool = True,
        resources: V1ResourceRequirements = None,
        env: List[V1EnvVar] = None,
        name_suffix: str = "",
        use_aci: bool = True,
    ):
        labels = {
            # TODO: Remove this once there are no longer dependencies on it
            "bwbble-release": job.metadata.name,
            "bwbble-alignjob-name": job.metadata.name,
            "bwbble-stage": self.stage,
        }

        resources = resources or V1ResourceRequirements(
            limits={"memory": "2Gi", "cpu": "1"}, requests={"memory": "2Gi", "cpu": "1"}
        )
        created_resources = []
        env_array = []

        if use_aci and not use_config_map_args:
            raise Exception(
                "Azure Container Instances require that arguments are passed using a file"
            )

        if use_config_map_args:
            env_array.append(
                V1EnvVar(name="ARGS_FILE", value="/var/run/args/container_args")
            )

            created_resources.append(
                CoreV1Api(self.api_client).create_namespaced_config_map(
                    job.metadata.namespace,
                    V1ConfigMap(
                        api_version="v1",
                        kind="ConfigMap",
                        metadata=V1ObjectMeta(
                            name=self.get_job_name(job, name_suffix), labels=labels,
                        ),
                        data={
                            "container_args": " ".join(
                                [f"'{a}'" if " " in a else a for a in args]
                            ),
                        },
                    ),
                )
            )

        if env is not None:
            env_array.extend(env)

        job_spec = V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=V1ObjectMeta(
                name=self.get_job_name(job, name_suffix), labels=labels,
            ),
            spec=V1JobSpec(
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(name=self.stage, labels=labels),
                    spec=V1PodSpec(
                        restart_policy="Never",
                        containers=[
                            V1Container(
                                name=self.stage,
                                image=container_image,
                                image_pull_policy="IfNotPresent",
                                args=args,
                                env=env_array,
                                resources=resources,
                                volume_mounts=[
                                    V1VolumeMount(mount_path="/input", name="input"),
                                    V1VolumeMount(
                                        mount_path="/mg-ref-output", name="ref-output"
                                    ),
                                    V1VolumeMount(
                                        mount_path="/mg-align-output",
                                        name="align-output",
                                    ),
                                ],
                            )
                        ],
                        volumes=[
                            V1Volume(
                                name="input",
                                azure_file=V1AzureFileVolumeSource(
                                    secret_name="azure-secret",
                                    share_name="input",
                                    read_only=True,
                                ),
                            ),
                            V1Volume(
                                name="ref-output",
                                azure_file=V1AzureFileVolumeSource(
                                    secret_name="azure-secret",
                                    share_name="ref-output",
                                    read_only=False,
                                ),
                            ),
                            V1Volume(
                                name="align-output",
                                azure_file=V1AzureFileVolumeSource(
                                    secret_name="azure-secret",
                                    share_name="align-output",
                                    read_only=False,
                                ),
                            ),
                        ],
                    ),
                )
            ),
        )

        if use_aci:
            job_spec.spec.template.spec.node_selector = {
                "kubernetes.io/role": "agent",
                "beta.kubernetes.io/os": "linux",
                "type": "virtual-kubelet",
            }

            job_spec.spec.template.spec.tolerations = [
                V1Toleration(key="virtual-kubelet.io/provider", operator="Exists"),
                V1Toleration(key="azure.com/aci", effect="NoSchedule"),
            ]

        if use_config_map_args:

            job_spec.spec.template.spec.volumes.append(
                V1Volume(
                    name="args",
                    config_map=V1ConfigMapVolumeSource(
                        name=f"bwbble-{job.metadata.name}-{self.stage}{name_suffix}"
                    ),
                )
            )

            job_spec.spec.template.spec.containers[0].args = []
            job_spec.spec.template.spec.containers[0].volume_mounts.append(
                V1VolumeMount(mount_path="/var/run/args", name="args")
            )

        created_resources.append(
            BatchV1Api(self.api_client).create_namespaced_job(
                job.metadata.namespace, job_spec
            )
        )

        return created_resources

    def run(self, job: V1AlignJob):
        raise Exception("Not yet implemented")
