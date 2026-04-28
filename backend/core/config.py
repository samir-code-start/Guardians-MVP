from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_PROJECT_ID: str = ""
    GCP_PROJECT_ID: str = ""
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_AI_INDEX_ENDPOINT_ID: str = ""
    VERTEX_AI_DEPLOYED_INDEX_ID: str = ""
    FIREBASE_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Optional defaults for local dev API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
