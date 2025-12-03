# Mini OpenShift API - Quick Test Reference

## 🚀 Quick Start

### 1. Start Server
```bash
cd mini-openshift-fastapi
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 2. Run All Tests
```bash
./run_all_tests.sh
```

---

## 📋 Individual Tests

### Basic API Tests (4 tests, ~5s)
```bash
python tests/test_api.py
```
Tests: Registration, Login, Projects

### K8s Integration (6 tests, ~10s)
```bash
python tests/test_k8s_integration.py
```
Tests: Namespace creation/deletion, Validation

### Deployment Management (11 tests, ~15s)
```bash
python tests/test_deployment_management.py
```
Tests: Full deployment lifecycle

### Comprehensive Suite (15 tests, ~20s)
```bash
python tests/test_all_apis.py
```
Tests: All endpoints

---

## ✅ Prerequisites Checklist

- [ ] Server running on port 8000
- [ ] Kubernetes cluster accessible
- [ ] PostgreSQL database running
- [ ] Virtual environment activated

**Quick Check:**
```bash
curl http://localhost:8000           # Server
kubectl cluster-info                 # K8s
psql -h localhost -U postgres -c "SELECT 1"  # DB
```

---

## 🐛 Common Issues

### Server not running
```bash
uvicorn app.main:app --reload --port 8000
```

### K8s not accessible
```bash
kubectl cluster-info
# or
minikube start
```

### Clean up test resources
```bash
kubectl delete namespaces -l managed-by=mini-openshift
```

---

## 📊 Test Summary

| Test File | Tests | Duration |
|-----------|-------|----------|
| test_api.py | 4 | ~5s |
| test_k8s_integration.py | 6 | ~10s |
| test_deployment_management.py | 11 | ~15s |
| test_all_apis.py | 15 | ~20s |
| **Total** | **36** | **~50s** |

---

## 📖 Full Documentation

See [README_TESTING.md](./README_TESTING.md) for complete documentation.
