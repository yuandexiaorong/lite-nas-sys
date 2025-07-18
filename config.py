"""
配置文件
Configuration file for the embedded lightweight NAS management software.
"""

import os
from datetime import timedelta


class Config:
    """
    基础配置类
    Base configuration class.
    """
    # Flask基础配置 / Flask basic configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_change_in_production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = False
    TESTING = False
    
    # 数据库配置 / Database configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'users.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 会话配置 / Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Docker配置 / Docker configuration
    DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
    DOCKER_TIMEOUT = int(os.environ.get('DOCKER_TIMEOUT', 30))
    
    # 文件管理器配置 / File manager configuration
    FILEBROWSER_PORT = int(os.environ.get('FILEBROWSER_PORT', 8088))
    FILEBROWSER_IMAGE = os.environ.get('FILEBROWSER_IMAGE', 'filebrowser/filebrowser:latest')
    FILEBROWSER_DATA_DIR = os.environ.get('FILEBROWSER_DATA_DIR', '/DATA')
    FILEBROWSER_CONFIG_DIR = os.environ.get('FILEBROWSER_CONFIG_DIR', './filebrowser/config')
    FILEBROWSER_DB_DIR = os.environ.get('FILEBROWSER_DB_DIR', './filebrowser/database')
    
    # 应用配置 / Application configuration
    APP_PORT = int(os.environ.get('APP_PORT', 5000))
    APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
    APP_DEBUG = os.environ.get('APP_DEBUG', 'False').lower() == 'true'
    
    # 日志配置 / Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    LOG_MAX_SIZE = int(os.environ.get('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # 安全配置 / Security configuration
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 12))
    SESSION_PROTECTION = 'strong'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1小时 / 1 hour
    
    # 国际化配置 / Internationalization configuration
    LANGUAGES = ['zh', 'en']
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'zh')
    BABEL_DEFAULT_LOCALE = DEFAULT_LANGUAGE
    BABEL_DEFAULT_TIMEZONE = os.environ.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Shanghai')
    
    # 资源监控配置 / Resource monitoring configuration
    MONITOR_INTERVAL = int(os.environ.get('MONITOR_INTERVAL', 2))  # 秒 / seconds
    MONITOR_ENABLED = os.environ.get('MONITOR_ENABLED', 'True').lower() == 'true'
    
    # 应用商店配置 / App store configuration
    APP_STORE_CONFIG_FILE = os.environ.get('APP_STORE_CONFIG_FILE', 'apps.json')
    APP_STORE_ENABLED = os.environ.get('APP_STORE_ENABLED', 'True').lower() == 'true'
    
    # 备份配置 / Backup configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'False').lower() == 'true'
    BACKUP_DIR = os.environ.get('BACKUP_DIR', './backups')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 7))
    
    # 邮件配置（可选） / Email configuration (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 时区配置 / Timezone configuration
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Shanghai')


class DevelopmentConfig(Config):
    """
    开发环境配置
    Development environment configuration.
    """
    DEBUG = True
    APP_DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境允许HTTP会话
    # Allow HTTP sessions in development
    SESSION_COOKIE_SECURE = False
    
    # 开发环境CSRF保护可以关闭
    # CSRF protection can be disabled in development
    WTF_CSRF_ENABLED = False


class TestingConfig(Config):
    """
    测试环境配置
    Testing environment configuration.
    """
    TESTING = True
    DEBUG = True
    APP_DEBUG = True
    
    # 测试环境使用内存数据库
    # Use in-memory database for testing
    DATABASE_PATH = ':memory:'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 测试环境关闭CSRF保护
    # Disable CSRF protection in testing
    WTF_CSRF_ENABLED = False
    
    # 测试环境使用固定密钥
    # Use fixed secret key for testing
    SECRET_KEY = 'test-secret-key-for-testing-only'


