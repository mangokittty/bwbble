from k8sbwbble.controller import Controller
from kubernetes.config import load_kube_config, load_incluster_config

if __name__ == "__main__":
    print("Configuring bwbble controller for access to K8s API")

    # Load the Kubernetes config file
    try:
        load_incluster_config()
    except:
        load_kube_config()

    controller = Controller()

    # TODO: Use argparse to provide the namespace as an argument

    print("Starting controller for namespace bwbble-dev")
    controller.run("bwbble-dev")
