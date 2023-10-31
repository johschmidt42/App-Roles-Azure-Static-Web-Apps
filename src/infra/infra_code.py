#!/usr/bin/env python
import json
from pathlib import Path

from azapi.provider import AzapiProvider
from azapi.resource_action import ResourceAction
from cdktf import App, AzurermBackend, TerraformStack
from cdktf_cdktf_provider_azuread.application import (
    Application,
    ApplicationAppRole,
    ApplicationWeb,
)
from cdktf_cdktf_provider_azuread.application_password import ApplicationPassword
from cdktf_cdktf_provider_azuread.provider import AzureadProvider
from cdktf_cdktf_provider_azuread.service_principal import ServicePrincipal
from cdktf_cdktf_provider_azurerm.application_insights import ApplicationInsights
from cdktf_cdktf_provider_azurerm.log_analytics_workspace import LogAnalyticsWorkspace
from cdktf_cdktf_provider_azurerm.provider import (
    AzurermProvider,
    AzurermProviderFeatures,
)
from cdktf_cdktf_provider_azurerm.static_site import StaticSite
from cdktf_cdktf_provider_github.actions_secret import ActionsSecret
from cdktf_cdktf_provider_github.provider import GithubProvider
from constructs import Construct
from infra_config import InfraConfig

root_path: Path = Path(__file__).parent.parent.parent


class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, config: InfraConfig, id_: str):
        super().__init__(scope, id_)
        self.config: InfraConfig = config

        self.setup_providers_and_backend()

        static_site: StaticSite = StaticSite(
            scope=self,
            id_="mystaticsite",
            location=self.config.location,
            name="mystaticsite",
            resource_group_name=self.config.resource_group_name,
            sku_tier="Standard",
            sku_size="Standard",
        )

        spa_domain: str = static_site.default_host_name

        """
        Log analytics workspace and app insights enable logging your applications state
        """
        self.log_analytics_workspace: LogAnalyticsWorkspace = LogAnalyticsWorkspace(
            scope=self,
            id_="log_analytics_ws",
            name="logAnalyticsWs",
            resource_group_name=self.config.resource_group_name,
            location=self.config.location,
            sku="PerGB2018",
        )

        self.app_insights: ApplicationInsights = ApplicationInsights(
            scope=self,
            id_="app_insights",
            name="app_insights",
            resource_group_name=self.config.resource_group_name,
            location=self.config.location,
            application_type="web",
            workspace_id=self.log_analytics_workspace.id,
            retention_in_days=30,
        )

        """
        App registration is configured to redirect back to static web app successful after authentication
        Application app roles are created that can later be assigned to users. Its ids can be chosen randomly.
        """
        aad_application: Application = Application(
            scope=self,
            id_="spa_aad_app_johannes",
            display_name="spa_aad_app_johannes",
            web=ApplicationWeb(
                redirect_uris=[f"https://{spa_domain}/.auth/login/aad/callback"],
                implicit_grant={
                    "access_token_issuance_enabled": True,
                    "id_token_issuance_enabled": True,
                },
            ),
            # id is randomly generated uuid
            app_role=[
                ApplicationAppRole(
                    display_name="admin",
                    description="admin",
                    allowed_member_types=["User", "Application"],
                    value="admin",
                    id="4cfc4dae-8aa4-4d60-af72-d8e6df9606d7",
                ),
                ApplicationAppRole(
                    display_name="user",
                    description="user",
                    allowed_member_types=["User", "Application"],
                    value="user",
                    id="d1154158-67e1-458c-bc32-6c5290dc6b0d",
                ),
            ],
            depends_on=[static_site],
        )

        # client_secret creation for app registration
        aad_application_pw: ApplicationPassword = ApplicationPassword(
            scope=self,
            id_="application_pw",
            application_object_id=aad_application.object_id,
            display_name="app pw",
        )

        # Creation of Service principal / entrerprise application entry
        # without the tags, there would not be an entry in enterprise application
        # this shows that it is possible to create a service principal without enterprise application entry
        sp = ServicePrincipal(
            scope=self,
            id_="service_principal",
            application_id=aad_application.application_id,
            app_role_assignment_required=True,
            tags=[
                "AppServiceIntegratedApp",
                "WindowsAzureActiveDirectoryIntegratedApp",
            ],
        )

        # for configuring application settings of static web app,
        # we need the 'azapi' provider
        # noqa: E501 https://stackoverflow.com/questions/70081845/azure-static-web-app-application-settings-using-terraform
        ResourceAction(
            scope=self,
            id_="spa_application_settings",
            type="Microsoft.Web/staticSites/config@2022-03-01",
            resource_id=f"{static_site.id}/config/appsettings",
            method="PUT",
            body=json.dumps(
                {
                    "properties": {
                        "AZURE_CLIENT_ID": sp.application_id,
                        "AZURE_CLIENT_SECRET": aad_application_pw.value,
                        "APPLICATIONINSIGHTS_CONNECTION_STRING": self.app_insights.connection_string,  # noqa: E501
                    },
                    "kind": "appsettings",
                }
            ),
        )

        self.setup_github(
            api_key=static_site.api_key,
        )

    def setup_providers_and_backend(self):
        # remote azure backend
        AzurermBackend(
            scope=self,
            subscription_id=self.config.arm_subscription_id,
            tenant_id=self.config.arm_tenant_id,
            resource_group_name=self.config.resource_group_name,
            storage_account_name=self.config.backend_storage_account_name,
            container_name=self.config.backend_storage_container_name,
            key=self.config.backend_storage_key,
            client_id=self.config.terraform_arm_client_id,
            client_secret=self.config.terraform_arm_client_secret,
        )
        # "normal" azure provider for most of the resources
        AzurermProvider(
            scope=self,
            id="azurerm_provider",
            client_id=self.config.terraform_arm_client_id,
            client_secret=self.config.terraform_arm_client_secret,
            features=AzurermProviderFeatures(),
            subscription_id=self.config.arm_subscription_id,
            tenant_id=self.config.arm_tenant_id,
            skip_provider_registration=True,
        )

        # Active directory specific resources need 
        # a different resource provider
        AzureadProvider(
            scope=self,
            id="spa_azuread_provider",
            client_id=self.config.terraform_arm_client_id,
            client_secret=self.config.terraform_arm_client_secret,
            tenant_id=self.config.arm_tenant_id,
        )

        # App registration configuration can currently only be done by
        # az api provider
        AzapiProvider(
            scope=self,
            id="spa_azapi_provider",
            client_id=self.config.terraform_arm_client_id,
            client_secret=self.config.terraform_arm_client_secret,
            tenant_id=self.config.arm_tenant_id,
            subscription_id=self.config.arm_subscription_id,
        )

        # github provider is needed for connecting azure webapp with github codebase
        # for automatic cicd pipeline
        GithubProvider(scope=self, id="github_provider", token=self.config.github_token)

    def setup_github(self, api_key: str):

        # github is connected to azure static site by the AZURE_STATIC_WEB_APP_API_TOKEN
        # which is used to authorize github when deploying code changes to azure
        # it needs to be in github.secrets and is used in the cicd pipeline
        ActionsSecret(
            scope=self,
            id_="github_actions_secret",
            repository=self.config.github_repo_name,
            secret_name="AZURE_STATIC_WEB_APP_API_TOKEN",
            plaintext_value=api_key,
        )


if __name__ == "__main__":
    config: InfraConfig = InfraConfig()

    app: App = App()
    InfraStack(app, config=config, id_="spa-infra")

    app.synth()
