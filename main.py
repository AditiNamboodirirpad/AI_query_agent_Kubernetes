#IMPORTS
import re
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kubernetes import client, config
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

import os
import logging

# Creating a directory for logs
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join\
                            (log_directory, "agent.log")),
        logging.StreamHandler()  # Log to console
    ]
)


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logging.error("OPENAI_API_KEY not found in environment variables.")
    raise ValueError("Missing OpenAI API key")
else:
    logging.info("Environment variables loaded successfully.")


# Initializing the OpenAI client
openai_client = AsyncOpenAI(api_key=api_key)
logging.info("OpenAI client initialized successfully.")

# Initializing the Kubernetes configuration
from kubernetes import config

try:
    # Works inside the cluster
    config.load_incluster_config()
    logging.info("Loaded in-cluster Kubernetes config")
except config.ConfigException:
    # Fallback for local development
    config.load_kube_config()
    logging.info("Loaded local kubeconfig")

# Initializing the FastAPI application
app = FastAPI()
logging.info("FastAPI application initialized successfully.")


# Defining the request model for the API using Pydantic's BaseModel
# QueryRequest will validate incoming requests, ensuring they contain a 'query' field of type string
class QueryRequest(BaseModel):
    query: str

# Defining the response model for the API using Pydantic's BaseModel
# QueryResponse will format the response sent back to the client, containing the 'query' and 'answer' fields
class QueryResponse(BaseModel):
    query: str
    answer: str


# Function fetches information about all pods in a specified Kubernetes namespace. Returns a list of dictionaries containing pod information, or an empty list if an error occurs.
def get_pods_info(namespace="default"):
    try:
        # Creating an instance of the Kubernetes API client to interact with the Core V1 API
        # Reference to the CoreV1Api for pod operations
        api_instance = client.CoreV1Api()
        # Fetching the list of pods within the specified namespace
        pods = api_instance.list_namespaced_pod(namespace=namespace)
        # Initializing an empty list to hold the information of each pod
        pod_info = []
        # Extracting relevant information for each pod
        for pod in pods.items:
            info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node": pod.spec.node_name,

            }
            pod_info.append(info)
        pod_count = len(pod_info)
        return pod_info, pod_count
   #Exception handling 
    except Exception as e:
        print(f"Error fetching pod information: {e}")
        return [], 0 
     

# Function to fetch deployment information from a specified namespace
def get_deployments_info(namespace="default"):
    try:
         # Creating an instance of the AppsV1Api to interact with Kubernetes deployments
        apps_v1 = client.AppsV1Api()
        # Retrieving the list of deployments in the specified namespace
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
         # Initializing a list to store deployment information
        deployment_info = []
        for deployment in deployments.items:
            info = {
                "name": deployment.metadata.name,
                "replicas": deployment.spec.replicas,
                "available_replicas": deployment.status.available_replicas,
                "ready_replicas": deployment.status.ready_replicas,
                "status": deployment.status.conditions[-1].type if deployment.status.conditions else "Unknown",
                "selector": deployment.spec.selector.match_labels if deployment.spec.selector else {},
                "strategy": deployment.spec.strategy.type if deployment.spec.strategy else "Unknown"
            }
            deployment_info.append(info)
        deployment_count = len(deployment_info)
        return deployment_info, deployment_count
    #Exception handling 
    except Exception as e:
        logging.error(f"Error fetching deployment information: {e}")
        return [],0


# Function to fetch logs from a specific pod in a specified namespace
def get_pod_logs(pod_name, namespace="default"):
    try:
        # Creating an instance of the CoreV1Api to interact with the Kubernetes API.
        api_instance = client.CoreV1Api()
        # Fetching the logs of the specified pod in the provided namespace.
        # This method reads the log of the pod and returns it as a string.
        logs = api_instance.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        return logs
    except Exception as e:
        logging.error(f"Error fetching logs for pod {pod_name}: {e}")
        # Returning an empty string if an error occurs to prevent the application from crashing.
        return ""


# Function to provide details about each node
def get_nodes_info():
    try:
        # Creating an instance of the CoreV1Api to interact with Kubernetes nodes
        api_instance = client.CoreV1Api()
        # Listing all nodes in the cluster
        nodes = api_instance.list_node()
        
        # Initializing an empty list to store node information
        node_info = []
        # Counting nodes in the cluster
        node_count = len(nodes.items)

        # Logging the total number of nodes in the cluster
        logging.info(f"Total number of nodes in the cluster: {node_count}")

        # Extracting relevant information for each node
        for node in nodes.items:
            info = {
                "name": node.metadata.name,
                "status": node.status.conditions[-1].type if node.status.conditions else "Unknown",
                "labels": node.metadata.labels,
                "node_ip": node.status.addresses[0].address if node.status.addresses else "Unknown",
                "unschedulable": node.spec.unschedulable if hasattr(node.spec, "unschedulable") else False
            }
            node_info.append(info)

        # Returning node information along with the count of nodes
        return node_info, node_count  
    except Exception as e:
        logging.error(f"Error fetching nodes information: {e}")
        return [], 0  # Returning empty list and count 0


