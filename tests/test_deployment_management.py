import asyncio
import httpx
import subprocess

BASE_URL = "http://localhost:8000/api/v1"

async def test_deployment_management():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("1. Logging in...")
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        response = await client.post(f"{BASE_URL}/login/access-token", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("   ✓ Success: Got token")
        else:
            print("   ✗ Failed:", response.text)
            return

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create a test project
        print("\n2. Creating test project 'deployment-test'...")
        project_data = {
            "name": "deployment-test",
            "description": "Project for testing deployments"
        }
        response = await client.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
        if response.status_code == 200:
            project = response.json()
            project_id = project['id']
            project_name = project['name']
            print(f"   ✓ Success: Project created with ID {project_id}")
        elif "already exists" in response.text:
            # Get existing project
            response = await client.get(f"{BASE_URL}/projects/", headers=headers)
            projects = response.json()
            project = next((p for p in projects if p['name'] == 'deployment-test'), None)
            if project:
                project_id = project['id']
                project_name = project['name']
                print(f"   ✓ Using existing project with ID {project_id}")
            else:
                print("   ✗ Failed to find project")
                return
        else:
            print("   ✗ Failed:", response.text)
            return

        # 3. Create a deployment
        print("\n3. Creating deployment 'nginx-app'...")
        deployment_data = {
            "name": "nginx-app",
            "image": "nginx:latest",
            "replicas": 2,
            "port": 80,
            "labels": {
                "app": "nginx",
                "tier": "frontend"
            }
        }
        response = await client.post(
            f"{BASE_URL}/projects/{project_id}/deployments/",
            json=deployment_data,
            headers=headers
        )
        if response.status_code == 201:
            deployment = response.json()
            print(f"   ✓ Success: Deployment created")
            print(f"      Name: {deployment['name']}")
            print(f"      Image: {deployment['image']}")
            print(f"      Replicas: {deployment['replicas']}")
        else:
            print("   ✗ Failed:", response.text)
            return

        # 4. Verify deployment in K8s
        print("\n4. Verifying deployment in K8s...")
        result = subprocess.run(
            ["kubectl", "get", "deployment", "nginx-app", "-n", project_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✓ Success: Deployment exists in K8s")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"   ✗ Failed: Deployment not found in K8s")

        # 5. List deployments
        print("\n5. Listing deployments...")
        response = await client.get(
            f"{BASE_URL}/projects/{project_id}/deployments/",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Success: Found {result['total']} deployment(s)")
            for dep in result['deployments']:
                print(f"      - {dep['name']}: {dep['ready_replicas']}/{dep['replicas']} ready")
        else:
            print("   ✗ Failed:", response.text)

        # 6. Get deployment details
        print("\n6. Getting deployment details...")
        response = await client.get(
            f"{BASE_URL}/projects/{project_id}/deployments/nginx-app",
            headers=headers
        )
        if response.status_code == 200:
            deployment = response.json()
            print(f"   ✓ Success: Got deployment details")
            print(f"      Ready: {deployment['ready_replicas']}/{deployment['replicas']}")
            print(f"      Available: {deployment['available_replicas']}")
        else:
            print("   ✗ Failed:", response.text)

        # 7. Scale deployment
        print("\n7. Scaling deployment to 3 replicas...")
        response = await client.patch(
            f"{BASE_URL}/projects/{project_id}/deployments/nginx-app/scale",
            json={"replicas": 3},
            headers=headers
        )
        if response.status_code == 200:
            deployment = response.json()
            print(f"   ✓ Success: Scaled to {deployment['replicas']} replicas")
        else:
            print("   ✗ Failed:", response.text)

        # 8. Verify scaling in K8s
        print("\n8. Verifying scaling in K8s...")
        await asyncio.sleep(2)  # Give K8s time to update
        result = subprocess.run(
            ["kubectl", "get", "deployment", "nginx-app", "-n", project_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✓ Success: Deployment scaled in K8s")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"   ✗ Failed to verify scaling")

        # 9. Delete deployment
        print("\n9. Deleting deployment...")
        response = await client.delete(
            f"{BASE_URL}/projects/{project_id}/deployments/nginx-app",
            headers=headers
        )
        if response.status_code == 200:
            print(f"   ✓ Success: Deployment deleted")
        else:
            print("   ✗ Failed:", response.text)

        # 10. Verify deletion in K8s
        print("\n10. Verifying deletion in K8s...")
        await asyncio.sleep(2)
        result = subprocess.run(
            ["kubectl", "get", "deployment", "nginx-app", "-n", project_name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"   ✓ Success: Deployment deleted from K8s")
        else:
            print(f"   ✗ Warning: Deployment still exists (may be terminating)")

        # 11. Clean up project
        print("\n11. Cleaning up test project...")
        response = await client.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            print(f"   ✓ Success: Project deleted")
        else:
            print("   ✗ Failed:", response.text)

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Deployment Management API")
    print("=" * 60)
    asyncio.run(test_deployment_management())
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
