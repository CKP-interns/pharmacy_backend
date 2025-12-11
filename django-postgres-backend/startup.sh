#!/bin/bash
# Azure App Service startup script for Django
cd /home/site/wwwroot

# Try to install system dependencies if not already present
# Note: Azure App Service may have restrictions on installing system packages
# This will fail gracefully if permissions are not available

# Check and install poppler-utils if missing (required for pdfplumber)
if ! command -v pdftoppm &> /dev/null; then
    echo "pdftoppm not found, attempting to install poppler-utils..."
    if command -v apt-get &> /dev/null; then
        apt-get update -qq && apt-get install -y -qq poppler-utils 2>&1 || echo "Could not install poppler-utils (may require elevated permissions)"
    else
        echo "apt-get not available - PDF processing may not work without poppler-utils"
    fi
else
    echo "poppler-utils is available"
fi

# Start gunicorn
gunicorn pharmacy_backend.wsgi --bind=0.0.0.0 --timeout 600

