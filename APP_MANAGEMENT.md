# 应用商店管理功能

## 功能概述

应用商店管理功能允许管理员手动添加、编辑和删除应用商店中的APP，提供了完整的CRUD操作。

## 功能特性

### 🔧 管理员功能
- **添加APP**: 管理员可以手动添加新的APP到应用商店
- **编辑APP**: 管理员可以修改现有APP的配置信息
- **删除APP**: 管理员可以删除不需要的APP
- **查看APP列表**: 获取所有APP的详细信息

### 🎨 用户界面
- **响应式设计**: 支持桌面和移动设备
- **直观操作**: 简洁的模态框界面
- **实时反馈**: 操作结果即时显示
- **多语言支持**: 中文和英文界面

### 🔒 权限控制
- 仅管理员可以执行添加、编辑、删除操作
- 普通用户只能查看和安装APP
- 所有操作都有日志记录

## API接口

### 1. 添加APP
```http
POST /api/add_app
Content-Type: application/json

{
  "name": "APP名称",
  "image": "Docker镜像",
  "icon": "图标类名",
  "description": "APP描述",
  "category_zh": "中文分类",
  "category_en": "英文分类",
  "default_ports": {"80/tcp": 8080},
  "env": ["环境变量"],
  "volumes": ["数据卷"]
}
```

### 2. 编辑APP
```http
POST /api/update_app
Content-Type: application/json

{
  "name": "APP名称",
  "image": "新的Docker镜像",
  "icon": "新的图标类名",
  "description": "新的描述",
  "category_zh": "新的中文分类",
  "category_en": "新的英文分类",
  "default_ports": {"80/tcp": 8081},
  "env": ["新的环境变量"],
  "volumes": ["新的数据卷"]
}
```

### 3. 删除APP
```http
POST /api/delete_app
Content-Type: application/json

{
  "name": "APP名称"
}
```

### 4. 获取APP列表
```http
GET /api/get_apps
```

## 使用说明

### 添加新APP

1. **登录管理员账号**
   - 访问应用商店页面
   - 确保已登录管理员账号

2. **点击添加按钮**
   - 在应用商店页面右上角点击"添加APP"按钮
   - 弹出添加APP的模态框

3. **填写APP信息**
   - **APP名称**: 必填，APP的显示名称
   - **Docker镜像**: 必填，Docker镜像地址（如：nginx:latest）
   - **图标**: 可选，选择APP图标
   - **描述**: 必填，APP的详细描述
   - **中文分类**: 必填，中文分类名称
   - **英文分类**: 必填，英文分类名称
   - **端口映射**: 可选，格式：主机端口:容器端口，多个用逗号分隔
   - **数据卷**: 可选，格式：主机路径:容器路径，多个用逗号分隔
   - **环境变量**: 可选，格式：KEY=VALUE，多个用逗号分隔

4. **保存APP**
   - 点击"添加"按钮保存
   - 系统会自动验证并添加到apps.json文件

### 编辑APP

1. **进入编辑模式**
   - 在APP卡片右上角点击三点菜单
   - 选择"编辑"选项

2. **修改信息**
   - 在编辑模态框中修改需要更新的信息
   - 支持修改所有字段

3. **保存更改**
   - 点击"保存"按钮
   - 系统会更新apps.json文件

### 删除APP

1. **确认删除**
   - 在APP卡片右上角点击三点菜单
   - 选择"删除"选项
   - 确认删除操作

2. **完成删除**
   - 系统会从apps.json文件中移除该APP
   - 页面会自动刷新

## 配置说明

### APP数据结构
```json
{
  "name": "APP名称",
  "image": "Docker镜像",
  "icon": "Bootstrap图标类名",
  "description": "APP描述",
  "category_zh": "中文分类",
  "category_en": "英文分类",
  "default_ports": {
    "80/tcp": 8080,
    "443/tcp": 8443
  },
  "env": [
    "PASSWORD=123456",
    "DEBUG=true"
  ],
  "volumes": [
    "/data/app:/app/data",
    "/var/log/app:/app/logs"
  ]
}
```

### 支持的图标
- `bi-app`: 默认图标
- `bi-film`: 影音类
- `bi-cloud`: 云盘类
- `bi-download`: 下载类
- `bi-gear`: 工具类
- `bi-database`: 数据库类
- `bi-bar-chart`: 监控类
- `bi-house-door`: 智能家居类
- `bi-shield-lock`: 安全类
- `bi-code-slash`: 开发类

### 端口映射格式
- 格式：`主机端口:容器端口`
- 示例：`8080:80,8443:443`
- 容器端口会自动添加`/tcp`后缀

### 数据卷格式
- 格式：`主机路径:容器路径`
- 示例：`/data/app:/app/data`
- 支持多个数据卷，用逗号分隔

### 环境变量格式
- 格式：`KEY=VALUE`
- 示例：`PASSWORD=123456,DEBUG=true`
- 支持多个环境变量，用逗号分隔

## 测试

### 运行测试脚本
```bash
python test_app_management.py
```

### 测试内容
- 登录验证
- 获取APP列表
- 添加新APP
- 更新APP信息
- 删除APP
- 验证操作结果

## 注意事项

### 安全考虑
- 所有管理操作都需要管理员权限
- 操作日志会记录管理员的操作行为
- 输入验证防止恶意数据

### 数据持久化
- APP信息保存在`apps.json`文件中
- 文件格式为UTF-8编码的JSON
- 建议定期备份该文件

### 性能优化
- 页面使用异步加载
- 操作结果实时反馈
- 支持后台安装APP

### 错误处理
- 网络错误自动重试
- 输入验证错误提示
- 操作失败友好提示

## 故障排除

### 常见问题

1. **添加APP失败**
   - 检查必填字段是否完整
   - 验证APP名称是否重复
   - 确认Docker镜像地址正确

2. **编辑APP失败**
   - 检查APP是否存在
   - 验证修改的数据格式
   - 确认有足够的权限

3. **删除APP失败**
   - 检查APP是否存在
   - 确认没有正在运行的容器
   - 验证文件权限

### 日志查看
```bash
# 查看应用日志
tail -f app.log

# 查看Docker日志
docker logs nas-manager
```

## 更新日志

### v1.0.0 (2025-07-18)
- ✅ 添加管理员手动增加APP功能
- ✅ 添加APP编辑功能
- ✅ 添加APP删除功能
- ✅ 完善前端界面
- ✅ 添加API接口
- ✅ 添加权限控制
- ✅ 添加操作日志
- ✅ 添加测试脚本

## 技术支持

如有问题或建议，请通过以下方式联系：

- **GitHub Issues**: 提交问题报告
- **邮箱**: 发送邮件反馈
- **文档**: 查看项目文档

---

**注意**: 此功能仅限管理员使用，请谨慎操作，避免误删重要APP。