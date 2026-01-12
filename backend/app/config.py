# Configuration settings for the application
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Database Configuration (PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432  # PostgreSQL default port
    DB_USER: str = "postgres"  # PostgreSQL default user
<<<<<<< HEAD
    DB_PASSWORD: str = "12345"  # Set your PostgreSQL password
=======
    DB_PASSWORD: str = "1234"  # Set your PostgreSQL password
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
    DB_NAME: str = "sevenext"  # PostgreSQL database name


    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "z-q20QXTmbrGNE5F1JJqW9RjBY5iTUiqNJ2sCoicTOY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 
    
    # CORS Configuration
    
    CORS_ORIGINS: list = [      
    "http://13.233.199.134",        # AWS EC2 IP address
    "https://13.233.199.134",           # Production domain
    "https://www.13.233.199.134",       # With www
    "http://13.233.199.134",        # Keep for local development
    "http://localhost:5173",
    "http://localhost:8001",         # Keep for local development
    "http://localhost:3000",         # Frontend dev server
]

    # Password Reset Configuration
    RESET_TOKEN_EXPIRE_MINUTES: int = 30  # Reset link valid for 30 minutes
<<<<<<< HEAD
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for reset link
=======
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for reset link
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
    TWILIO_ACCOUNT_SID: str = "ACd0cb471ec5ff7efa0b36e9b602ee05d5"
    TWILIO_AUTH_TOKEN: str = "bdd0d73e5a28e94f75d62e2991b3401f"
    TWILIO_PHONE_NUMBER: str = "+17578632685"



    
    
    # SendGrid configuration
<<<<<<< HEAD
    SENDGRID_API_KEY: str = "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"
=======
    SENDGRID_API_KEY: str = "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"
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
    SENDGRID_FROM_EMAIL: str = "musicmagician92@outlook.com"  # Change to your verified sender email
    SENDGRID_FROM_NAME: str = "sdrarunvarshan"

    # -----------------------
    # Razorpay Configuration
    # -----------------------
    RAZORPAY_KEY_ID: str = "rzp_test_RsbvNk5QaP0H82"
    RAZORPAY_KEY_SECRET: str = "GUaTY0kewJ3nQ1UaE7hU2GAr"
    RAZORPAY_WEBHOOK_SECRET: str = "rdksbfbo8ha438heudjf328489y7"

    # -----------------------
    # Delhivery Webhook Security
    # -----------------------
    # IMPORTANT: Get this secret from Delhivery support or generate a strong random string
    # This is used to verify webhook signatures and prevent unauthorized requests
<<<<<<< HEAD
    DELHIVERY_WEBHOOK_SECRET: str = "your-delhivery-webhook-secret-change-in-production"
    
    # Optional: Enable/disable webhook signature verification
    # Set to False only for testing, MUST be True in production
    WEBHOOK_SIGNATURE_VERIFICATION_ENABLED: bool = True
=======
    DELHIVERY_WEBHOOK_SECRET: str = "test-webhook-secret-12345"  # Change in production
    
    # Webhook signature verification
    # ⚠️ TESTING MODE: Set to False to allow testing without signature
    # 🔒 PRODUCTION: MUST set to True for security
    WEBHOOK_SIGNATURE_VERIFICATION_ENABLED: bool = False  # Set True in production
    
    # Allowed IPs for webhook (Delhivery's IPs)
    # Leave empty to allow all IPs (only safe if signature verification is enabled)
    WEBHOOK_ALLOWED_IPS: list = []  # Add Delhivery IPs in production
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7


    
    # -----------------------
    # Pydantic Config
    # -----------------------
    class Config:
        env_file = ".env"
        case_sensitive = True
        # FIX: Allow extra variables from .env to prevent crashes
        extra = "allow" 
    
    

settings = Settings()

   