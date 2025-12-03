import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"

async def wait_for_server(client):
    print("Waiting for server to be ready...")
    for i in range(10):
        try:
            response = await client.get(f"{BASE_URL}/login/access-token", timeout=5.0)
            if response.status_code in [200, 405, 422]: # 405/422 means endpoint exists
                print("Server is ready!")
                return True
        except Exception:
            pass
        print(f"Server not ready, retrying ({i+1}/10)...")
        await asyncio.sleep(2)
    return False

async def test_additional_endpoints():
    # Increase timeout to 60 seconds
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 70)
        print("Testing Additional Backend Endpoints")
        print("=" * 70)

        if not await wait_for_server(client):
            print("❌ Server is not reachable. Is it running?")
            return

        # 1. Login as Admin (needed for some operations)
        print("\n1. Logging in...")
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/login/access-token", data=login_data)
        except httpx.ReadTimeout:
            print("❌ Login timed out. Server might be overloaded or reloading.")
            return

        if response.status_code != 200:
            # Try creating the user if login fails
            print("   ℹ User not found, creating...")
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123"
            }
            await client.post(f"{BASE_URL}/users/", json=user_data)
            response = await client.post(f"{BASE_URL}/login/access-token", data=login_data)
            
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("   ✓ Success: Got token")
        else:
            print("   ✗ Failed to login:", response.text)
            return

        headers = {"Authorization": f"Bearer {token}"}
        
        # Get current user ID
        response = await client.get(f"{BASE_URL}/users/me", headers=headers)
        user_id = response.json()["id"]
        print(f"   ℹ Current User ID: {user_id}")

        # --- User Management Tests ---

        # 2. Search Users
        print("\n2. Testing User Search...")
        response = await client.get(f"{BASE_URL}/users/?q=test", headers=headers)
        if response.status_code == 200:
            users = response.json()
            print(f"   ✓ Success: Found {len(users)} users matching 'test'")
        else:
            print("   ✗ Failed:", response.text)

        # 3. Update User (Self)
        print("\n3. Testing Update User (Self)...")
        # Use /users/me for self update as /users/{id} is admin only
        update_data = {"username": "updated_testuser"}
        response = await client.put(f"{BASE_URL}/users/me", json=update_data, headers=headers)
        if response.status_code == 200:
            print("   ✓ Success: User updated")
            # Revert change
            await client.put(f"{BASE_URL}/users/me", json={"username": "testuser"}, headers=headers)
        else:
            print("   ✗ Failed:", response.text)

        # 4. Change Password
        print("\n4. Testing Change Password...")
        pwd_data = {
            "old_password": "password123",
            "new_password": "newpassword123"
        }
        response = await client.post(f"{BASE_URL}/users/{user_id}/change-password", json=pwd_data, headers=headers)
        if response.status_code == 200:
            print("   ✓ Success: Password changed")
            
            # Verify login with new password
            print("   ℹ Verifying login with new password...")
            new_login = {
                "username": "test@example.com",
                "password": "newpassword123"
            }
            resp = await client.post(f"{BASE_URL}/login/access-token", data=new_login)
            if resp.status_code == 200:
                print("   ✓ Success: Login with new password works")
                token = resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
            else:
                print("   ✗ Failed to login with new password")
                
            # Revert password
            print("   ℹ Reverting password...")
            revert_data = {
                "old_password": "newpassword123",
                "new_password": "password123"
            }
            await client.post(f"{BASE_URL}/users/{user_id}/change-password", json=revert_data, headers=headers)
        else:
            print("   ✗ Failed:", response.text)

        # --- Project Management Tests ---

        # 5. Create Project
        print("\n5. Creating Test Project...")
        project_data = {
            "name": "api-test-project",
            "description": "Project for API testing"
        }
        response = await client.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
        if response.status_code == 200:
            project = response.json()
            project_id = project["id"]
            print(f"   ✓ Success: Project created ({project_id})")
        elif "already exists" in response.text:
            # Get existing
            response = await client.get(f"{BASE_URL}/projects/?q=api-test", headers=headers)
            projects = response.json()
            if projects:
                project = projects[0]
                project_id = project["id"]
                print(f"   ✓ Using existing project ({project_id})")
            else:
                print("   ✗ Failed to find existing project")
                return
        else:
            print("   ✗ Failed:", response.text)
            return

        # 6. Get Project by ID
        print("\n6. Testing Get Project by ID...")
        response = await client.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            print("   ✓ Success: Project details retrieved")
        else:
            print("   ✗ Failed:", response.text)

        # 7. Update Project
        print("\n7. Testing Update Project...")
        update_proj = {"description": "Updated description for API testing"}
        response = await client.put(f"{BASE_URL}/projects/{project_id}", json=update_proj, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["description"] == "Updated description for API testing":
                print("   ✓ Success: Project updated")
            else:
                print("   ✗ Failed: Description not updated")
        else:
            print("   ✗ Failed:", response.text)

        # 8. Search Projects
        print("\n8. Testing Project Search...")
        response = await client.get(f"{BASE_URL}/projects/?q=api-test", headers=headers)
        if response.status_code == 200:
            projects = response.json()
            print(f"   ✓ Success: Found {len(projects)} projects matching 'api-test'")
        else:
            print("   ✗ Failed:", response.text)

        # 9. Cleanup
        print("\n9. Cleaning up...")
        response = await client.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            print("   ✓ Success: Project deleted")
        else:
            print("   ⚠ Warning: Failed to delete project")

        print("\n" + "=" * 70)
        print("Additional Endpoints Test Complete!")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_additional_endpoints())
