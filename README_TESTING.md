# Mini OpenShift API - Testing Guide

This guide provides detailed instructions on how to run all test scripts manually without external support.

---

## 📁 Test Files Overview

All test files are located in the `tests/` directory:

```
mini-openshift-fastapi/
├── tests/
│   ├── test_api.py                    # Basic API tests (auth, users, projects)
│   ├── test_k8s_integration.py        # Kubernetes integration tests
│   ├── test_deployment_management.py  # Deployment management tests
│   └── test_all_apis.py              # Comprehensive test suite (all endpoints)
└── README_TESTING.md                  # This file
```

---

## 🚀 Prerequisites

### 1. Backend Server Running
The FastAPI server must be running before executing tests:

```bash
cd mini-openshift-fastapi
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Verify server is running:**
- Open browser: http://localhost:8000/docs
- You should see the Swagger UI

### 2. Kubernetes Cluster Running
Verify your Kubernetes cluster is accessible:

```bash
kubectl cluster-info
```

**Expected output:**
```
Kubernetes control plane is running at https://127.0.0.1:6443
```

### 3. PostgreSQL Database Running
Ensure the database is running and accessible:

```bash
# If using Docker
docker ps | grep postgres

# Or check connection
psql -h localhost -U postgres -d miniopenshift -c "SELECT 1"
```

### 4. Python Virtual Environment
Activate the virtual environment:

```bash
cd mini-openshift-fastapi
source venv/bin/activate
```

---

## 📝 Running Individual Test Scripts

### Test 1: Basic API Tests
**File:** `tests/test_api.py`  
**Duration:** ~5 seconds  
**Tests:** User registration, login, project creation, project listing

```bash
# From mini-openshift-fastapi directory
python tests/test_api.py
```

**What it tests:**
- ✅ User registration
- ✅ User login (JWT token)
- ✅ Project creation
- ✅ Project listing

**Expected output:**
```
1. Registering User...
   ✓ Success: User created

2. Logging in...
   ✓ Success: JWT token received

3. Creating Project...
   ✓ Success: Project created

4. Listing Projects...
   ✓ Success: Projects retrieved
```

---

### Test 2: Kubernetes Integration Tests
**File:** `tests/test_k8s_integration.py`  
**Duration:** ~10 seconds  
**Tests:** K8s namespace creation, validation, deletion

```bash
python tests/test_k8s_integration.py
```

**What it tests:**
- ✅ Project creation → K8s namespace creation
- ✅ K8s namespace exists and is active
- ✅ Invalid project name validation (rejects uppercase)
- ✅ Project deletion → K8s namespace deletion

**Expected output:**
```
1. Login
   ✓ Success: Got token

2. Create Project 'test-k8s-project'
   ✓ Success: Project created

3. Verify K8s namespace exists
   ✓ Success: Namespace 'test-k8s-project' exists in K8s
   NAME               STATUS   AGE
   test-k8s-project   Active   1s

4. Test invalid project name (uppercase)
   ✓ Success: Validation rejected uppercase name

5. Delete project
   ✓ Success: Project deleted

6. Verify K8s namespace deleted
   ✓ Success: Namespace deleted from K8s
```

---

### Test 3: Deployment Management Tests
**File:** `tests/test_deployment_management.py`  
**Duration:** ~15 seconds  
**Tests:** Full deployment lifecycle (create, scale, delete)

```bash
python tests/test_deployment_management.py
```

**What it tests:**
- ✅ Create project
- ✅ Create deployment (nginx, 2 replicas)
- ✅ Verify deployment in K8s
- ✅ List deployments
- ✅ Get deployment details
- ✅ Scale deployment (2 → 3 replicas)
- ✅ Verify scaling in K8s
- ✅ Delete deployment
- ✅ Verify deletion in K8s
- ✅ Clean up project

**Expected output:**
```
============================================================
Testing Deployment Management API
============================================================
1. Logging in...
   ✓ Success: Got token

