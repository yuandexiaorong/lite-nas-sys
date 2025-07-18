# 贡献指南

感谢您对嵌入式轻NAS管理软件项目的关注！我们欢迎所有形式的贡献，包括但不限于代码、文档、测试、问题报告等。

## 🤝 如何贡献

### 📋 贡献类型

#### 🐛 问题报告 (Bug Reports)
- 使用 [GitHub Issues](https://github.com/your-username/dockerManager/issues) 报告问题
- 提供详细的问题描述和复现步骤
- 包含系统环境信息（操作系统、Python版本、Docker版本等）
- 附上错误日志和截图（如适用）

#### 💡 功能建议 (Feature Requests)
- 在 Issues 中提出新功能建议
- 详细描述功能需求和预期效果
- 讨论实现方案和技术可行性
- 考虑对现有功能的影响

#### 🔧 代码贡献 (Code Contributions)
- Fork 项目到个人仓库
- 创建功能分支进行开发
- 编写测试用例
- 提交 Pull Request

#### 📚 文档改进 (Documentation)
- 完善 README 文档
- 添加代码注释
- 编写使用教程
- 翻译文档

#### 🧪 测试贡献 (Testing)
- 编写单元测试
- 进行集成测试
- 报告测试结果
- 改进测试覆盖率

## 🚀 开发环境搭建

### 系统要求
- Python 3.7+
- Docker
- Git

### 环境准备
```bash
# 1. Fork 并克隆项目
git clone https://github.com/your-username/dockerManager.git
cd dockerManager

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install pytest pytest-cov flake8 black

# 5. 启动开发服务器
python app.py
```

### 代码规范

#### Python 代码规范
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 编码规范
- 使用 4 个空格缩进
- 行长度不超过 120 字符
- 函数和类必须有文档字符串

#### 代码格式化
```bash
# 使用 black 格式化代码
black app.py

# 使用 flake8 检查代码规范
flake8 app.py
```

#### 注释规范
- 所有函数必须有中英文文档字符串
- 复杂逻辑需要行内注释
- 使用中文注释说明业务逻辑
- 使用英文注释说明技术细节

示例：
```python
def create_user(username, password):
    """
    创建新用户
    Create a new user.
    
    Args:
        username (str): 用户名 / Username
        password (str): 密码 / Password
        
    Returns:
        bool: 创建成功返回True / Returns True if successful
    """
    # 检查用户名是否已存在
    # Check if username already exists
    if user_exists(username):
        return False
    
    # 创建用户记录
    # Create user record
    return add_user_to_db(username, hash_password(password))
```

## 📝 提交规范

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型
- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

#### 示例
```
feat(user): 添加用户密码强度验证

- 实现12位密码长度检查
- 添加密码复杂度验证
- 更新相关测试用例

Closes #123
```

### 分支命名规范
- `feature/功能名称` - 新功能开发
- `fix/问题描述` - 问题修复
- `docs/文档类型` - 文档更新
- `test/测试类型` - 测试相关

## 🧪 测试指南

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test_app.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行前端测试
node test_web.js
```

### 编写测试
- 每个新功能都要有对应的测试
- 测试覆盖率不低于 80%
- 测试用例要有详细的中英文注释
- 使用有意义的测试数据

示例：
```python
def test_user_registration_success(client):
    """
    测试用户注册成功
    Test successful user registration.
    """
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    assert response.status_code == 200
    assert b'注册成功' in response.data
```

## 🔄 Pull Request 流程

### 1. 准备工作
- 确保代码通过所有测试
- 更新相关文档
- 检查代码规范

### 2. 创建 Pull Request
- 使用清晰的标题描述变更
- 在描述中详细说明修改内容
- 关联相关的 Issue
- 添加测试结果截图（如适用）

### 3. 代码审查
- 响应审查者的反馈
- 及时修改代码问题
- 保持沟通和讨论

### 4. 合并
- 获得至少一个维护者的批准
- 确保 CI/CD 检查通过
- 解决所有冲突

## 📋 贡献清单

在提交 Pull Request 前，请确认：

- [ ] 代码遵循项目编码规范
- [ ] 添加了必要的测试用例
- [ ] 测试全部通过
- [ ] 更新了相关文档
- [ ] 提交信息符合规范
- [ ] 没有引入新的警告或错误

## 🏷️ 标签说明

### Issue 标签
- `bug` - 问题报告
- `enhancement` - 功能增强
- `documentation` - 文档相关
- `good first issue` - 适合新手的简单问题
- `help wanted` - 需要帮助的问题

### Pull Request 标签
- `ready for review` - 准备审查
- `work in progress` - 开发中
- `needs review` - 需要审查
- `approved` - 已批准

## 🎯 新手指南

### 从哪里开始
1. 查看 `good first issue` 标签的问题
2. 阅读项目文档和代码注释
3. 在本地环境运行项目
4. 尝试修复简单的问题

### 学习资源
- [Flask 官方文档](https://flask.palletsprojects.com/)
- [Docker 官方文档](https://docs.docker.com/)
- [Python 编码规范](https://www.python.org/dev/peps/pep-0008/)
- [Git 工作流](https://guides.github.com/introduction/flow/)

## 📞 联系我们

### 沟通渠道
- **GitHub Issues**: 问题讨论和功能建议
- **GitHub Discussions**: 一般性讨论
- **邮箱**: your-email@example.com

### 行为准则
- 尊重所有贡献者
- 保持友好和专业的交流
- 欢迎不同背景和经验水平的贡献者
- 提供建设性的反馈

## 🙏 致谢

感谢所有为项目做出贡献的开发者！您的贡献让这个项目变得更好。

### 贡献者荣誉墙
贡献者的名字将出现在：
- README.md 文件中
- 项目发布说明中
- 项目网站（如果有）

---

**注意**: 通过提交 Pull Request，您同意您的贡献将在 MIT 许可证下发布。 
