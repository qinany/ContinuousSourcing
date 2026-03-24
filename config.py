import os

# Flask Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '8080'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Database Configuration
DATABASE_HOST = os.getenv('DATABASE_HOST', '10.0.28.161')
DATABASE_PORT = int(os.getenv('DATABASE_PORT', '80'))
DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'f980f7da-efd3-477d-b84a-c171929c50ea')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'cs1_0_1')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# Task Configuration
TASK_NAME = os.getenv('TASK_NAME', 'data_sourcing_v_5_0')

# Queue Names
QUEUE_PRIORITY_JUDGE = os.getenv('QUEUE_PRIORITY_JUDGE', 'priority_judge')
QUEUE_CATEGORIES = os.getenv('QUEUE_CATEGORIES', 'get_categories')
QUEUE_DATA_VOLUME = os.getenv('QUEUE_DATA_VOLUME', 'data_volume')
QUEUE_QUALITY = os.getenv('QUEUE_QUALITY', 'quality_judgment')
QUEUE_GET_PICTURE = os.getenv('QUEUE_GET_PICTURE', 'get_picture')
QUEUE_GET_SCREENSHOT = os.getenv('QUEUE_GET_SCREENSHOT', 'get_screenshot')
QUEUE_GET_WEBSITE_CONTENT = os.getenv('QUEUE_GET_WEBSITE_CONTENT', 'get_website_info')

# LLM Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# MinIO Configuration (Optional)
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'continuous-sourcing')

# Crawler Configuration
CRAWLER_WORKER_RESTART_INTERVAL = int(os.getenv('CRAWLER_WORKER_RESTART_INTERVAL', '3600'))  # 1 hour
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '5'))

# Class for compatibility
class Settings:
    pass

settings = Settings()
settings.redis_host = REDIS_HOST
settings.redis_port = REDIS_PORT
settings.redis_db = REDIS_DB
settings.database_host = DATABASE_HOST
settings.database_port = DATABASE_PORT
settings.database_user = DATABASE_USER
settings.database_password = DATABASE_PASSWORD
settings.database_name = DATABASE_NAME
settings.task_name = TASK_NAME
settings.openai_api_key = OPENAI_API_KEY
settings.deepseek_api_key = DEEPSEEK_API_KEY
settings.gemini_api_key = GEMINI_API_KEY
settings.minio_endpoint = MINIO_ENDPOINT
settings.minio_access_key = MINIO_ACCESS_KEY
settings.minio_secret_key = MINIO_SECRET_KEY
settings.minio_bucket = MINIO_BUCKET
