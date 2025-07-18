# Docker 部署指南

本文档介绍如何使用 Docker 部署嵌入式轻NAS管理软件。

## 🐳 快速部署

### 使用 Docker Compose（推荐）

1. **创建 docker-compose.yml 文件**

```yaml
version: '3.8'

services:
  nas-manager:
    build: .
    container_name: nas-manager
    ports:
      - "5000:5000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your_secret_key_here
      - TZ=Asia/Shanghai
    restart: unless-stopped
    depends_on:
      - filebrowser
    networks:
      - nas-network

  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    ports:
      - "8088:80"
    volumes:
      - ./data:/srv
      - ./filebrowser/config:/config
      - ./filebrowser/database:/database
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    networks:
      - nas-network

networks:
  nas-network:
    driver: bridge

volumes:
  data:
  logs:
```

2. **创建 Dockerfile**

```dockerfile
# 使用官方Python运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# 安装Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/filebrowser/config /app/filebrowser/database

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/resource || exit 1

# 启动命令
CMD ["python", "app.py"]
```

3. **启动服务**

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f nas-manager
```

### 使用 Docker 命令

1. **构建镜像**

```bash
docker build -t nas-manager .
```

2. **运行容器**

```bash
docker run -d \
  --name nas-manager \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your_secret_key_here \
  --restart unless-stopped \
  nas-manager
```

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_ENV` | `development` | Flask环境模式 |
| `SECRET_KEY` | `your_secret_key_here` | Flask密钥（生产环境必须修改） |
| `TZ` | `UTC` | 时区设置 |
| `DOCKER_HOST` | `unix:///var/run/docker.sock` | Docker守护进程地址 |
| `FILEBROWSER_PORT` | `8088` | 文件管理器端口 |
| `DATA_DIR` | `/app/data` | 数据存储目录 |

### 数据卷映射

| 容器路径 | 主机路径 | 说明 |
|----------|----------|------|
| `/var/run/docker.sock` | `/var/run/docker.sock` | Docker套接字（必需） |
| `/app/data` | `./data` | 应用数据目录 |
| `/app/logs` | `./logs` | 日志文件目录 |
| `/srv` | `./data` | 文件管理器数据目录 |
| `/config` | `./filebrowser/config` | 文件管理器配置 |
| `/database` | `./filebrowser/database` | 文件管理器数据库 |

## 🚀 生产环境部署

### 1. 安全配置

```bash
# 生成强密钥
openssl rand -hex 32

# 创建环境变量文件
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=your_generated_secret_key_here
TZ=Asia/Shanghai
EOF
```

### 2. 反向代理配置（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # 主应用
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 文件管理器
    location /filemanager/ {
        proxy_pass http://localhost:8088/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 使用 Docker Compose 生产配置

```yaml
version: '3.8'

services:
  nas-manager:
    build: .
    container_name: nas-manager
    ports:
      - "127.0.0.1:5000:5000"  # 只允许本地访问
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
    depends_on:
      - filebrowser
    networks:
      - nas-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nas-manager.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.nas-manager.tls=true"

  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    ports:
      - "127.0.0.1:8088:80"  # 只允许本地访问
    volumes:
      - ./data:/srv
      - ./filebrowser/config:/config
      - ./filebrowser/database:/database
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
    networks:
      - nas-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.filebrowser.rule=Host(`your-domain.com`) && PathPrefix(`/filemanager`)"
      - "traefik.http.routers.filebrowser.tls=true"

networks:
  nas-network:
    driver: bridge
```

## 📊 监控和维护

### 1. 日志管理

```bash
# 查看应用日志
docker-compose logs -f nas-manager

# 查看文件管理器日志
docker-compose logs -f filebrowser

# 查看系统日志
docker system df
docker system prune
```

### 2. 备份和恢复

```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz data/ filebrowser/

# 恢复数据
tar -xzf backup-20250116.tar.gz
```

### 3. 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

## 🔍 故障排除

### 常见问题

#### 1. Docker 权限问题
```bash
# 将用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录或重启
newgrp docker
```

#### 2. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :5000

# 修改端口映射
docker-compose.yml:
  ports:
    - "5001:5000"  # 使用5001端口
```

#### 3. 数据卷权限
```bash
# 修复权限
sudo chown -R 1000:1000 data/ filebrowser/
```

#### 4. 内存不足
```bash
# 增加Docker内存限制
docker-compose.yml:
  deploy:
    resources:
      limits:
        memory: 1G
```

### 调试命令

```bash
# 进入容器调试
docker exec -it nas-manager bash

# 查看容器资源使用
docker stats nas-manager

# 检查网络连接
docker network ls
docker network inspect nas-network
```

## 📝 最佳实践

### 1. 安全建议
- 修改默认密码
- 使用HTTPS
- 定期更新镜像
- 限制容器权限
- 监控异常访问

### 2. 性能优化
- 使用SSD存储
- 配置适当的内存限制
- 启用日志轮转
- 定期清理无用镜像

### 3. 备份策略
- 定期备份数据目录
- 备份配置文件
- 测试恢复流程
- 异地备份重要数据

## 📞 支持

如果遇到问题，请：
1. 查看日志文件
2. 检查配置文件
3. 参考故障排除部分
4. 提交GitHub Issue

---

**注意**: 生产环境部署前请仔细阅读安全配置部分，确保系统安全。 