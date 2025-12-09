# Azure Credentials Setup for GitHub Actions

## Option 1: Using Publish Profile (Simpler)

If you want to use the publish profile method (no service principal needed), update the workflow to use:

```yaml
- name: Deploy to Azure Web App
  uses: Azure/webapps-deploy@v3
  with:
    app-name: Pharma
    publish-profile: ${{ secrets.AZUREAPPSERVICE_PUBLISHPROFILE_PHARMA }}
    package: django-postgres-backend
```

**GitHub Secret Required:**
- `AZUREAPPSERVICE_PUBLISHPROFILE_PHARMA` - Download from Azure Portal → App Service "Pharma" → Get publish profile

## Option 2: Using Service Principal (Recommended - More Secure)

The current workflow uses service principal authentication. You need to create an Azure Service Principal and add it as a GitHub secret.

### Steps to Create Service Principal:

1. **Install Azure CLI** (if not already installed)

2. **Login to Azure:**
   ```bash
   az login
   ```

3. **Create Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "github-actions-pharma" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/sites/Pharma --sdk-auth
   ```
   
   Replace:
   - `{subscription-id}` with your Azure subscription ID
   - `{resource-group}` with your resource group name

4. **Copy the JSON output** and add it as a GitHub secret:
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `AZURE_CREDENTIALS`
   - Value: Paste the entire JSON output from step 3

### Example JSON Output:
```json
{
  "clientId": "xxxx-xxxx-xxxx-xxxx",
  "clientSecret": "xxxx-xxxx-xxxx-xxxx",
  "subscriptionId": "xxxx-xxxx-xxxx-xxxx",
  "tenantId": "xxxx-xxxx-xxxx-xxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

## Current Workflow Configuration

The workflow is currently configured to use **Option 2 (Service Principal)**. If you prefer to use **Option 1 (Publish Profile)**, you can:

1. Remove the "Azure Login" step
2. Change the deploy step to use `publish-profile` instead of relying on login

