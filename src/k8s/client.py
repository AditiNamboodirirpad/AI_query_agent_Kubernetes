# Sets up the Kubernetes connection — tries in-cluster first, then local kubeconfig
from kubernetes import config


def init_k8s():
    try:
        config.load_incluster_config()
        print("Connected using in-cluster Kubernetes config")
    except config.ConfigException:
        config.load_kube_config()
        print("Connected using local kubeconfig")
