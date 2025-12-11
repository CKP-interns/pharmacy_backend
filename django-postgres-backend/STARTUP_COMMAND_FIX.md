# Fix: ModuleNotFoundError: No module named 'config'

## Problem
Azure is using the startup command: `gunicorn config.wsgi` but your project uses `pharmacy_backend.wsgi`.

## Solution: Set Startup Command in Azure Portal

You need to manually set the startup command in Azure Portal:

1. Go to **Azure Portal** → **App Service "Pharma"**
2. Navigate to **Configuration** → **General settings**
3. Find **Startup Command** field
4. Set it to:
   ```
   gunicorn pharmacy_backend.wsgi --bind=0.0.0.0 --timeout 600
   ```
5. Click **Save**
6. The app will restart automatically

## Alternative: Using Azure CLI

If you have Azure CLI installed and are logged in:

```bash
az webapp config set --name Pharma --resource-group <your-resource-group> --startup-file "gunicorn pharmacy_backend.wsgi --bind=0.0.0.0 --timeout 600"
```

Replace `<your-resource-group>` with your actual resource group name.

## Why This Happens

Azure App Service auto-detects Django apps and may use an incorrect module name if it finds old configuration or if the project structure was changed from `config` to `pharmacy_backend`.

## Verification

After setting the startup command, check the logs to confirm it's using the correct command:
- Azure Portal → App Service "Pharma" → Log stream
- You should see: `gunicorn pharmacy_backend.wsgi --bind=0.0.0.0 --timeout 600`

