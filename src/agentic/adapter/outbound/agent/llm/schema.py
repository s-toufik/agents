from pydantic import BaseModel, SecretStr


class ModelConnector(BaseModel):
    base_url: str
    api_key: SecretStr | None


class ModelParameters(BaseModel):
    model_name: str
    max_tokens: int
    temperature: float
