import asyncio
import httpx
import subprocess
import time

BASE_URL = "http://localhost:8000/api/v1"

async def test_pod_management():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        print("=" * 70)
        print("Testing Pod Management API")
        print("=" * 70)
        
        print("\n1. Logging in...")
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
        print("\n2. Creating test project 'pod-test'...")
        project_data = {
            "name": "pod-test",
            "description": "Project for testing pods"
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
            project = next((p for p in projects if p['name'] == 'pod-test'), None)
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

        # 3. Create a deployment (to have pods)
        print("\n3. Creating deployment 'test-app' to generate pods...")
        deployment_data = {
            "name": "test-app",
            "image": "nginx:alpine",
            "replicas": 2,
            "port": 80
        }
        response = await client.post(
            f"{BASE_URL}/projects/{project_id}/deployments/",
            json=deployment_data,
            headers=headers
        )
        if response.status_code == 201:
            print("   ✓ Success: Deployment created")
        else:
            print("   ✗ Failed:", response.text)
            return

        # Wait for pods to be created
        print("\n4. Waiting for pods to be created (5 seconds)...")
        await asyncio.sleep(5)
        print("   ✓ Wait complete")

        # 5. List pods
        print("\n5. Listing pods in project...")
        response = await client.get(
            f"{BASE_URL}/projects/{project_id}/pods/",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Success: Found {result['total']} pod(s)")
            pods = result['pods']
            if pods:
                for pod in pods:
                    print(f"      - {pod['name']}: {pod['phase']}")
                # Save first pod name for later tests
                test_pod_name = pods[0]['name']
            else:
                print("   ⚠ No pods found yet (may still be creating)")
                test_pod_name = None
        else:
            print("   ✗ Failed:", response.text)
            return

        # 6. Get pod details (if pod exists)
        if test_pod_name:
            print(f"\n6. Getting details for pod '{test_pod_name}'...")
            response = await client.get(
                f"{BASE_URL}/projects/{project_id}/pods/{test_pod_name}",
                headers=headers
            )
            if response.status_code == 200:
                pod = response.json()
                print("   ✓ Success: Pod details retrieved")
                print(f"      Phase: {pod['phase']}")
                print(f"      Node: {pod.get('node_name', 'N/A')}")
                print(f"      Pod IP: {pod.get('pod_ip', 'N/A')}")
                print(f"      Containers: {len(pod['containers'])}")
                for container in pod['containers']:
                    print(f"         - {container['name']}: {container['state']}")
            else:
                print("   ✗ Failed:", response.text)

            # 7. Get pod logs
            print(f"\n7. Getting logs from pod '{test_pod_name}'...")
            response = await client.get(
                f"{BASE_URL}/projects/{project_id}/pods/{test_pod_name}/logs",
                params={"tail_lines": 10},
                headers=headers
            )
            if response.status_code == 200:
                logs_data = response.json()
                print("   ✓ Success: Logs retrieved")
                print(f"      Container: {logs_data['container']}")
                print(f"      Lines: {logs_data['lines']}")
                if logs_data['logs']:
                    print("      First few lines:")
                    for line in logs_data['logs'].split('\n')[:3]:
                        if line.strip():
                            print(f"         {line[:70]}...")
            else:
                print("   ✗ Failed:", response.text)

            # 8. Verify pods in K8s
            print(f"\n8. Verifying pods in K8s...")
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", project_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("   ✓ Success: Pods exist in K8s")
                print(f"   {result.stdout.strip()}")
            else:
                print("   ✗ Failed to verify in K8s")

            # 9. Delete a pod
            print(f"\n9. Deleting pod '{test_pod_name}'...")
            response = await client.delete(
                f"{BASE_URL}/projects/{project_id}/pods/{test_pod_name}",
                headers=headers
            )
            if response.status_code == 200:
                print("   ✓ Success: Pod deleted")
                print("   ℹ Note: Deployment will recreate the pod automatically")
            else:
                print("   ✗ Failed:", response.text)

            # 10. Wait and verify pod recreation
            print("\n10. Waiting for deployment to recreate pod (5 seconds)...")
            await asyncio.sleep(5)
            response = await client.get(
                f"{BASE_URL}/projects/{project_id}/pods/",
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Success: {result['total']} pod(s) now exist")
                print("   ℹ Deployment automatically recreated the pod")
            else:
                print("   ✗ Failed:", response.text)
        else:
            print("\n6-10. Skipped (no pods available yet)")

        # 11. Clean up deployment
        print("\n11. Cleaning up deployment...")
        response = await client.delete(
            f"{BASE_URL}/projects/{project_id}/deployments/test-app",
            headers=headers
        )
        if response.status_code == 200:
            print("   ✓ Success: Deployment deleted")
        else:
            print("   ⚠ Warning: Failed to delete deployment")

        # 12. Clean up project
        print("\n12. Cleaning up test project...")
        response = await client.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            print("   ✓ Success: Project deleted")
        else:
            print("   ⚠ Warning: Failed to delete project")

        print("\n" + "=" * 70)
        print("Pod Management Test Complete!")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_pod_management())
