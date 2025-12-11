#!/bin/bash
# Azure App Service build script
# This script runs during build time (before startup.sh)

# Install system dependencies for PDF processing
# Note: Azure App Service Linux uses Ubuntu/Debian

# Try to install poppler-utils if possible (required for pdfplumber)
# On Azure App Service, we might need to use apt-get if available
# However, Azure App Service build environment may not allow apt-get
# In that case, this will fail gracefully and we'll handle it in code

echo "Checking for poppler-utils..."
if command -v apt-get &> /dev/null; then
    echo "Installing poppler-utils for PDF processing..."
    apt-get update -qq && apt-get install -y -qq poppler-utils 2>&1 || echo "Could not install poppler-utils (may require sudo or not be available in build environment)"
else
    echo "apt-get not available - skipping poppler-utils installation"
    echo "Note: PDF processing may fail if poppler-utils is not installed in runtime environment"
fi

# Check if tesseract is available (optional for OCR)
if command -v tesseract &> /dev/null; then
    echo "Tesseract OCR is available"
else
    echo "Tesseract OCR not found (optional for PDF OCR functionality)"
fi

echo "Build script completed"

