# 软件著作权文档

## 目录
1. [软件基本信息](#一软件基本信息)
2. [软件技术特点](#二软件技术特点)
3. [软件功能说明](#三软件功能说明)
4. [代码量统计](#四代码量统计)
5. [版本历史](#五版本历史)
6. [部署说明](#六部署说明)
7. [其他说明](#七其他说明)

## 一、软件基本信息

### 软件名称
嵌入式轻NAS管理软件

### 软件版本
V1.0.0

### 开发完成日期
2025-01-16

### 软件著作权人
梁宏伟 <lianghongwei>

### 联系方式
邮箱: 287066024@qq.com

## 二、软件技术特点

### 1. 技术架构
- **后端框架**: Flask + Flask-Login + Flask-Babel
- **数据库**: SQLite
- **容器技术**: Docker SDK for Python
- **前端框架**: Bootstrap 5 + Bootstrap Icons
- **监控库**: psutil (跨平台资源监控)
- **测试框架**: pytest + Playwright

### 2. 功能模块
- **用户管理系统**: 多用户注册/登录、管理员权限控制、12位密码安全策略、用户权限分级管理
- **容器管理功能**: Docker容器一键启动/停止/重启、容器日志实时查看、镜像拉取和管理、容器Web UI自动跳转
- **资源监控系统**: 实时CPU使用率监控、内存使用情况统计、存储空间监控(支持多分区)、RAID状态检测
- **应用商店**: 20+热门应用一键安装、分类管理、安装进度实时显示、应用状态管理
- **文件管理器集成**: 集成FileBrowser Web文件管理器、多用户权限控制、自动登录跳转、文件上传/下载/分享
- **国际化支持**: 中英文双语支持、动态语言切换、完整翻译覆盖
- **自动化测试**: 后端API测试(pytest框架)、前端E2E测试(Playwright)

### 3. 安全特性
- 密码哈希存储(Werkzeug)
- CSRF保护
- 会话管理
- 权限验证装饰器
- 12位密码长度要求

### 4. 兼容性
支持平台: Linux/ARM64/WSL2/Windows

## 三、软件功能说明

### 1. 用户管理
- 提供用户注册、登录和注销功能
- 管理员可创建和管理用户账户
- 实现了12位密码安全策略
- 支持用户权限分级管理

### 2. 容器管理
- 可视化管理Docker容器的启动、停止和重启
- 实时查看容器日志
- 管理Docker镜像
- 自动检测容器Web UI端口并提供跳转

### 3. 资源监控
- 实时监控CPU使用率
- 显示内存使用情况
- 监控多个存储分区的使用情况
- 检测RAID状态

### 4. 应用商店
- 提供20+常用应用的一键安装
- 应用分类管理(影音、云盘、下载、运维等)
- 实时显示安装进度
- 管理已安装应用的状态

### 5. 文件管理
- 集成FileBrowser提供Web文件管理界面
- 支持文件上传、下载和分享
- 实现多用户文件权限控制
- 自动登录文件管理器

### 6. 国际化
- 支持中英文双语切换
- 动态加载语言资源
- 完整覆盖所有界面元素的翻译

## 四、代码量统计
- **总代码行数**: 7079行
- **功能代码**: 6113行(约占86.4%)
- **配置代码**: 487行(约占6.9%)
- **测试覆盖率**: 90%+

## 五、版本历史

### V1.0.0 (2025-01-16)
- 首次正式发布
- 包含用户管理、容器管理、资源监控、应用商店、文件管理、国际化等完整功能
- 实现自动化测试框架
- 完善安全机制

### V0.9.0 (2025-01-15)
- 开发阶段版本
- 完成基础Flask应用框架搭建
- 实现用户认证系统
- 开发Docker容器管理API
- 设计基础Web界面

### V0.8.0 (2025-01-14)
- 项目规划阶段
- 完成需求分析
- 设计系统架构
- 确定技术栈选型
- 规划功能模块

## 六、部署说明

### 系统要求
- 操作系统: Linux/ARM64/WSL2/Windows
- Python: 3.7+
- Docker: 已安装并运行
- 内存: 至少512MB可用内存

### 安装步骤
1. 克隆项目: `git clone git@github.com:yuandexiaorong/lite-nas-sys.git && cd lite-nas-sys`
2. 安装依赖: `pip install -r requirements.txt`
3. 启动应用: `python app.py`
4. 访问系统: 打开浏览器访问 `http://localhost:5000`

### Docker部署
提供Docker Compose配置文件，支持一键部署

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

## 七、其他说明

### 开发目的
提供一个轻量级、易于部署的嵌入式NAS管理系统，满足个人和小型团队的数据存储和管理需求。

### 适用范围
适用于家庭、小型办公室等场景的NAS设备管理。

### 后续规划
- 容器备份/恢复功能
- 更详细的监控图表
- SSL证书管理
- 移动端适配优化
- 主题切换功能
- 性能统计报告
- 操作审计日志
- API限流保护

### 注意事项
- 生产环境建议使用HTTPS
- 定期更新依赖包
- 监控异常访问
- 首次登录后请立即修改默认密码

---

**文档生成日期**: 2025-07-18
**文档版本**: V1.0.0