from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ========================================
    # DATABASE (RENDER READY)
    # ========================================
    DATABASE_URL: str

    # ========================================
    # API CONFIG
    # ========================================
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ========================================
    # CORS CONFIG
    # ========================================
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://sevenxt-dash.onrender.com",
        "https://sevenxt.in",
        "https://www.sevenxt.in",
        "https://your-frontend.vercel.app",
    ]

    # ========================================
    # PASSWORD RESET
    # ========================================
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:3000"

    # ========================================
    # TWILIO
    # ========================================
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ========================================
    # SENDGRID
    # ========================================
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = ""
    SENDGRID_FROM_NAME: str = ""

    # ========================================
    # RAZORPAY
    # ========================================
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ========================================
    # DELHIVERY WEBHOOK
    # ========================================
    DELHIVERY_WEBHOOK_SECRET: str = ""
    WEBHOOK_SIGNATURE_VERIFICATION_ENABLED: bool = False
    WEBHOOK_ALLOWED_IPS: list[str] = []

    # ========================================
    # PYDANTIC CONFIG
    # ========================================
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Global instance
settings = Settings()