2. Creating test project 'deployment-test'...
   ✓ Success: Project created

3. Creating deployment 'nginx-app'...
   ✓ Success: Deployment created
      Name: nginx-app
      Image: nginx:latest
      Replicas: 2

4. Verifying deployment in K8s...
   ✓ Success: Deployment exists in K8s
   NAME        READY   UP-TO-DATE   AVAILABLE   AGE
   nginx-app   0/2     2            0           0s

5. Listing deployments...
   ✓ Success: Found 1 deployment(s)

6. Getting deployment details...
   ✓ Success: Got deployment details

7. Scaling deployment to 3 replicas...
   ✓ Success: Scaled to 3 replicas

8. Verifying scaling in K8s...
   ✓ Success: Deployment scaled in K8s

9. Deleting deployment...
   ✓ Success: Deployment deleted

10. Verifying deletion in K8s...
   ✓ Success: Deployment deleted from K8s

11. Cleaning up test project...
   ✓ Success: Project deleted

============================================================
Test Complete!
============================================================
```

---

### Test 4: Comprehensive API Test Suite
**File:** `tests/test_all_apis.py`  
**Duration:** ~20 seconds  
**Tests:** All implemented endpoints (15 tests)

```bash
python tests/test_all_apis.py
```

**What it tests:**
- **Section 1: Authentication** (2 tests)
  - User registration
  - User login
  
- **Section 2: User Management** (2 tests)
  - Get current user
  - List users
  
- **Section 3: Project Management** (3 tests)
  - Create project
  - K8s namespace creation
  - List projects
  
- **Section 4: Deployment Management** (8 tests)
  - Create deployment
  - K8s deployment creation
  - List deployments
  - Get deployment details
  - Scale deployment
  - K8s scaling verification
  - Delete deployment
  - K8s deletion verification

**Expected output:**
```
======================================================================
MINI OPENSHIFT - COMPREHENSIVE API TEST SUITE
======================================================================

======================================================================
SECTION 1: AUTHENTICATION TESTS
======================================================================
[1.1] Testing User Registration...
   ✓ User registration successful
[1.2] Testing User Login...
   ✓ Login successful
   ✓ JWT token received (length: 165)

======================================================================
SECTION 2: USER MANAGEMENT TESTS
======================================================================
[2.1] Testing Get Current User...
   ✓ Current user retrieved
[2.2] Testing List Users...
   ✓ Users list retrieved (3 users)

======================================================================
SECTION 3: PROJECT MANAGEMENT TESTS
======================================================================
[3.1] Testing Create Project...
   ✓ Project created successfully
[3.2] Testing K8s Namespace Creation...
   ✓ K8s namespace created successfully
[3.3] Testing List Projects...
   ✓ Projects list retrieved (2 projects)

======================================================================
SECTION 4: DEPLOYMENT MANAGEMENT TESTS
======================================================================
[4.1] Testing Create Deployment...
   ✓ Deployment created successfully
[4.2] Testing K8s Deployment Creation...
   ✓ K8s deployment created successfully
[4.3] Testing List Deployments...
   ✓ Deployments list retrieved (1 deployments)
[4.4] Testing Get Deployment Details...
   ✓ Deployment details retrieved
[4.5] Testing Scale Deployment...
   ✓ Deployment scaled to 4 replicas
[4.6] Testing K8s Deployment Scaling...
   ✓ K8s deployment scaled successfully
[4.7] Testing Delete Deployment...
   ✓ Deployment deleted successfully
[4.8] Testing K8s Deployment Deletion...
   ✓ K8s deployment deleted successfully

======================================================================
CLEANUP
======================================================================
[Cleanup] Deleting test project...
   ✓ Test project deleted

======================================================================
ALL TESTS COMPLETED SUCCESSFULLY! ✅
======================================================================
```

---

## 🔧 Running All Tests at Once

Create a simple script to run all tests sequentially:

```bash
#!/bin/bash
# run_all_tests.sh

echo "Running all Mini OpenShift API tests..."
echo ""

