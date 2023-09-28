#!/usr/bin/env python
import json
import os
from pathlib import Path

from azapi.provider import AzapiProvider
from azapi.resource_action import ResourceAction
from cdktf import App, AzurermBackend, TerraformStack
from cdktf_cdktf_provider_azuread.application import (
    Application,
    ApplicationAppRole,
    ApplicationWeb,
)
from cdktf_cdktf_provider_azuread.application_password import (
    ApplicationPassword,
)
from cdktf_cdktf_provider_azuread.provider import AzureadProvider
from cdktf_cdktf_provider_azuread.service_principal import ServicePrincipal
from cdktf_cdktf_provider_azurerm.provider import (
    AzurermProvider,
    AzurermProviderFeatures,
)
from cdktf_cdktf_provider_azurerm.static_site import StaticSite
from cdktf_cdktf_provider_github.actions_secret import ActionsSecret
from cdktf_cdktf_provider_github.provider import GithubProvider
from cdktf_cdktf_provider_github.repository_file import RepositoryFile
from constructs import Construct

from infra_config import InfraConfig

root_path = Path(__file__).parent.parent.parent


class InfraStack(TerraformStack):
    def __init__(self, scope: Construct, config: InfraConfig, id_: str):
        super().__init__(scope, id_)
        self.config = config

        self.setup_providers_and_backend()

        static_site = StaticSite(
            scope=self,
            id_="mystaticsite",
            location=self.config.location,
            name="mystaticsite",
            resource_group_name=self.config.resource_group_name,
            sku_tier="Standard",
        )

        spa_domain: str = static_site.default_host_name

        aad_app_registration = Application(
            scope=self,
            id_="spa_aad_app_johannes",
            display_name="spa_aad_app_johannes",
            web=ApplicationWeb(
                redirect_uris=[
                    f"https://{spa_domain}/.auth/login/aad/callback"
                ],
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

        aad_application_pw = ApplicationPassword(
            scope=self,
            id_="application_pw",
            application_object_id=aad_app_registration.object_id,
            display_name="app pw",
        )

        # tags for enterprise application because we manage user access roles in enterprise application
        sp = ServicePrincipal(
            scope=self,
            id_="service_principal",
            application_id=aad_app_registration.application_id,
            app_role_assignment_required=True,
            tags=[
                "AppServiceIntegratedApp",
                "WindowsAzureActiveDirectoryIntegratedApp",
            ],
        )

        # for configuring application settings of static web page, we need azapi provider
        # https://stackoverflow.com/questions/70081845/azure-static-web-app-application-settings-using-terraform
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
                    },
                    "kind": "appsettings",
                }
            ),
        )

        # GITHUB COMPONENTS FOR CI/CD Pipeline from linked github repository

        workflow_template_path = (
            root_path / "data" / "github_cicd_template.yaml"
        )

        self.setup_github(
            api_key=static_site.api_key,
            workflow_template_path=workflow_template_path,
        )

    def setup_providers_and_backend(self):
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

        # ad app registration und service principal
        AzureadProvider(
            scope=self,
            id="spa_azuread_provider",
            client_id=self.config.terraform_arm_client_id,
            client_secret=self.config.terraform_arm_client_secret,
            tenant_id=self.config.arm_tenant_id,
        )

        # for editing application settings in static web page
        AzapiProvider(
            scope=self,
            id="spa_azapi_provider",
            client_id=self.config.terraform_arm_client_id,
            client_secret=self.config.terraform_arm_client_secret,
            tenant_id=self.config.arm_tenant_id,
            subscription_id=self.config.arm_subscription_id,
        )

        GithubProvider(
            scope=self, id="github_provider", token=self.config.token_for_github
        )

    def setup_github(self, api_key: str, workflow_template_path: Path):
        file_contents = workflow_template_path.read_text()

        actions_secret = ActionsSecret(
            scope=self,
            id_="github_actions_secret",
            repository=self.config.repo_name_github,
            secret_name="AZURE_STATIC_WEB_APP_API_TOKEN",
            plaintext_value=api_key,
        )

        # commit only when template file changes
        RepositoryFile(
            scope=self,
            id_="github_workflow_file",
            repository=self.config.repo_name_github,
            branch="cicd/infra",  # TODO: remaster to always push to current branch
            file=".github/workflows/azure-static-web-app.yaml",
            content=file_contents,
            commit_message="Add workflow (by terraform)",
            commit_author="Patrick Strasser",
            commit_email="p.strasser@dmesh.io",
            overwrite_on_create=True,
            depends_on=[actions_secret]
        )


if __name__ == "__main__":
    config = InfraConfig()

    app = App()
    InfraStack(app, config=config, id_="spa-infra")

    app.synth()