# Defining a POST endpoint at the "/query" route, specifying that it returns a QueryResponse model
@app.post("/query", response_model=QueryResponse)
async def query_kubernetes(request: QueryRequest):
    # Logging the received query to track incoming requests for debugging and analytics
    logging.info("Received query: %s", request.query)
    try:
        # Determining if the query is for pod logs
        if "log" in request.query.lower():
            # Using regular expression to extract pod name
            # Match "log ... <pod-name>" in a flexible way
            match = re.search(r"log\s+(?:for\s+)?(?:the\s+pod\s+)?([a-zA-Z0-9-]+)", request.query, re.IGNORECASE)
            if match:
                pod_name = match.group(1).strip()
                logs = get_pod_logs(pod_name, namespace="default")
                return QueryResponse(query=request.query, answer=logs)
            else:
                return QueryResponse(query=request.query, answer="Pod name not found in the query.")

            # match = re.search(r"log for the pod (.+?) in the default namespace", request.query, re.IGNORECASE)
            # if match:
            #     # Extracting the pod name from the matched group
            #     pod_name = match.group(1).strip()  
            #     logging.info("Extracted pod name: %s", pod_name)
            #     # Fetching logs for the specified pod
            #     logs = get_pod_logs(pod_name, namespace="default")
            #     return QueryResponse(query=request.query, answer=logs)
            # else:
            #     logging.error("Pod name not found in query: %s", request.query)
            #     return QueryResponse(query=request.query, answer="Pod name not found in the query.")


        # Fetching information from the functions get_pods_info, get_deployments_info, and get_nodes_info
        pod_data, pod_count = get_pods_info(namespace="default")
        deployment_data, deployment_count = get_deployments_info(namespace="default")
        node_data, node_count = get_nodes_info()

        # if "how many pods" in request.query.lower():
        #     return QueryResponse(query=request.query, answer=str(pod_count))

        # elif "get pods" in request.query.lower():
        #     names = "\n".join([p["name"] for p in pod_data])
        #     return QueryResponse(query=request.query, answer=names)

        # Creating structured JSON-style context
        context = {
            "pods": pod_data,
            "deployments": deployment_data,
            "nodes": node_data,
            "pod_count": pod_count,
            "deployment_count": deployment_count,
            "node_count": node_count
        }

        # Constructing a prompt for the AI assistant, Tweaking the system prompt to get the answers in a clear and concize format.
        #prompt = "You are an AI assistant that answers only Kubernetes-related queries. If the user asks how many pods, return the number.If the user asks for pod names, return the names. If the user asks about deployments or nodes, return that information clearly.Analyze the following Kubernetes pods, deployment and node data:\n" + "\n".join( [f"Pod name: {pod['name']}, Namespace: {pod['namespace']}, Status: {pod['status']}, Node: {pod['node']}" for pod in pod_data] ) + "\n".join( [f"Name: {deployment['name']}, Replicas: {deployment['replicas']}, Available: {deployment['available_replicas']}, Status: {deployment['status']}" for deployment in deployment_data] ) + "\n".join( [f"Name: {node['name']}, Status: {node['status']}, Node IP: {node['node_ip']}, Unschedulable: {node['unschedulable']}" for node in node_data] )
        # Prompt with strict instructions
        openai_message = [
            {
                "role": "system",
                "content": (
                    "You are a Kubernetes assistant. "
                    "Answer in clear, natural sentences. "
                    "Base all responses ONLY on the provided JSON cluster data. "
                    "If the user asks for counts, state them in a sentence "
                    "(e.g., 'There are 5 pods running in the default namespace.'). "
                    "If they ask for names, list them naturally in one sentence. "
                    "If they ask about deployments or nodes, summarize them clearly."
                )
            },
            {
                "role": "user",
                "content": f"Cluster data:\n{json.dumps(context, indent=2)}\n\nQuestion: {request.query}"
            }
        ]

        # # The messages for the OpenAI API, with a system message and the user's query
        # openai_message = [
        #     {
        #         "role": "system",
        #         "content": f"{prompt}"
        #     },
        #     {
        #         "role": "user",
        #         "content": f"{request.query}"
        #     } 
        # ]

        # Using OpenAI chat API
        openai_response = await openai_client.chat.completions.create(
            messages=openai_message,
            model="gpt-4o"
        )

        # Extracting OpenAI response and preparing the answer
        enhanced_answer = openai_response.choices[0].message.content
        logging.info("OpenAI response received successfully.")
        return QueryResponse(query=request.query, answer=enhanced_answer)
    
    except Exception as e:
        # Logging any errors that occur during the process for troubleshooting
        logging.error("An error occurred: %s", e, exc_info=True)  # Log the error
        raise HTTPException(status_code=500, detail=str(e))
    


    
# Entry point for running the app
if __name__ == "__main__":
    # Importing the Uvicorn ASGI server to run the FastAPI application
    import uvicorn
    logging.info("Starting FastAPI server on port 8000...")
    # Running the FastAPI application using Uvicorn, making it accessible on all interfaces (0.0.0.0) at port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