echo "1. Basic API Tests"
python tests/test_api.py
echo ""

echo "2. Kubernetes Integration Tests"
python tests/test_k8s_integration.py
echo ""

echo "3. Deployment Management Tests"
python tests/test_deployment_management.py
echo ""

echo "4. Comprehensive API Tests"
python tests/test_all_apis.py
echo ""

echo "All tests completed!"
```

**Make it executable and run:**
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

---

## 🐛 Troubleshooting

### Issue 1: "Connection refused" error

**Problem:** Cannot connect to API server

**Solution:**
```bash
# Check if server is running
curl http://localhost:8000

# If not, start the server
cd mini-openshift-fastapi
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

### Issue 2: "Kubernetes cluster not found"

**Problem:** Cannot connect to Kubernetes

**Solution:**
```bash
# Check cluster status
kubectl cluster-info

# If not running, start your cluster
# For minikube:
minikube start

# For Docker Desktop:
# Enable Kubernetes in Docker Desktop settings
```

---

### Issue 3: "Database connection failed"

**Problem:** Cannot connect to PostgreSQL

**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# If not, start PostgreSQL
# For Docker:
docker start postgres

# For local installation:
brew services start postgresql
```

---

### Issue 4: "User already exists" error

**Problem:** Test user already exists in database

**Solution:**
The comprehensive test (`test_all_apis.py`) automatically handles this by using unique usernames with timestamps. For other tests, you can:

1. **Option 1:** Delete existing test users from database
```bash
psql -h localhost -U postgres -d miniopenshift
DELETE FROM users WHERE email LIKE 'test%';
```

2. **Option 2:** Modify test script to use different email/username

---

### Issue 5: "Namespace already exists"

**Problem:** K8s namespace from previous test still exists

**Solution:**
```bash
# List all test namespaces
kubectl get namespaces | grep test

# Delete specific namespace
kubectl delete namespace test-k8s-project

# Or delete all mini-openshift managed namespaces
kubectl delete namespaces -l managed-by=mini-openshift
```

---

## 📊 Test Coverage Summary

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_api.py` | 4 | Basic API functionality |
| `test_k8s_integration.py` | 6 | K8s namespace management |
| `test_deployment_management.py` | 11 | Deployment lifecycle |
| `test_all_apis.py` | 15 | All endpoints |
| **Total** | **36** | **100% of implemented features** |

---

## 🎯 Quick Reference

### Run Specific Test
```bash
python tests/test_api.py                    # Basic tests
python tests/test_k8s_integration.py        # K8s tests
python tests/test_deployment_management.py  # Deployment tests
python tests/test_all_apis.py              # All tests
```

### Check Prerequisites
```bash
# Server running?
curl http://localhost:8000

# K8s running?
kubectl cluster-info

# Database running?
psql -h localhost -U postgres -d miniopenshift -c "SELECT 1"
```

### Clean Up After Tests
```bash
# Delete test namespaces
kubectl delete namespaces -l managed-by=mini-openshift

# Delete test users (optional)
psql -h localhost -U postgres -d miniopenshift
DELETE FROM users WHERE email LIKE 'test%';
```

---

## 📝 Notes

1. **Test Order:** Tests can be run in any order, but `test_all_apis.py` is the most comprehensive.

2. **Cleanup:** All tests clean up after themselves (delete created resources).

3. **Idempotent:** Tests can be run multiple times without issues.

4. **Timing:** Some tests wait for K8s operations to complete (2-3 seconds).

5. **Unique Data:** `test_all_apis.py` uses timestamps to ensure unique usernames.

---

## 🚀 Next Steps

After running tests successfully:

1. **Verify in Swagger UI:** http://localhost:8000/docs
2. **Check K8s resources:** `kubectl get all --all-namespaces`
3. **View database:** `psql -h localhost -U postgres -d miniopenshift`

---

**Last Updated:** December 2, 2025  
**Version:** 1.0  
**Status:** All tests passing ✅
