from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #Lee variables de entorno, y si existe, un arichivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    data_file: str = "data/offers.json"
    cv_file: str = "data/cv.txt"

settings = Settings()