class ProductionConfig(Config):
    """
    生产环境配置
    Production environment configuration.
    """
    DEBUG = False
    APP_DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境必须使用HTTPS
    # HTTPS is required in production
    SESSION_COOKIE_SECURE = True
    
    # 生产环境必须设置强密钥
    # Strong secret key is required in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # 生产环境启用所有安全特性
    # Enable all security features in production
    WTF_CSRF_ENABLED = True
    SESSION_PROTECTION = 'strong'
    
    # 生产环境日志配置
    # Production logging configuration
    LOG_FILE = '/var/log/nas-manager/app.log'
    LOG_MAX_SIZE = 50 * 1024 * 1024  # 50MB
    LOG_BACKUP_COUNT = 10
    
    # 生产环境备份配置
    # Production backup configuration
    BACKUP_ENABLED = True
    BACKUP_DIR = '/var/backups/nas-manager'
    BACKUP_RETENTION_DAYS = 30


class DockerConfig(ProductionConfig):
    """
    Docker环境配置
    Docker environment configuration.
    """
    # Docker环境特定配置
    # Docker-specific configuration
    APP_HOST = '0.0.0.0'
    APP_PORT = 5000
    
    # Docker环境数据目录
    # Docker data directories
    DATABASE_PATH = '/app/data/users.db'
    FILEBROWSER_DATA_DIR = '/app/data'
    FILEBROWSER_CONFIG_DIR = '/app/filebrowser/config'
    FILEBROWSER_DB_DIR = '/app/filebrowser/database'
    
    # Docker环境日志目录
    # Docker log directory
    LOG_FILE = '/app/logs/app.log'
    BACKUP_DIR = '/app/backups'


# 配置映射 / Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    获取当前环境配置
    Get current environment configuration.
    
    Returns:
        Config: 配置对象 / Configuration object
    """
    env = os.environ.get('FLASK_ENV', 'development')
    config_obj = config.get(env, config['default'])
    
    # 验证必需的环境变量
    # Validate required environment variables
    if config_obj.FLASK_ENV == 'production':
        if not config_obj.SECRET_KEY or config_obj.SECRET_KEY == 'your_secret_key_here_change_in_production':
            raise ValueError('SECRET_KEY must be set in production environment')
    
    return config_obj


def validate_config(config_obj):
    """
    验证配置有效性
    Validate configuration validity.
    
    Args:
        config_obj: 配置对象 / Configuration object
        
    Raises:
        ValueError: 配置无效时抛出异常 / Raises exception when configuration is invalid
    """
    # 验证必需的环境变量
    # Validate required environment variables
    if config_obj.FLASK_ENV == 'production':
        if not config_obj.SECRET_KEY or config_obj.SECRET_KEY == 'your_secret_key_here_change_in_production':
            raise ValueError('SECRET_KEY must be set in production environment')
    
    # 验证端口范围
    # Validate port ranges
    if not (1 <= config_obj.APP_PORT <= 65535):
        raise ValueError(f'Invalid APP_PORT: {config_obj.APP_PORT}')
    
    if not (1 <= config_obj.FILEBROWSER_PORT <= 65535):
        raise ValueError(f'Invalid FILEBROWSER_PORT: {config_obj.FILEBROWSER_PORT}')
    
    # 验证密码长度
    # Validate password length
    if config_obj.PASSWORD_MIN_LENGTH < 8:
        raise ValueError(f'PASSWORD_MIN_LENGTH must be at least 8, got: {config_obj.PASSWORD_MIN_LENGTH}')
    
    # 验证监控间隔
    # Validate monitoring interval
    if config_obj.MONITOR_INTERVAL < 1:
        raise ValueError(f'MONITOR_INTERVAL must be at least 1 second, got: {config_obj.MONITOR_INTERVAL}')


# 导出配置 / Export configuration
__all__ = ['Config', 'DevelopmentConfig', 'TestingConfig', 'ProductionConfig', 'DockerConfig', 'get_config', 'validate_config'] 