# Configuration settings for the application
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Database Configuration (PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432  # PostgreSQL default port
    DB_USER: str = "postgres"  # PostgreSQL default user
    DB_PASSWORD: str = "12345"  # Set your PostgreSQL password
    DB_NAME: str = "sevenext"  # PostgreSQL database name


    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "z-q20QXTmbrGNE5F1JJqW9RjBY5iTUiqNJ2sCoicTOY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 #for token expiry
    
    # CORS Configuration
    
    CORS_ORIGINS: list = [      
    "http://13.233.199.134",        # AWS EC2 IP address
    "https://13.233.199.134",           # Production domain
    "https://www.13.233.199.134",       # With www
    "http://13.233.199.134",        # Keep for local development
    "http://localhost:5173",
    "http://192.168.1.2:3000",
    "http://localhost:3000", 
    "http://localhost:8001",        # Frontend dev server
    "https://sevenxt.in",           # New Production Domain
    "https://www.sevenxt.in"        # New Production Domain WWW
]

    # Password Reset Configuration
    RESET_TOKEN_EXPIRE_MINUTES: int = 30  # Reset link valid for 30 minutes
    FRONTEND_URL: str = "https://localhost:3000"  # Frontend URL for reset link
    TWILIO_ACCOUNT_SID: str = "ACd0cb471ec5ff7efa0b36e9b602ee05d5"
    TWILIO_AUTH_TOKEN: str = "bdd0d73e5a28e94f75d62e2991b3401f"
    TWILIO_PHONE_NUMBER: str = "+17578632685"



    
    
    # SendGrid configuration
    SENDGRID_API_KEY: str = "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"
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
    DELHIVERY_WEBHOOK_SECRET: str = "your-delhivery-webhook-secret-change-in-production"
    
    # Optional: Enable/disable webhook signature verification
    # Set to False only for testing, MUST be True in production
    WEBHOOK_SIGNATURE_VERIFICATION_ENABLED: bool = False  # ⚠️ TESTING MODE - Set to True in production
    
    # Optional: List of allowed IP addresses for webhooks (leave empty to allow all)
    # Example: ["203.192.229.0/24", "52.66.0.0/16"] for Delhivery IPs
    WEBHOOK_ALLOWED_IPS: list = [
        # Production IPs
        # "13.229.195.68", "18.139.238.62", "52.76.70.1", "3.108.106.65",
        # "13.127.20.101", "13.126.12.240", "35.154.161.83", "3.6.106.39", "18.61.175.16",
        # # Staging/Dev IPs
        # "18.136.12.154", "13.250.167.49", "52.220.126.238", "3.109.19.228",
        # "3.7.116.186", "3.6.106.39",
        # # Localhost (for testing)
        # "127.0.0.1", "localhost"
    ]


    
    # -----------------------
    # Pydantic Config
    # -----------------------
    class Config:
        env_file = ".env"
        case_sensitive = True
        # FIX: Allow extra variables from .env to prevent crashes
        extra = "allow" 
    
    

settings = Settings()

   