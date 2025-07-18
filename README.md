# 嵌入式轻NAS管理软件

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Required-orange.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个轻量级的嵌入式NAS管理系统，基于Flask和Docker构建，提供容器管理、资源监控、文件管理等功能。

## 🌟 功能特性

### 🔐 用户管理
- 多用户注册/登录系统
- 管理员权限控制
- 12位密码安全策略
- 用户权限分级管理

### 🐳 容器管理
- Docker容器一键启动/停止/重启
- 容器日志实时查看
- 镜像拉取和管理
- 容器Web UI自动跳转

### 📊 资源监控
- 实时CPU使用率监控
- 内存使用情况统计
- 存储空间监控（支持多分区）
- RAID状态检测

### 🛍️ 应用商店
- 20+热门应用一键安装
- 分类管理（影音、云盘、下载、运维等）
- 安装进度实时显示
- 应用状态管理

### 📁 文件管理
- 集成FileBrowser Web文件管理器
- 多用户权限控制
- 自动登录跳转
- 文件上传/下载/分享

### 🌍 国际化
- 中英文双语支持
- 动态语言切换
- 完整翻译覆盖

### 🧪 自动化测试
- 后端API测试（pytest）
- 前端E2E测试（Playwright）
- 详细测试注释
- 持续集成支持

## 🚀 快速开始

### 系统要求

- **操作系统**: Linux/ARM64/WSL2/Windows
- **Python**: 3.7+
- **Docker**: 已安装并运行
- **内存**: 至少512MB可用内存

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/dockerManager.git
cd dockerManager
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python app.py
```

4. **访问系统**
- 打开浏览器访问: `http://localhost:5000`
- 默认管理员账号: `admin`
- 默认密码: `admin123456789`

## 📖 使用指南

### 首次登录
1. 使用默认管理员账号登录
2. 建议立即修改默认密码
3. 进入"用户管理"创建其他用户

### 容器管理
1. 首页查看所有运行中的容器
2. 点击容器卡片进行启动/停止/重启操作
3. 点击容器图标可跳转到Web管理界面
4. 查看容器日志了解运行状态

### 应用安装
1. 进入"应用商店"页面
2. 选择需要的应用
3. 点击"安装"按钮
4. 等待安装完成

### 文件管理
1. 点击导航栏"文件管理器"
2. 使用Web界面管理文件
3. 支持上传、下载、分享等操作

### 资源监控
- 首页实时显示系统资源使用情况
- 每2秒自动刷新数据
- 支持多硬盘和RAID监控

## 🔧 配置说明

### 环境变量
```bash
# Flask配置
export FLASK_ENV=production
export SECRET_KEY=your_secret_key_here

# Docker配置
export DOCKER_HOST=unix:///var/run/docker.sock

# 文件管理器配置
export FILEBROWSER_PORT=8088
export DATA_DIR=/DATA
```

### 数据库
- 使用SQLite数据库存储用户信息
- 数据库文件: `users.db`
- 自动创建初始管理员账号

### 文件管理器
- 自动启动FileBrowser容器
- 端口: 8088
- 数据目录: `/DATA`
- 自动同步用户账号

## 🧪 测试

### 运行后端测试
```bash
pytest test_app.py -v
```

### 运行前端测试
```bash
# 安装Playwright
npm install -g playwright
playwright install

# 运行测试
node test_web.js
```

## 📁 项目结构

```
dockerManager/
├── app.py                 # 主应用程序
├── requirements.txt       # Python依赖
├── apps.json             # 应用商店配置
├── test_app.py           # 后端测试
├── test_web.js           # 前端测试
├── templates/            # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── appstore.html     # 应用商店
│   └── ...
├── translations/         # 国际化文件
│   ├── zh/              # 中文
│   └── en/              # 英文
├── static/              # 静态资源
├── filebrowser/         # 文件管理器配置
└── users.db             # 用户数据库
```

## 🔒 安全说明

### 密码策略
- 管理员密码必须不少于12位
- 支持密码修改和同步
- 密码哈希存储

### 权限控制
- 管理员可访问所有功能
- 普通用户仅可查看容器状态
- 文件管理器权限分级

### 网络安全
- 生产环境建议使用HTTPS
- 定期更新依赖包
- 监控异常访问

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 版权信息

© 2025 梁宏伟 (lianghongwei). 保留所有权利。

联系方式: 邮箱 287066024@qq.com

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

详细贡献指南请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 更新日志

详细更新历史请查看 [CHANGELOG.md](CHANGELOG.md)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Docker](https://www.docker.com/) - 容器技术
- [FileBrowser](https://filebrowser.org/) - 文件管理器
- [Bootstrap](https://getbootstrap.com/) - UI框架

## 📞 联系方式

- 项目主页: [GitHub](https://github.com/your-username/dockerManager)
- 问题反馈: [Issues](https://github.com/your-username/dockerManager/issues)
- 邮箱: your-email@example.com

---

**注意**: 本项目仅适用于已安装Docker的环境，Flask开发服务器不适合生产环境使用。