import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_api():
    async with httpx.AsyncClient() as client:
        # 1. Register User
        print("1. Registering User...")
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
        response = await client.post(f"{BASE_URL}/users/", json=user_data)
        if response.status_code == 200:
            print("   Success:", response.json())
        elif response.status_code == 400 and "already exists" in response.text:
             print("   User already exists, proceeding...")
        else:
            print("   Failed:", response.text)
            return

        # 2. Login
        print("\n2. Logging in...")
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        response = await client.post(f"{BASE_URL}/login/access-token", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("   Success: Got token")
        else:
            print("   Failed:", response.text)
            return

        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create Project
        print("\n3. Creating Project...")
        project_data = {
            "name": "my-first-project",
            "description": "A test project"
        }
        response = await client.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
        if response.status_code == 200:
            print("   Success:", response.json())
        else:
            print("   Failed:", response.text)

        # 4. List Projects
        print("\n4. Listing Projects...")
        response = await client.get(f"{BASE_URL}/projects/", headers=headers)
        if response.status_code == 200:
            print("   Success:", response.json())
        else:
            print("   Failed:", response.text)

if __name__ == "__main__":
    asyncio.run(test_api())
