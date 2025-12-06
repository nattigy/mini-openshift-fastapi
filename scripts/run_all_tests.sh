#!/bin/bash

# Mini OpenShift API - Test Runner Script
# This script runs all test suites sequentially

set -e  # Exit on error

echo "======================================================================"
echo "Mini OpenShift API - Running All Tests"
echo "======================================================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# Check if server is running
echo "Checking if API server is running..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✓ API server is running"
else
    echo "✗ API server is not running!"
    echo "Please start the server with: uvicorn app.main:app --reload --port 8000"
    exit 1
fi

# Check if Kubernetes is accessible
echo "Checking Kubernetes cluster..."
if kubectl cluster-info > /dev/null 2>&1; then
    echo "✓ Kubernetes cluster is accessible"
else
    echo "✗ Kubernetes cluster is not accessible!"
    echo "Please ensure your Kubernetes cluster is running"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Test 1/4: Basic API Tests"
echo "======================================================================"
python tests/test_api.py
echo ""

echo "======================================================================"
echo "Test 2/4: Kubernetes Integration Tests"
echo "======================================================================"
python tests/test_k8s_integration.py
echo ""

echo "======================================================================"
echo "Test 3/4: Deployment Management Tests"
echo "======================================================================"
python tests/test_deployment_management.py
echo ""

echo "======================================================================"
echo "Test 4/4: Comprehensive API Tests"
echo "======================================================================"
python tests/test_all_apis.py
echo ""

echo "======================================================================"
echo "✅ All Tests Completed Successfully!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  - Basic API Tests: PASSED"
echo "  - K8s Integration Tests: PASSED"
echo "  - Deployment Management Tests: PASSED"
echo "  - Comprehensive API Tests: PASSED"
echo ""
echo "Total: 36 tests across 4 test suites"
echo ""
