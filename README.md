# K8sGPT — AI Kubernetes Assistant

[![CI](https://github.com/AditiNamboodirirpad/AI_query_agent_Kubernetes/actions/workflows/ci.yml/badge.svg)](https://github.com/AditiNamboodirirpad/AI_query_agent_Kubernetes/actions/workflows/ci.yml)

## Demo

[![K8sGPT Demo](https://asciinema.org/a/855106.svg)](https://asciinema.org/a/855106)

---

## What is this?

I built this because I found Kubernetes really hard to navigate at first — there are so many `kubectl` commands just to check basic things. So I made an AI assistant that lets you ask plain English questions about your cluster and get real answers.

You type `k8sgpt` in the terminal and just... talk to it.

```
You › how many pods are running?
You › why is my deployment failing?
You › show me logs for pod nginx-abc123
You › how is my cluster doing overall?
```

The AI figures out which Kubernetes data it needs to answer each question — it doesn't just dump everything at once.

---

## How it works

The app has two parts:

1. **A FastAPI server** that connects to the Kubernetes cluster and exposes a `/query` endpoint
2. **A terminal chat client** (`k8sgpt` command) that talks to the server

When you ask a question, the server passes it to a **LangGraph agent**. The agent uses Claude (Anthropic) to decide which Kubernetes tools to call — things like `list_pods`, `get_pod_logs`, `list_events` — and then combines the results into an answer.

```
Your question
    ↓
Claude thinks: "I need pod data for this"
    ↓
Agent calls list_pods tool → gets real cluster data
    ↓
Claude thinks: "I have enough to answer"
    ↓
You get a clear answer
```

This is called a ReAct agent (Reason + Act). It's different from just sending all your cluster data to an LLM every time — the agent only fetches what it actually needs.

---

## Tech stack

- Python 3.10
- FastAPI + Uvicorn
- LangGraph (ReAct agent pattern)
- Claude via `langchain-anthropic`
- Kubernetes Python client
- Pydantic v2
- Docker + Minikube (local Kubernetes cluster)

---

## Setup

### What you need
- Python 3.10+
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed
- Docker Desktop running
- An [Anthropic API key](https://console.anthropic.com)

### Install

```bash
git clone https://github.com/AditiNamboodirirpad/AI_query_agent_Kubernetes.git
cd AI_query_agent_Kubernetes

pip install -r requirements.txt
pip install -e .  # registers the k8sgpt command
```

### Configure

```bash
cp .env.example .env
# open .env and add your ANTHROPIC_API_KEY
```

### Start Minikube

```bash
minikube start --driver=docker --kubernetes-version=v1.32.0
```

### Run the server

```bash
uvicorn main:app --port 8000
```

### Use the terminal client

```bash
k8sgpt
```

That's it. You should see `Kubernetes connected` and can start asking questions.

---

## Deploy to Kubernetes (Minikube)

```bash
# Point Docker at Minikube so the image is built inside the cluster
eval $(minikube docker-env)
docker build -t k8sgpt:latest .

# Create a secret for the API key
kubectl create secret generic anthropic-secret \
  --from-literal=ANTHROPIC_API_KEY="your_key_here"

# Apply RBAC permissions and deploy the app
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment.yaml

# Check it's running
kubectl get pods

# Open the service
minikube service k8sgpt-service
```

---

## API endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/query` | POST | Ask the agent a question |
| `/health` | GET | Check if the server and cluster are reachable |
| `/cluster/health` | GET | Get a 0–100 health score with AI analysis |
| `/sessions/{id}` | DELETE | Clear conversation history |

The Swagger UI is available at `http://localhost:8000/docs` when the server is running.

---

## Example queries to try

```bash
# Deploy some test workloads first
kubectl create deployment nginx --image=nginx --replicas=3
kubectl create deployment broken-app --image=nginx:doesnotexist --replicas=2

# Then ask the agent
k8sgpt
```

```
You › how many pods are running?
You › why is broken-app failing?
You › how do I fix it?
You › what is my cluster health score?
```

---

## Project structure

```
src/
  k8s/        # functions that call the Kubernetes API
  agent/      # LangGraph agent, tools, and conversation memory
  api/        # FastAPI routes and models
cli/          # terminal chat client (the k8sgpt command)
k8s/          # Kubernetes deployment manifests and RBAC config
tests/        # unit and integration tests
```

---

## Running tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```
