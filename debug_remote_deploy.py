import requests
import json
import uuid

API_URL = "http://localhost:8000/api/v1"

def debug():
    # Login
    print("Logging in...")
    r = requests.post(f"{API_URL}/login/access-token", data={"username": "admin@example.com", "password": "password123"})
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Project
    print("Getting projects...")
    r = requests.get(f"{API_URL}/projects/", headers=headers)
    if r.status_code != 200:
        print(f"List projects failed: {r.text}")
        return
        
    projects = r.json()
    if not projects:
        # Create
        print("Creating project...")
        r = requests.post(f"{API_URL}/projects/", json={"name": f"debug-{str(uuid.uuid4())[:6]}", "domain": "example.com"}, headers=headers)
        if r.status_code != 200:
            print(f"Create project failed: {r.text}")
            return
        project_id = r.json()["id"]
    else:
        project_id = projects[0]["id"]
    
    print(f"Using Project ID: {project_id}")
    
    # Get Env
    r = requests.get(f"{API_URL}/environments/", headers=headers)
    envs = r.json()
    if not envs:
        print("No environments found!")
        return
    env_id = envs[0]["id"]
    print(f"Using Env ID: {env_id}")
    
    # Create Deploy
    payload = {
        "name": f"app-{str(uuid.uuid4())[:6]}",
        "image": "nginx",
        "replicas": 1,
        "environment_id": env_id,
        "subdomain": "debug"
    }
    print(f"Creating deployment with payload: {json.dumps(payload, indent=2)}")
    r = requests.post(f"{API_URL}/projects/{project_id}/deployments/", json=payload, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    debug()
