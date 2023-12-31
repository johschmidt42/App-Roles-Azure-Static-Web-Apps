# Role Based Access Control (RBAC) in Azure Static Web Apps (SWA)

Build a secure web app with Azure SWA and Azure Active Directory App Roles

![app.gif](app.gif)

## Overview

- **Frontend**: React
- **Backend**: Managed Azure Functions (Python)
- **Authentication**: Custom authentication provider with Azure AD
- **Authorization**: Role-based access control (RBAC) with Azure AD App Roles

## Installation

### Manual deployment

Create an Azure Static Web App.

![create_swa.png](create_swa.png)

Follow the steps in the blog post.

### Automatic deployment with Infrastructure as Code (IaC)

#### Installation

1. Install terraform and cdktf cli,
   follow [here](https://developer.hashicorp.com/terraform/tutorials/cdktf/cdktf-install)
2. `pip install -r requirements-infra.txt`
3. run `cdktf provider add azure/azapi` followed by `cdktf get`. This is necessary as the azapi provider itself is not
   yet published to pypi and needs to be retrieved via the terraform binding mechanism (
   see [here](https://discuss.hashicorp.com/t/is-it-already-possible-to-use-azapi-in-cdktf/43706) for more information).
   For that, the cdktf-cli (installed by npm) and the cdktf python package need to have the same version
4. Create an azure service principal for infrastructure deployment
5. Create a resource group in azure and grant the service principal contributor rights to it (the SP will be used by
   terraform and needs contributor rights for resource creation/management)
6. Create a storage account and container within the resource group (this will be used as the remote backend for the
   terraform state)
7. Create
   a [PAT in GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token).
   This allows Terraform to access your GitHub repository
8. Run `cp .env-infra.example .env-infra` and fill all the configuration of `.env-infra` with data of steps from 3-6
9. Deploy with `cdktf apply`

#### Further manual steps

You need to add two secrets to your GitHub repository:
Go to your GitHub repository -> Settings -> Secrets and Variables -> Actions and click on `new repository secret`. Name
it `ARM_TENANT_ID` and enter the tenant uuid here.

## Backend versions

- [backend_v1](src%2Fbackend_v1): [v1 programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-configuration)
- [backend_v2](src%2Fbackend_v2): [v2 programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators)
- [backend_v2_fastapi](src%2Fbackend_v2_fastapi): [v2 programming model with FastAPI](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators#web-frameworks)
  (currently not working, see [this issue](https://github.com/Azure/azure-functions-python-worker/issues/1310))
