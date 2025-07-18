"""
嵌入式轻NAS管理软件后端自动化测试代码
Backend automated test code for Embedded Lite NAS Management Software

- 覆盖用户注册、登录、登出、资源监控、用户管理、应用商店、文件管理器、密码修改、容器管理等主要功能点
- 采用pytest框架，所有测试、fixture、辅助函数均有详细中英文注释，便于团队维护
"""
import pytest
from app import app, init_db, get_db

@pytest.fixture(scope='module')
def client():
    """
    Flask 测试客户端fixture。
    - 初始化测试数据库
    - 提供测试用client对象
    Flask test client fixture.
    - Initialize test database
    - Provide client object for testing
    """
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def register(client, username, password):
    """
    注册用户辅助函数
    - 用于测试用例中快速注册用户
    Helper function for user registration
    - Used to quickly register a user in test cases
    """
    return client.post('/register', data={'username': username, 'password': password}, follow_redirects=True)

def login(client, username, password):
    """
    登录用户辅助函数
    - 用于测试用例中快速登录
    Helper function for user login
    - Used to quickly log in a user in test cases
    """
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def logout(client):
    """
    登出用户辅助函数
    - 用于测试用例中快速登出
    Helper function for user logout
    - Used to quickly log out a user in test cases
    """
    return client.get('/logout', follow_redirects=True)

def test_register_login_logout(client):
    """
    测试注册、登录、登出流程
    - 注册新用户
    - 登录
    - 登出
    """
    rv = register(client, 'testuser', 'testpass')
    assert b'注册成功' in rv.data or b'login' in rv.data.lower()
    rv = login(client, 'testuser', 'testpass')
    assert b'首页' in rv.data or b'index' in rv.data.lower()
    rv = logout(client)
    assert b'登录' in rv.data or b'login' in rv.data.lower()

def test_duplicate_register(client):
    """
    测试重复注册同一用户名
    """
    register(client, 'dupuser', '123456')
    rv = register(client, 'dupuser', '123456')
    assert b'已存在' in rv.data or b'exists' in rv.data.lower()

def test_wrong_login(client):
    """
    测试错误密码登录
    """
    rv = login(client, 'testuser', 'wrongpass')
    assert b'错误' in rv.data or b'error' in rv.data.lower()

def test_api_resource(client):
    """
    测试资源监控API
    - 返回应包含cpu/mem/disks/raid字段
    """
    login(client, 'testuser', 'testpass')
    rv = client.get('/api/resource')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'cpu' in data and 'mem' in data and 'disks' in data and 'raid' in data

def test_appstore_page(client):
    """
    测试应用商店页面可访问
    """
    login(client, 'testuser', 'testpass')
    rv = client.get('/appstore')
    assert rv.status_code == 200
    assert b'APP' in rv.data or b'app' in rv.data.lower()

def test_user_management(client):
    """
    测试用户管理页面（需管理员权限）
    """
    login(client, 'admin', 'admin123456789')
    rv = client.get('/users')
    assert rv.status_code == 200
    assert b'用户' in rv.data or b'user' in rv.data.lower()

def test_set_admin_and_unset(client):
    """
    测试设置/取消管理员权限
    - 先插入普通用户
    - 设置为管理员
    - 再取消管理员
    """
    login(client, 'admin', 'admin123456789')
    db = get_db()
    db.execute('INSERT OR IGNORE INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)', ('normaluser', 'hash', 0))
    db.commit()
    # 获取normaluser的id
    user = db.execute('SELECT id FROM users WHERE username=?', ('normaluser',)).fetchone()
    uid = user[0]
    rv = client.get(f'/set_admin/{uid}', follow_redirects=True)
    assert b'管理员' in rv.data or b'admin' in rv.data.lower()
    rv = client.get(f'/unset_admin/{uid}', follow_redirects=True)
    assert b'取消' in rv.data or b'unset' in rv.data.lower()

def test_delete_user(client):
    """
    测试删除用户
    """
    login(client, 'admin', 'admin123456789')
    db = get_db()
    db.execute('INSERT OR IGNORE INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)', ('deluser', 'hash', 0))
    db.commit()
    rv = client.post('/delete_user/deluser', follow_redirects=True)
    assert b'已删除' in rv.data or b'deleted' in rv.data.lower()

def test_filemanager_entry(client):
    """
    测试文件管理器入口跳转
    """
    login(client, 'admin', 'admin123456789')
    rv = client.get('/filemanager')
    assert rv.status_code == 302
    assert '/filemanager/' in rv.headers['Location']

def test_change_password(client):
    """
    测试管理员修改密码流程
    - 修改密码
    - 恢复原密码
    """
    login(client, 'admin', 'admin123456789')
    rv = client.post('/change_password', data={'old_password': 'admin123456789', 'new_password': 'newpassword123'}, follow_redirects=True)
    assert b'密码修改成功' in rv.data or b'success' in rv.data.lower()
    # 恢复密码
    rv = client.post('/change_password', data={'old_password': 'newpassword123', 'new_password': 'admin123456789'}, follow_redirects=True)
    assert b'密码修改成功' in rv.data or b'success' in rv.data.lower()

def test_container_list(client):
    """
    测试容器列表API
    Test the container list API.
    步骤：
    1. 管理员登录
    2. 访问 /api/containers 获取容器列表
    3. 断言返回200且为列表类型
    Steps:
    1. Login as admin
    2. Access /api/containers to get container list
    3. Assert status 200 and response is a list
    """
    login(client, 'admin', 'admin123456789')
    rv = client.get('/api/containers')
    assert rv.status_code == 200  # 断言HTTP状态码为200
    data = rv.get_json()
    assert isinstance(data, list)  # 应返回容器列表，Assert response is a list


def test_container_start_stop(client):
    """
    测试启动/停止容器API
    Test start/stop container API.
    步骤：
    1. 管理员登录
    2. 启动指定容器
    3. 停止指定容器
    4. 断言均返回200
    Steps:
    1. Login as admin
    2. Start a specific container
    3. Stop the specific container
    4. Assert both responses are 200
    """
    login(client, 'admin', 'admin123456789')
    # 启动容器 Start container
    rv = client.post('/api/container/start', json={'name': 'test_container'})
    assert rv.status_code == 200  # 断言启动成功 Assert start success
    # 停止容器 Stop container
    rv = client.post('/api/container/stop', json={'name': 'test_container'})
    assert rv.status_code == 200  # 断言停止成功 Assert stop success

# 你可以继续添加容器管理、镜像管理、日志查看等API的测试用例，并为每个测试加上类似注释