#!/usr/bin/env python
from kubernetes.client.rest import ApiException
from kubernetes import client, config
import re
from datetime import timedelta


def main():
    config.load_kube_config()
    pod_name = "bwbble-align-dummylargereads1-range-0--1-799ms"
    try:
        api_instance = client.CoreV1Api()
        api_response = api_instance.list_namespaced_pod(
            namespace='bwbble-dev', label_selector="bwbble-stage=align")
        for item in api_response.items:
            logs = api_instance.read_namespaced_pod_log(
                item.metadata.name, 'bwbble-dev', container='align', tail_lines=100)
            if logs:
                rem = re.search(
                    r"read alignment time: (\d+\.?\d*) sec", logs, re.IGNORECASE)

                if rem:
                    print(item.metadata.name, ": ",
                          timedelta(seconds=float(rem[1]))
                          )

            for containerStatus in item.status.container_statuses:
                if containerStatus.state.terminated:
                    print(item.metadata.name, "::", containerStatus.name, ": ",
                          containerStatus.state.terminated.finished_at - containerStatus.state.terminated.started_at)
                else:
                    print(item.metadata.name, "::",
                          containerStatus.name, ": Not yet finished")
        print("----------------------------------------------")

    except ApiException as e:
        print(e)


if __name__ == '__main__':
    main()
