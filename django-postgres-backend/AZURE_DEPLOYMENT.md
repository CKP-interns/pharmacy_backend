# Azure Deployment - System Dependencies

## PDF/CSV Import Issues on Azure

The supplier import functionality requires system-level dependencies that may not be installed on Azure App Service by default.

### Required System Packages

1. **poppler-utils** - Required for PDF processing (pdfplumber library)
2. **tesseract-ocr** - Optional, for OCR functionality in PDFs

### Solution Options

#### Option 1: Use Azure App Service Extension (Recommended)

Azure App Service Linux supports installing system packages via SSH or startup commands, but you need elevated permissions.

1. Go to Azure Portal → Your App Service → Configuration
2. Under "General settings", enable "Always On" if not already enabled
3. Add a startup command or use SSH to install packages:

```bash
apt-get update && apt-get install -y poppler-utils tesseract-ocr
```

#### Option 2: Use Custom Docker Image

If you have a custom Dockerfile, add these to your Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
```

#### Option 3: Use Azure App Service SSH

1. Enable SSH in Azure Portal (Configuration → General settings → SSH)
2. Connect via SSH: `az webapp ssh --resource-group <rg> --name <app-name>`
3. Install packages:
   ```bash
   sudo apt-get update
   sudo apt-get install -y poppler-utils tesseract-ocr
   ```

### Verifying Installation

After deployment, check the logs for:
- "poppler-utils is available" (success)
- "pdftoppm not found" (needs installation)

### Error Messages

If PDF import fails, you'll see:
- "PDF processing requires poppler-utils system package"
- Clear instructions in the error message

### Alternative: Use CSV Format

If PDF processing cannot be configured, users can use CSV format for imports, which doesn't require system dependencies.

