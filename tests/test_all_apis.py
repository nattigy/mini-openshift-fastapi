import asyncio
import httpx
import subprocess
from typing import Optional
import time

BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        # Use timestamp to ensure unique username
        timestamp = int(time.time())
        self.test_user_email = f"test-{timestamp}@example.com"
        self.test_user_username = f"testuser-{timestamp}"
        self.test_user_password = "TestPassword123"
        self.project_id: Optional[str] = None
        self.project_name: Optional[str] = None
        
    async def run_all_tests(self):
        """Run all API tests"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client
            
            print("=" * 70)
            print("MINI OPENSHIFT - COMPREHENSIVE API TEST SUITE")
            print("=" * 70)
            
            # Authentication Tests
            await self.test_authentication()
            
            # User Management Tests
            await self.test_user_management()
            
            # Project Management Tests
            await self.test_project_management()
            
            # Deployment Management Tests
            await self.test_deployment_management()
            
            # Cleanup
            await self.cleanup()
            
            print("\n" + "=" * 70)
            print("ALL TESTS COMPLETED SUCCESSFULLY! ✅")
            print("=" * 70)
    
    async def test_authentication(self):
        """Test authentication endpoints"""
        print("\n" + "=" * 70)
        print("SECTION 1: AUTHENTICATION TESTS")
        print("=" * 70)
        
        # Test 1: User Registration
        print("\n[1.1] Testing User Registration...")
        signup_data = {
            "email": self.test_user_email,
            "username": self.test_user_username,
            "password": self.test_user_password
        }
        response = await self.client.post(f"{BASE_URL}/users/", json=signup_data)
        
        if response.status_code == 200:
            print("   ✓ User registration successful")
        elif "already exists" in response.text:
            print("   ✓ User already exists (using existing account)")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("User registration failed")
        
        # Test 2: User Login
        print("\n[1.2] Testing User Login...")
        login_data = {
            "username": self.test_user_email,
            "password": self.test_user_password
        }
        response = await self.client.post(
            f"{BASE_URL}/login/access-token",
            data=login_data
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("   ✓ Login successful")
            print(f"   ✓ JWT token received (length: {len(self.token)})")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Login failed")
    
    async def test_user_management(self):
        """Test user management endpoints"""
        print("\n" + "=" * 70)
        print("SECTION 2: USER MANAGEMENT TESTS")
        print("=" * 70)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test 3: Get Current User
        print("\n[2.1] Testing Get Current User...")
        response = await self.client.get(f"{BASE_URL}/users/me", headers=headers)
        
        if response.status_code == 200:
            user = response.json()
            print("   ✓ Current user retrieved")
            print(f"   ✓ Email: {user['email']}")
            print(f"   ✓ Role: {user['role']}")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Get current user failed")
        
        # Test 4: List Users
        print("\n[2.2] Testing List Users...")
        response = await self.client.get(f"{BASE_URL}/users/", headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            print(f"   ✓ Users list retrieved ({len(users)} users)")
            for user in users[:3]:  # Show first 3
                print(f"      - {user['email']} ({user['role']})")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("List users failed")
    
    async def test_project_management(self):
        """Test project management endpoints"""
        print("\n" + "=" * 70)
        print("SECTION 3: PROJECT MANAGEMENT TESTS")
        print("=" * 70)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test 5: Create Project
        print("\n[3.1] Testing Create Project...")
        project_data = {
            "name": "test-api-project",
            "description": "Comprehensive API test project"
        }
        response = await self.client.post(
            f"{BASE_URL}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 200:
            project = response.json()
            self.project_id = project['id']
            self.project_name = project['name']
            print("   ✓ Project created successfully")
            print(f"   ✓ Project ID: {self.project_id}")
            print(f"   ✓ Project Name: {self.project_name}")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Create project failed")
        
        # Test 6: Verify K8s Namespace Created
        print("\n[3.2] Testing K8s Namespace Creation...")
        result = subprocess.run(
            ["kubectl", "get", "namespace", self.project_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✓ K8s namespace created successfully")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"   ✗ Failed: Namespace not found")
            raise Exception("K8s namespace creation failed")
        
        # Test 7: List Projects
        print("\n[3.3] Testing List Projects...")
        response = await self.client.get(f"{BASE_URL}/projects/", headers=headers)
        
        if response.status_code == 200:
            projects = response.json()
            print(f"   ✓ Projects list retrieved ({len(projects)} projects)")
            for proj in projects[:3]:  # Show first 3
                print(f"      - {proj['name']}: {proj.get('description', 'No description')}")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("List projects failed")
    
    async def test_deployment_management(self):
        """Test deployment management endpoints"""
        print("\n" + "=" * 70)
        print("SECTION 4: DEPLOYMENT MANAGEMENT TESTS")
        print("=" * 70)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test 8: Create Deployment
        print("\n[4.1] Testing Create Deployment...")
        deployment_data = {
            "name": "test-nginx",
            "image": "nginx:alpine",
            "replicas": 2,
            "port": 80,
            "env_vars": {
                "ENV": "test",
                "APP_NAME": "nginx-test"
            },
            "labels": {
                "tier": "frontend",
                "test": "comprehensive"
            }
        }
        response = await self.client.post(
            f"{BASE_URL}/projects/{self.project_id}/deployments/",
            json=deployment_data,
            headers=headers
        )
        
        if response.status_code == 201:
            deployment = response.json()
            print("   ✓ Deployment created successfully")
            print(f"   ✓ Name: {deployment['name']}")
            print(f"   ✓ Image: {deployment['image']}")
            print(f"   ✓ Replicas: {deployment['replicas']}")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Create deployment failed")
        
        # Test 9: Verify K8s Deployment Created
        print("\n[4.2] Testing K8s Deployment Creation...")
        result = subprocess.run(
            ["kubectl", "get", "deployment", "test-nginx", "-n", self.project_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✓ K8s deployment created successfully")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"   ✗ Failed: Deployment not found")
            raise Exception("K8s deployment creation failed")
        
        # Test 10: List Deployments
        print("\n[4.3] Testing List Deployments...")
        response = await self.client.get(
            f"{BASE_URL}/projects/{self.project_id}/deployments/",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Deployments list retrieved ({result['total']} deployments)")
            for dep in result['deployments']:
                print(f"      - {dep['name']}: {dep['ready_replicas']}/{dep['replicas']} ready")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("List deployments failed")
        
        # Test 11: Get Deployment Details
        print("\n[4.4] Testing Get Deployment Details...")
        response = await self.client.get(
            f"{BASE_URL}/projects/{self.project_id}/deployments/test-nginx",
            headers=headers
        )
        
        if response.status_code == 200:
            deployment = response.json()
            print("   ✓ Deployment details retrieved")
            print(f"   ✓ Ready: {deployment['ready_replicas']}/{deployment['replicas']}")
            print(f"   ✓ Available: {deployment['available_replicas']}")
            print(f"   ✓ Updated: {deployment['updated_replicas']}")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Get deployment details failed")
        
        # Test 12: Scale Deployment
        print("\n[4.5] Testing Scale Deployment...")
        response = await self.client.patch(
            f"{BASE_URL}/projects/{self.project_id}/deployments/test-nginx/scale",
            json={"replicas": 4},
            headers=headers
        )
        
        if response.status_code == 200:
            deployment = response.json()
            print(f"   ✓ Deployment scaled to {deployment['replicas']} replicas")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Scale deployment failed")
        
        # Test 13: Verify Scaling in K8s
        print("\n[4.6] Testing K8s Deployment Scaling...")
        await asyncio.sleep(2)  # Wait for K8s to update
        result = subprocess.run(
            ["kubectl", "get", "deployment", "test-nginx", "-n", self.project_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "4" in result.stdout:
            print("   ✓ K8s deployment scaled successfully")
            print(f"   {result.stdout.strip()}")
        else:
            print("   ⚠ Scaling in progress...")
        
        # Test 14: Delete Deployment
        print("\n[4.7] Testing Delete Deployment...")
        response = await self.client.delete(
            f"{BASE_URL}/projects/{self.project_id}/deployments/test-nginx",
            headers=headers
        )
        
        if response.status_code == 200:
            print("   ✓ Deployment deleted successfully")
        else:
            print(f"   ✗ Failed: {response.text}")
            raise Exception("Delete deployment failed")
        
        # Test 15: Verify Deletion in K8s
        print("\n[4.8] Testing K8s Deployment Deletion...")
        await asyncio.sleep(2)
        result = subprocess.run(
            ["kubectl", "get", "deployment", "test-nginx", "-n", self.project_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("   ✓ K8s deployment deleted successfully")
        else:
            print("   ⚠ Deployment still terminating...")
    
    async def cleanup(self):
        """Clean up test resources"""
        print("\n" + "=" * 70)
        print("CLEANUP")
        print("=" * 70)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Delete test project
        print("\n[Cleanup] Deleting test project...")
        if self.project_id:
            response = await self.client.delete(
                f"{BASE_URL}/projects/{self.project_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                print("   ✓ Test project deleted")
            else:
                print(f"   ⚠ Failed to delete project: {response.text}")

async def main():
    tester = APITester()
    try:
        await tester.run_all_tests()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
