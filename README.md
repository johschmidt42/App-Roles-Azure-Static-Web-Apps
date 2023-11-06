# Azure Static Web App (Frontend + Backend)

- **Frontend**: React
- **Backend**: Managed Azure Functions (Python)
- **Authentication**: Custom authentication provider with Azure AD
- **Authorization**: Role-based access control (RBAC) with Azure AD App Roles

## Backend versions

- **[backend_v1](src%2Fbackend_v1)
  **: [v1 programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-configuration)
- **[backend_v2](src%2Fbackend_v2)
  **: [v2 programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators)
- **[backend_v2_fastapi](src%2Fbackend_v2_fastapi)
  **: [v2 programming model with FastAPI](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators#web-frameworks) (
  currently not working, see [this issue](https://github.com/Azure/azure-functions-python-worker/issues/1310))

## Infrastructure for Azure SPA

### Installation

1. Install terraform and cdktf cli,
   follow [here](https://developer.hashicorp.com/terraform/tutorials/cdktf/cdktf-install)
2. `pip install -r requirements-infra.txt`
3. run `cdktf provider add azure/azapi` followed by `cdktf get`. This is necessary as the azapi provider itself is not
   yet published to pypi and needs to be retrieved via terraform binding mechanism (
   see [here](https://discuss.hashicorp.com/t/is-it-already-possible-to-use-azapi-in-cdktf/43706) for more information).
   For that, the cdktf-cli (installed by npm) and the cdktf python package need to have the same version
4. Create an azure service principal for infrastructure deployment
5. Create a resource group in azure and grant the service principal contributor rights to it (the SP will be used by
   terraform and needs contributor rights for resource creation / management)
6. create storage account and container within resource group (this will be used as remote backend for the terraform
   providers)
7. Create
   a [PAT in GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token).
   This allows Terraform to access your GitHub repository
8. Run `cp .env-infra.example .env-infra` and fill all the configuration of `.env-infra` with data of steps from 3-6
9. Deploy with `cdktf apply`

### Further manual steps

- You need to add two secrets to your github repository. Go to your GitHub repository -> Settings -> Secrets and Variables -> Actions and click on `new repository secret`. Name it `ARM_TENANT_ID` and enter the tenant uuid here. 

# Azure B2C Tenant Documentation

## Authentication

Authentication is done by creating a user flow in the b2c tenant. This user flow is then referenced in `staticwebapp.config.json` as a part of the login url. An alternative to user flow (that offer solutions for the most common scenarios as login, registration, user edit, ...), [custom policies](https://learn.microsoft.com/en-us/azure/active-directory-b2c/custom-policy-overview) can be used.

It is shown [here](https://learn.microsoft.com/en-us/azure/active-directory-b2c/user-flow-custom-attributes?pivots=b2c-user-flow) how to add custom claim attributes. The datatypes can be of type string, boolean or integer. These custom attributes can also be created and managed via Graph API.

## Access Control

Users that registered to the b2c tenant by the login/signup flow are shown in Entra ID users tab. Although they appear to be full users and can also log into the portal (with read-only and a very short ttl token) with the url `https://portal.azure.com/{b2c-tenant-name}.onmicrosoft.com`, these users are classified as consumer users and can only use the tenant for authorization. They have no possibility to access resources. Read [here](https://learn.microsoft.com/en-us/azure/active-directory-b2c/user-overview#consumer-user) for more. If you go to entra id -> users, you see all consumer users (they have source set to Azure Active Directory) and admin / guest users (with source External Active Directory). That being said, the tenant settings for users (found under entra id -> user settings) do not apply to consumer users.

## Role Management

Out of the box, Azure B2C tenants don't support app roles, but you can write them into the manifest. This was mentioned [here](https://learn.microsoft.com/en-us/answers/questions/799654/assign-app-roles-to-ad-users-in-ad-b2c). Although, after exploration and finding [this](https://learn.microsoft.com/en-us/answers/questions/947710/create-app-roles-in-app-registration-and-assign-th), the app roles do not seem to affect / target the consumer users of the user flows. App roles seems not to be the tool of choice for access control in Azure B2C.

### 1. Solution: managed azure function
An alternative is described [here](https://www.youtube.com/watch?v=C9qN6QqnxQ8&ab_channel=SSWTV%7CVideosfordevelopers%2Cbydevelopers). By creating custom policies, the app returns a role claim attribute that is filled with data by an azure function. 


### 2. Solution: Azure Graph API
Furthermore, use the Microsoft Graph API to set the value of a custom claim to specific roles: [here](https://clintmcmahon.com/add-role-claims-to-an-azure-b2c-user-flow-access-token/).


## 3. Solution
Use the GetRoles endpoint in the backend. The GetRoles endpoints gets user id information as well as tenant and can ask the microsoft API in which groups the user is present. Example mapping:  "Set the role to admin if user is in Admin group". This is similar to this one: [click](https://learn.microsoft.com/en-us/azure/static-web-apps/assign-roles-microsoft-graph)


## Add Github Oauth Identity Provider
[full link](https://learn.microsoft.com/en-us/azure/active-directory-b2c/identity-provider-github?pivots=b2c-user-flow)

1. Create app registration within your github account [here](https://github.com/settings/developers). For callback url, use `https://your-tenant-name.b2clogin.com/your-tenant-name.onmicrosoft.com/oauth2/authresp`. Save the `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`.
2. Go to Azure B2C -> Identity Provider -> Github -> create with the client id and secret.
3. Create new user flow or edit existing user flow and incorporate github as identity provider

## Add Microsoft personal account identity provider [here](https://learn.microsoft.com/en-us/azure/active-directory-b2c/identity-provider-microsoft-account?pivots=b2c-user-flow)

1. Create new app registration (entra id -> app registrations -> specify personal (and others) under supported account types)
2. create client secret and copy id, secret
3. specify same redirect uri (for type web) as in github

## Add Google Identity Provider

1. go to [google developer console](https://console.developers.google.com/)
2. create or select project (you need one)
3. select api & services on the left side
4. credentials -> create credentials -> oauth client id (with application type web)
5. for redirect uri, enter same url as for github and save client id and client secret.

##### Custom Claims Creation

Go to your Azure B2C tenant -> User Attributes -> Add

##### Custom Claims Usage

Go to your user flow -> Check new attributes

#### Infra Code

Creating a B2C tenant with a service principal is not possible with service principal credentials ([here](https://learn.microsoft.com/en-us/answers/questions/1298957/can-you-create-an-azure-b2c-tenant-with-a-service)). Furthermore, many resources like [user flows](https://github.com/hashicorp/terraform-provider-azuread/issues/175) are currently not supported by terrform az providers.

# todo:

- [x] infra code
- [x] b2c tenant settings ([here](https://learn.microsoft.com/en-us/entra/fundamentals/users-default-permissions#restrict-member-users-default-permissions))
- [x] google identity provider
- [x] microsoft identity provider
- [x] custom policies ([here](https://learn.microsoft.com/en-us/azure/active-directory-b2c/custom-policy-overview))
- [ ] access control in b2c([here](https://learn.microsoft.com/en-us/azure/active-directory-b2c/manage-user-access))
- [ ] lifecycle control ([here](https://learn.microsoft.com/en-us/entra/id-governance/lifecycle-workflows-deployment))
- [x] custom claims
- [x] github identity provider
