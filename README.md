# Cleric Query Agent Assignment

## Overview
This project implements an AI agent using FastAPI that interacts with a Kubernetes cluster to answer queries related to applications deployed within it. The agent utilizes OpenAI's API for natural language processing.

## Technologies Used
- **Python 3.10**: Programming language for the implementation.
- **FastAPI**: Framework for building the web application.
- **OpenAI API**: For natural language processing.
- **Kubernetes Client**: For interacting with the Kubernetes API.
- **Docker & Minikube**: For containerization and local Kubernetes deployment.

### Environment and Application Setup
1. **Environment Preparation**:
   - Install Python 3.10 along with necessary libraries (FastAPI, Pydantic, OpenAI, Kubernetes, etc.).
   - Configure a `.env` file to securely store sensitive information, including the OpenAI API key.
   - Set up logging to monitor application behavior, with logs stored in a `logs` directory and output to the console for real-time tracking.

2. **Docker and Kubernetes Configuration**:
   - Ensure that **Docker** and **Minikube** are installed and properly configured on your system.
   - Start the Minikube cluster to prepare it for interaction with the FastAPI application.

3. **Running the Application**:
   - Run the FastAPI application with `main.py`, which will serve the application on port 8000.
   - Access the API at `http://localhost:8000/query` to submit queries.
     
4. **Testing with Postman**:
   - Test the API using **Postman** by sending a POST request to `http://localhost:8000/query` with a JSON body containing your query. The API will return a response formatted according to the `QueryResponse` model.

5. **Logging**:
   - All logs are stored in `logs/agent.log`, providing a record of the application's flow and errors for easy troubleshooting.

## Code Workflow
1. **Imports**:
   - Imported necessary libraries such as FastAPI, logging, Pydantic for data validation, and Kubernetes client for API interaction.

2. **Environment Variables**:
   - Loaded environment variables from a `.env` file to retrieve the OpenAI API key.

3. **FastAPI Application**:
   - Initialized a FastAPI application instance to create the web server.

4. **Data Models**:
   - Defined request and response models using Pydantic:
     - `QueryRequest`: Validates incoming requests containing a `query` field.
     - `QueryResponse`: Formats the outgoing response with `query` and `answer` fields.

5. **Kubernetes API Interactions**:
   - Developed functions to interact with the Kubernetes cluster:
     - **`get_pods_info`**: Fetches information about all pods in a specified namespace.
     - **`get_deployments_info`**: Retrieves deployment information.
     - **`get_pod_logs`**: Fetches logs from a specified pod.
     - **`get_nodes_info`**: Provides details about each node in the cluster, including status and labels.

6. **API Endpoint**:
   - Created a POST endpoint (`/query`) to handle incoming queries:
     - Logged the received query for debugging purposes.
     - Analyzed the query to determine if it pertains to pod logs or general Kubernetes information.
     - Constructed a prompt for the OpenAI API based on the current state of pods, deployments, and nodes.
     - Used the OpenAI API to generate a natural language response based on the query and Kubernetes data.

7. **Error Handling**:
   - Implemented error handling to log errors and return appropriate HTTP exceptions when issues occur.

8. **Application Execution**:
   - Set up the entry point to run the FastAPI application using Uvicorn on port 8000.

## Conclusion
This project demonstrates the integration of FastAPI, Kubernetes, and OpenAI to create a functional AI agent capable of understanding and responding to queries about Kubernetes resources. The use of logging and error handling ensures robust application performance.
