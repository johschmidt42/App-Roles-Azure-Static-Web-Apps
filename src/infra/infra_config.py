from pydantic_settings import BaseSettings


class InfraConfig(BaseSettings):
    arm_subscription_id: str
    arm_tenant_id: str
    terraform_arm_client_id: str
    terraform_arm_client_secret: str
    resource_group_name: str
    backend_storage_account_name: str
    backend_storage_container_name: str
    backend_storage_key: str
    github_token: str
    github_repo_name: str
    location: str = "West Europe"

    class Config:
        env_file = ".env-infra"
