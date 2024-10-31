#IMPORTS
import re
# Importing FastAPI for building the web application and HTTPException for handling exceptions
from fastapi import FastAPI, HTTPException
# Logging module for console logging to track program flow and debug information
import logging
import os
# Creating a directory for logs
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_directory, "agent.log")), 
        logging.StreamHandler()  # Log to console
    ]
)
logging.info("FastAPI and HTTPException imported successfully.")

# Importing Pydantic's BaseModel to define data validation and serialization for request bodies
from pydantic import BaseModel
logging.info("Pydantic imported successfully.")

# Importing OS module to interact with environment variables and the file system
import os
logging.info("OS module imported successfully.")


# Importing Kubernetes client and config modules to interact with Kubernetes API
from kubernetes import client, config
logging.info("Kubernetes client and config imported successfully.")

# Importing asyncio module for asynchronous programming, necessary for non-blocking I/O operations
import asyncio
logging.info("Asyncio imported successfully.")

# Importing AsyncOpenAI for making asynchronous API calls to OpenAI's API
from openai import AsyncOpenAI
logging.info("OpenAI AsyncOpenAI imported successfully.")

# Importing load_dotenv from dotenv to load environment variables from a .env file into the application
from dotenv import load_dotenv
# Loading the environment variables from .env file
load_dotenv()
logging.info("Dotenv load_dotenv imported successfully and environment variables loaded.")

# Loading the OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
logging.info("OpenAI API key set successfully.")

# Initializing the OpenAI client
openai_client = AsyncOpenAI(api_key=api_key)
logging.info("OpenAI client initialized successfully.")

# Initializing the Kubernetes configuration
config.load_kube_config()
logging.info("Kubernetes configuration loaded successfully.")

# Initializing the FastAPI application
app = FastAPI()
logging.info("FastAPI application initialized successfully.")


# Defining the request model for the API using Pydantic's BaseModel
# QueryRequest will validate incoming requests, ensuring they contain a 'query' field of type string
class QueryRequest(BaseModel):
    query: str
logging.info("QueryRequest model defined successfully.")

# Defining the response model for the API using Pydantic's BaseModel
# QueryResponse will format the response sent back to the client, containing the 'query' and 'answer' fields
class QueryResponse(BaseModel):
    query: str
    answer: str
logging.info("QueryResponse model defined successfully.")


# Function fetches information about all pods in a specified Kubernetes namespace. Returns a list of dictionaries containing pod information, or an empty list if an error occurs.
def get_pods_info(namespace="default"):
    try:
        # Creating an instance of the Kubernetes API client to interact with the Core V1 API
        # Reference to the CoreV1Api for pod operations
        api_instance = client.CoreV1Api()
        # Fetching the list of pods within the specified namespace
        pods = api_instance.list_namespaced_pod(namespace="default")
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
        return pod_info
   #Exception handling 
    except Exception as e:
        print(f"Error fetching pod information: {e}")
        return []

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
        return deployment_info
    #Exception handling 
    except Exception as e:
        logging.error(f"Error fetching deployment information: {e}")
        return []


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
            match = re.search(r"log for the pod (.+?) in the default namespace", request.query, re.IGNORECASE)
            if match:
                # Extracting the pod name from the matched group
                pod_name = match.group(1).strip()  
                logging.info("Extracted pod name: %s", pod_name)
                # Fetching logs for the specified pod
                logs = get_pod_logs(pod_name, namespace="default")
                return QueryResponse(query=request.query, answer=logs)
            else:
                logging.error("Pod name not found in query: %s", request.query)
                return QueryResponse(query=request.query, answer="Pod name not found in the query.")

        # Fetching information from the functions get_pods_info, get_deployments_info, and get_nodes_info
        pod_data = get_pods_info(namespace="default")
        deployment_data = get_deployments_info(namespace="default")
        node_data, node_count = get_nodes_info()

        # Constructing a prompt for the AI assistant, Tweaking the system prompt to get the answers in a clear and concize format.
        prompt = "You are an Ai assistant and provide assistance to only kubernetes related queries.If the user asks how many pods just give the number of pods precisely and not more than that.Analyze the following Kubernetes pods, deployment and node data:\n" + "\n".join(
        [f"Pod name: {pod['name']}, Namespace: {pod['namespace']}, Status: {pod['status']}, Node: {pod['node']}" for pod in pod_data]
    ) + "\n".join(
        [f"Name: {deployment['name']}, Replicas: {deployment['replicas']}, Available: {deployment['available_replicas']}, Status: {deployment['status']}" for deployment in deployment_data]
     ) + "\n".join(
                [f"Name: {node['name']}, Status: {node['status']}, Node IP: {node['node_ip']}, Unschedulable: {node['unschedulable']}" for node in node_data]
            )



        # The messages for the OpenAI API, with a system message and the user's query
        openai_message = [
            {
                "role": "system",
                "content": f"{prompt}"
            },
            {
                "role": "user",
                "content": f"{request.query}"
            } 
        ]

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
