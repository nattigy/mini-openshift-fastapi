import asyncio
import httpx
import subprocess

BASE_URL = "http://localhost:8000/api/v1"

async def test_k8s_integration():
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

        # 2. Create Project with K8s-compatible name
        print("\n2. Creating Project 'test-k8s-project'...")
        project_data = {
            "name": "test-k8s-project",
            "description": "Testing K8s integration"
        }
        response = await client.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
        if response.status_code == 200:
            project = response.json()
            print(f"   ✓ Success: Project created with ID {project['id']}")
            project_id = project['id']
            project_name = project['name']
        else:
            print("   ✗ Failed:", response.text)
            return

        # 3. Verify namespace exists in K8s
        print("\n3. Verifying K8s namespace exists...")
        result = subprocess.run(
            ["kubectl", "get", "namespace", project_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✓ Success: Namespace '{project_name}' exists in K8s")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"   ✗ Failed: Namespace not found in K8s")
            print(f"   {result.stderr}")

        # 4. Test invalid project name (should fail validation)
        print("\n4. Testing invalid project name (uppercase)...")
        invalid_project = {
            "name": "Invalid-Project-Name",
            "description": "This should fail"
        }
        response = await client.post(f"{BASE_URL}/projects/", json=invalid_project, headers=headers)
        if response.status_code == 422:
            print("   ✓ Success: Validation rejected uppercase name")
        else:
            print("   ✗ Failed: Should have rejected invalid name")

        # 5. Delete Project
        print("\n5. Deleting project...")
        response = await client.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            print("   ✓ Success: Project deleted")
        else:
            print("   ✗ Failed:", response.text)

        # 6. Verify namespace is deleted from K8s
        print("\n6. Verifying K8s namespace is deleted...")
        await asyncio.sleep(2)  # Give K8s time to process deletion
        result = subprocess.run(
            ["kubectl", "get", "namespace", project_name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"   ✓ Success: Namespace '{project_name}' deleted from K8s")
        else:
            print(f"   ✗ Warning: Namespace still exists (may be terminating)")

if __name__ == "__main__":
    asyncio.run(test_k8s_integration())
