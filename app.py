# =============================================================================
# 文件名: app.py
# 功能:   嵌入式轻nas管理软件主程序
# 作者: 梁宏伟 <lianghongwei>，邮箱: 287066024@qq.com
# 创建时间: 2025-07-16
# 最后修改: 2025-07-18
# 依赖:   Flask, Flask-Login, Flask-Babel, Docker SDK, psutil, sqlite3, werkzeug
# 说明:   提供用户注册/登录/权限管理、容器/镜像管理、日志、资源监控、Web文件管理器集成等功能
# 注意事项:
#   - 仅适用于已安装 Docker 的 Linux/ARM64/WSL2/Windows 环境
#   - Flask 开发服务器不适合生产环境
#   - 项目名称：嵌入式轻nas管理软件
# =============================================================================

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify, Response
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_babel import Babel, gettext as _
from werkzeug.security import generate_password_hash, check_password_hash
import docker
import psutil
import json
import threading
import time
import requests
import subprocess
import platform
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

# 导入配置系统 / Import configuration system
from config import get_config, validate_config

# 导入工具函数 / Import utility functions
from utils import get_filebrowser_token, reset_filebrowser_admin_password, create_filebrowser_user

# ================= 配置初始化 =================
# Configuration initialization
config = get_config()
try:
    validate_config(config)
except ValueError as e:
    print(f"配置验证失败 / Configuration validation failed: {e}")
    exit(1)

# ================= Flask 应用配置 =================
app = Flask(__name__)

# 应用配置 / Application configuration
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG
app.config['TESTING'] = config.TESTING
app.config['BABEL_DEFAULT_LOCALE'] = config.BABEL_DEFAULT_LOCALE
app.config['BABEL_DEFAULT_TIMEZONE'] = config.BABEL_DEFAULT_TIMEZONE
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME
app.config['SESSION_COOKIE_SECURE'] = config.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = config.SESSION_COOKIE_SAMESITE
app.config['WTF_CSRF_ENABLED'] = config.WTF_CSRF_ENABLED
app.config['WTF_CSRF_TIME_LIMIT'] = config.WTF_CSRF_TIME_LIMIT

# ================= 日志配置 =================
# Logging configuration
if not app.debug and not app.testing:
    # 确保日志目录存在 / Ensure log directory exists
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志处理器 / Configure log handler
    file_handler = RotatingFileHandler(
        config.LOG_FILE, 
        maxBytes=config.LOG_MAX_SIZE, 
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    app.logger.info('NAS Manager startup')

# ================= 国际化相关 =================
def get_locale():
    """
    获取当前用户选择的语言。
    Get current user selected language.
    Returns:
        str: 语言代码（如'zh'或'en'） / Language code (e.g., 'zh' or 'en')
    """
    return session.get('lang', config.DEFAULT_LANGUAGE)

babel = Babel(app, locale_selector=get_locale)

@app.context_processor
def inject_get_locale():
    """
    注入 get_locale 到模板上下文，便于模板中直接调用。
    Inject get_locale to template context for direct use in templates.
    Returns:
        dict: 包含 get_locale 的字典 / Dictionary containing get_locale
    """
    return dict(get_locale=get_locale)

# ================= 登录管理相关 =================
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # 未登录时重定向到 login / Redirect to login when not authenticated
login_manager.session_protection = config.SESSION_PROTECTION

# Docker客户端配置 / Docker client configuration
try:
    client = docker.from_env(timeout=config.DOCKER_TIMEOUT)
    app.logger.info(f'Docker client initialized with timeout: {config.DOCKER_TIMEOUT}s')
except Exception as e:
    app.logger.error(f'Failed to initialize Docker client: {e}')
    client = None

# 数据库配置 / Database configuration
DATABASE = config.DATABASE_PATH

# ================= 用户模型 =================
class User(UserMixin):
    """
    用户模型，继承自 Flask-Login 的 UserMixin。
    User model, inherits from Flask-Login UserMixin.
    属性 / Attributes:
        id (int): 用户ID / User ID
        username (str): 用户名 / Username
        password_hash (str): 密码哈希 / Password hash
        is_admin (int): 是否为管理员（1为管理员，0为普通用户） / Is admin (1 for admin, 0 for regular user)
    """
    def __init__(self, id, username, password_hash, is_admin):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_admin = is_admin

    def get_id(self):
        """
        获取用户ID，供 Flask-Login 使用。
        Get user ID for Flask-Login.
        Returns:
            str: 用户ID字符串 / User ID string
        """
        return str(self.id)

# ================= 数据库操作相关 =================
def get_db():
    """
    获取当前请求上下文的 SQLite 数据库连接。
    Get SQLite database connection for current request context.
    若无连接则新建并绑定到 Flask g 对象。
    If no connection exists, create new one and bind to Flask g object.
    Returns:
        sqlite3.Connection: 数据库连接对象 / Database connection object
    注意事项 / Notes:
        - 每个请求结束后会自动关闭连接 / Connection will be closed automatically after each request
        - 数据库文件名由配置指定 / Database file name is specified by configuration
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    """
    执行 SQL 查询并返回结果。
    Execute SQL query and return results.
    Args:
        query (str): SQL 查询语句 / SQL query statement
        args (tuple): 查询参数 / Query parameters
        one (bool): 是否只返回一条结果 / Whether to return only one result
    Returns:
        list/tuple/None: 查询结果 / Query results
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    """
    初始化数据库，创建用户表并生成初始管理员账号。
    Initialize database, create user table and generate initial admin account.
    注意事项 / Notes:
        - 初始管理员账号：admin/admin123456789（12位密码） / Initial admin account: admin/admin123456789 (12-character password)
        - 若已存在则不会重复创建 / Will not recreate if already exists
    """
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            wallpaper TEXT
        )''')
        # 如果表已存在，添加wallpaper字段（如果不存在）
        try:
            db.execute('ALTER TABLE users ADD COLUMN wallpaper TEXT')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        db.commit()
        # 创建初始管理员 / Create initial admin
        admin = query_db('SELECT * FROM users WHERE username = ?', ('admin',), one=True)
        if not admin:
            # 使用固定的12位管理员密码 / Use fixed 12-character admin password
            admin_password = 'admin123456789'
            
            db.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                       ('admin', generate_password_hash(admin_password), 1))
            db.commit()
            app.logger.info(f'Initial admin account created with password: {admin_password}')
        # 同步 filebrowser 管理员 / Sync filebrowser admin
        sync_filebrowser_admin()

@app.teardown_appcontext
def close_connection(exception):
    """
    请求结束时自动关闭数据库连接。
    Automatically close database connection at end of request.
    Args:
        exception: 异常对象（可为None） / Exception object (can be None)
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login 用户加载回调。
    Flask-Login user loading callback.
    Args:
        user_id (str): 用户ID / User ID
    Returns:
        User/None: 用户对象或None / User object or None
    """
    user = query_db('SELECT * FROM users WHERE id = ?', (user_id,), one=True)
    if user:
        return User(user[0], user[1], user[2], user[3])
    return None

@app.route('/set_language/<lang>')
def set_language(lang):
    """
    设置当前会话的语言。
    Set current session language.
    Args:
        lang (str): 语言代码 / Language code
    Returns:
        Response: 重定向到前一页或首页 / Redirect to previous page or home page
    """
    if lang in config.LANGUAGES:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

# ================= 用户注册/登录/登出 =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册视图。
    User registration view.
    支持GET显示注册页，POST处理注册逻辑。
    Supports GET to display registration page, POST to handle registration logic.
    Returns:
        Response: 注册页或重定向 / Registration page or redirect
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 验证输入 / Validate input
        if not username or not password:
            flash(_('用户名和密码不能为空'))
            return redirect(url_for('register'))
        
        # 验证密码长度 / Validate password length
        if len(password) < config.PASSWORD_MIN_LENGTH:
            flash(_(f'密码长度不能少于{config.PASSWORD_MIN_LENGTH}位'))
            return redirect(url_for('register'))
        
        # 检查用户名是否已存在 / Check if username already exists
        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
        if user:
            flash(_('用户名已存在'))
            return redirect(url_for('register'))
        
        # 创建用户 / Create user
        db = get_db()
        db.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                   (username, generate_password_hash(password), 0))
        db.commit()
        
        # 注册主系统用户后，同步 filebrowser
        # After registering main system user, sync with filebrowser
        create_filebrowser_user(app, FILEBROWSER_URL, username, password)
        
        # 如果注册的是管理员，也同步 filebrowser 管理员密码
        # If registering admin, also sync filebrowser admin password
        if username == 'admin':
            reset_filebrowser_admin_password(app, 'filebrowser', username, password)
        
        flash(_('注册成功，请登录'))
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录视图。
    支持GET显示登录页，POST处理登录逻辑。
    Returns:
        Response: 登录页或重定向
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
        if user and check_password_hash(user[2], password):
            user_obj = User(user[0], user[1], user[2], user[3])
            login_user(user_obj)
            return redirect(url_for('index'))
        flash(_('用户名或密码错误'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """
    用户登出视图。
    需登录后访问。
    Returns:
        Response: 重定向到登录页
    """
    logout_user()
    return redirect(url_for('login'))

# ================= 权限装饰器 =================
def admin_required(f):
    """
    管理员权限装饰器。
    用于保护仅管理员可访问的视图。
    Args:
        f (function): 被装饰的视图函数
    Returns:
        function: 包装后的函数
    注意事项:
        - 若当前用户非管理员会自动重定向并提示
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash(_('需要管理员权限'))
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 导入工具函数
from utils import get_container_stats, safe_container_operation

# ================= 首页/容器管理 =================
@app.route('/')
@login_required
def index():
    """
    首页视图，展示容器、镜像、资源监控信息。
    需登录后访问。
    Returns:
        Response: 渲染首页模板
    """
    containers = client.containers.list(all=True)  # 获取所有容器
    images = client.images.list()  # 获取所有镜像
    cpu = psutil.cpu_percent(interval=0.5)  # 获取CPU使用率
    mem = psutil.virtual_memory()  # 获取内存信息
    # 为每个容器自动生成 web_url（优先常见 Web 端口）
    web_ports = [80, 443, 3000, 5000, 6881, 8080, 8081, 8096, 9000, 9091, 32400]
    for c in containers:
        web_url = ''
        ports = c.attrs.get('NetworkSettings', {}).get('Ports', {})
        # 先找常见 Web 端口
        for port_proto, bindings in ports.items():
            if not bindings or not port_proto.endswith('/tcp'):
                continue
            port = int(port_proto.split('/')[0])
            if port in web_ports:
                host_port = bindings[0]['HostPort']
                host_ip = bindings[0].get('HostIp', 'localhost')
                if host_ip in ['0.0.0.0', '127.0.0.1']:
                    host_ip = 'localhost'
                web_url = f'http://{host_ip}:{host_port}'
                break
        # 如果没找到常见端口，找第一个 TCP 端口
        if not web_url:
            for port_proto, bindings in ports.items():
                if not bindings or not port_proto.endswith('/tcp'):
                    continue
                host_port = bindings[0]['HostPort']
                host_ip = bindings[0].get('HostIp', 'localhost')
                if host_ip in ['0.0.0.0', '127.0.0.1']:
                    host_ip = 'localhost'
                web_url = f'http://{host_ip}:{host_port}'
                break
        c.web_url = web_url
    return render_template('index.html', containers=containers, images=images, cpu=cpu, mem=mem)

@app.route('/start/<cid>')
@login_required
def start_container(cid):
    """
    启动指定ID的容器。
    Args:
        cid (str): 容器ID
    Returns:
        Response: 重定向到首页
    """
    success, msg = safe_container_operation(
        lambda c: client.containers.get(c).start(),
        cid,
        _('容器已启动'),
        _('启动容器失败')
    )
    flash(msg)
    return redirect(url_for('index'))

@app.route('/stop/<cid>')
@login_required
def stop_container(cid):
    """
    停止指定ID的容器。
    Args:
        cid (str): 容器ID
    Returns:
        Response: 重定向到首页
    """
    success, msg = safe_container_operation(
        lambda c: client.containers.get(c).stop(),
        cid,
        _('容器已停止'),
        _('停止容器失败')
    )
    flash(msg)
    return redirect(url_for('index'))

@app.route('/restart/<cid>')
@login_required
def restart_container(cid):
    """
    重启指定ID的容器。
    Args:
        cid (str): 容器ID
    Returns:
        Response: 重定向到首页
    """
    success, msg = safe_container_operation(
        lambda c: client.containers.get(c).restart(),
        cid,
        _('容器已重启'),
        _('重启容器失败')
    )
    flash(msg)
    return redirect(url_for('index'))

@app.route('/remove/<cid>')
@login_required
@admin_required
def remove_container(cid):
    """
    删除指定ID的容器，仅管理员可用。
    Args:
        cid (str): 容器ID
    Returns:
        Response: 重定向到首页
    注意事项:
        - 强制删除，运行中容器也会被移除
    """
    success, msg = safe_container_operation(
        lambda c: client.containers.get(c).remove(force=True),
        cid,
        _('APP已删除'),
        _('删除容器失败')
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok' if success else 'error', 'msg': msg})
    flash(msg)
    return redirect(url_for('index'))

# 导入工具函数
from utils import retry_operation

# ================= 镜像管理 =================
@app.route('/pull_image', methods=['POST'])
@login_required
@admin_required
def pull_image():
    """
    拉取新镜像，仅管理员可用。
    Returns:
        Response: 重定向到首页
    """
    image = request.form['image']
    try:
        # 使用重试机制拉取镜像
        result = retry_operation(client.images.pull, max_retries=3, delay=2, repository=image)
        if result:
            flash(_('镜像拉取成功'))
        else:
            flash(_('镜像拉取失败: 重试次数已达上限'))
    except Exception as e:
        flash(_('镜像拉取失败: ') + str(e))
    return redirect(url_for('index'))

@app.route('/remove_image/<iid>')
@login_required
@admin_required
def remove_image(iid):
    """
    删除指定ID的镜像，仅管理员可用。
    Args:
        iid (str): 镜像ID
    Returns:
        Response: 重定向到首页
    注意事项:
        - 强制删除，若有容器依赖该镜像会一并删除
    """
    try:
        # 使用重试机制删除镜像
        result = retry_operation(client.images.remove, max_retries=3, delay=2, image=iid, force=True)
        if result is None:
            msg = _('APP源删除失败: 重试次数已达上限')
        else:
            msg = _('APP源已删除')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'ok' if result is not None else 'error', 'msg': msg})
        flash(msg)
    except Exception as e:
        msg = _('APP源删除失败: ') + str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'msg': msg}), 400
        flash(msg)
    return redirect(url_for('index'))

# ================= 日志查看 =================
@app.route('/logs/<cid>')
@login_required
def logs(cid):
    """
    查看指定容器的最近100行日志。
    Args:
        cid (str): 容器ID
    Returns:
        Response: 渲染日志模板
    """
    c = client.containers.get(cid)
    logs = c.logs(tail=100).decode(errors='ignore')
    return render_template('logs.html', logs=logs, container=c)

# ================= 用户管理（仅管理员） =================
@app.route('/users')
@login_required
@admin_required
def users():
    """
    用户管理页面，仅管理员可用。
    Returns:
        Response: 渲染用户管理模板
    """
    users = query_db('SELECT id, username, is_admin FROM users')
    return render_template('users.html', users=users)

@app.route('/set_admin/<uid>')
@login_required
@admin_required
def set_admin(uid):
    """
    将指定用户设为管理员。
    Args:
        uid (str): 用户ID
    Returns:
        Response: 重定向到用户管理页
    """
    db = get_db()
    db.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (uid,))
    db.commit()
    flash(_('已设为管理员'))
    return redirect(url_for('users'))

@app.route('/unset_admin/<uid>')
@login_required
@admin_required
def unset_admin(uid):
    """
    取消指定用户的管理员权限。
    确保系统中至少保留一个管理员。
    Args:
        uid (str): 用户ID
    Returns:
        Response: 重定向到用户管理页
    """
    db = get_db()
    
    # 检查是否是最后一个管理员
    admin_count = query_db('SELECT COUNT(*) FROM users WHERE is_admin = 1', one=True)[0]
    user_is_admin = query_db('SELECT is_admin FROM users WHERE id = ?', (uid,), one=True)[0]
    
    if admin_count == 1 and user_is_admin == 1:
        flash(_('不能取消最后一个管理员的权限'))
    else:
        db.execute('UPDATE users SET is_admin = 0 WHERE id = ?', (uid,))
        db.commit()
        flash(_('已取消管理员'))
    
    return redirect(url_for('users'))

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
@admin_required
def delete_user(username):
    """
    删除指定用户。
    Args:
        username (str): 用户名
    Returns:
        Response: 重定向到用户管理页或JSON响应
    注意事项:
        - 不能删除当前登录用户
        - 不能删除管理员账户
    """
    if username == current_user.username:
        flash(_('不能删除当前登录用户'))
        return redirect(url_for('users'))
    
    db = get_db()
    
    # 检查是否是管理员账户
    user = db.execute('SELECT is_admin FROM users WHERE username = ?', (username,)).fetchone()
    if user and user[0]:
        flash(_('不能删除管理员账户'))
        return redirect(url_for('users'))
    
    # 检查是否是最后一个用户
    user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count <= 1:
        flash(_('不能删除最后一个用户'))
        return redirect(url_for('users'))
    try:
        db.execute('DELETE FROM users WHERE username = ?', (username,))
        db.commit()
        # 同步删除 filebrowser 用户
        try:
            # 获取管理员密码用于认证
            admin_password = get_admin_password()
            if not admin_password:
                app.logger.error('无法获取管理员密码，无法删除filebrowser用户')
                flash(_('删除filebrowser用户失败: 无法获取管理员密码'))
                return redirect(url_for('users'))
            delete_filebrowser_user(app, FILEBROWSER_URL, username, admin_password)
        except Exception as e:
            app.logger.error(f'删除 filebrowser 用户失败: {e}')
        flash(_('用户已删除'))
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success', 'message': _('用户已删除')})
        return redirect(url_for('users'))
    except Exception as e:
        app.logger.error(f'删除用户失败: {e}')
        db.rollback()
        flash(f'{_('删除失败')}: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': f'{_('删除失败')}: {str(e)}'})
        return redirect(url_for('users'))

@app.route('/check_last_user')
@login_required
@admin_required
def check_last_user():
    """
    检查是否是最后一个用户
    Returns:
        JSON: 包含isLastUser字段的JSON响应
    """
    db = get_db()
    user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    return jsonify({'isLastUser': user_count <= 1})

@app.route('/appstore')
@login_required
def appstore():
    """
    应用商店页面，展示可一键安装的APP。
    """
    with open('apps.json', 'r', encoding='utf-8') as f:
        apps = json.load(f)
    # 获取所有已安装APP的名称（小写）
    installed_names = set()
    for c in client.containers.list(all=True):
        installed_names.add(c.name.lower())
    return render_template('appstore_fixed.html', apps=apps, installed_names=installed_names)

# 导入工具函数
from utils import create_filebrowser_user, delete_filebrowser_user, reset_filebrowser_admin_password, wait_filebrowser_ready, ensure_filebrowser_container_running

# 获取管理员密码辅助函数
def get_admin_password():
    db = sqlite3.connect(DATABASE)
    cur = db.execute('SELECT password_hash FROM users WHERE username = ? AND is_admin = 1', (FILEBROWSER_ADMIN,))
    row = cur.fetchone()
    db.close()
    if row:
        return row[0]
    return None

# 全局进度字典
install_progress = {}

def pull_image_with_progress(image, user_id):
    try:
        install_progress[user_id] = 'pulling'
        for line in client.api.pull(image, stream=True, decode=True):
            pass  # 只做拉取，不更新百分比
        install_progress[user_id] = 90  # APP源拉取完成
    except Exception as e:
        install_progress[user_id] = -1
        raise e

@app.route('/api/install_app', methods=['POST'])
@login_required
@admin_required
def install_app():
    data = request.json
    image = data['image']
    name = data['name']
    ports = data.get('ports', {})
    env = data.get('env', {})
    volumes = data.get('volumes', {})
    user_id = str(current_user.get_id())
    install_progress[user_id] = 0

    def do_install():
        try:
            pull_image_with_progress(image, user_id)
            # 创建APP阶段进度递增
            for p in range(91, 100):
                install_progress[user_id] = p
                time.sleep(0.05)
            client.containers.run(
                image, name=name, ports=ports, environment=env, volumes=volumes, detach=True
            )
            install_progress[user_id] = 100
        except Exception as e:
            install_progress[user_id] = -1

    t = threading.Thread(target=do_install)
    t.start()
    return jsonify({'status': 'ok'})

@app.route('/api/install_progress')
@login_required
def api_install_progress():
    user_id = str(current_user.get_id())
    progress = install_progress.get(user_id, 0)
    return jsonify({'progress': progress})

# ================= 应用商店管理 =================
@app.route('/api/add_app', methods=['POST'])
@login_required
@admin_required
def add_app():
    """
    管理员手动添加APP到应用商店。
    Admin manually add APP to app store.
    """
    try:
        data = request.json
        required_fields = ['name', 'image', 'description', 'category_zh', 'category_en']
        
        # 验证必需字段 / Validate required fields
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'缺少必需字段: {field}'}), 400
        
        # 验证APP名称是否已存在 / Check if app name already exists
        with open('apps.json', 'r', encoding='utf-8') as f:
            apps = json.load(f)
        
        for app in apps:
            if app['name'].lower() == data['name'].lower():
                return jsonify({'status': 'error', 'message': 'APP名称已存在'}), 400
        
        # 构建新APP对象 / Build new app object
        new_app = {
            'name': data['name'],
            'image': data['image'],
            'icon': data.get('icon', 'bi-app'),
            'description': data['description'],
            'category_zh': data['category_zh'],
            'category_en': data['category_en'],
            'default_ports': data.get('default_ports', {}),
            'env': data.get('env', []),
            'volumes': data.get('volumes', [])
        }
        
        # 添加到apps.json / Add to apps.json
        apps.append(new_app)
        
        with open('apps.json', 'w', encoding='utf-8') as f:
            json.dump(apps, f, ensure_ascii=False, indent=2)
        
        app.logger.info(f'Admin {current_user.username} added new app: {data["name"]}')
        return jsonify({'status': 'success', 'message': 'APP添加成功'})
        
    except Exception as e:
        app.logger.error(f'Error adding app: {e}')
        return jsonify({'status': 'error', 'message': f'添加失败: {str(e)}'}), 500

@app.route('/api/delete_app', methods=['POST'])
@login_required
@admin_required
def delete_app():
    """
    管理员删除APP从应用商店。
    Admin delete APP from app store.
    """
    try:
        data = request.json
        app_name = data.get('name')
        
        if not app_name:
            return jsonify({'status': 'error', 'message': '缺少APP名称'}), 400
        
        # 防止删除系统应用FileBrowser / Prevent deletion of system app FileBrowser
        if app_name.lower() == 'filebrowser':
            return jsonify({'status': 'error', 'message': '不能删除系统应用FileBrowser'}), 403
        
        # 读取现有APP列表 / Read existing app list
        with open('apps.json', 'r', encoding='utf-8') as f:
            apps = json.load(f)
        
        # 查找并删除APP / Find and delete app
        original_length = len(apps)
        apps = [app for app in apps if app['name'].lower() != app_name.lower()]
        
        if len(apps) == original_length:
            return jsonify({'status': 'error', 'message': 'APP不存在'}), 404
        
        # 保存更新后的APP列表 / Save updated app list
        with open('apps.json', 'w', encoding='utf-8') as f:
            json.dump(apps, f, ensure_ascii=False, indent=2)
        
        app.logger.info(f'Admin {current_user.username} deleted app: {app_name}')
        return jsonify({'status': 'success', 'message': 'APP删除成功'})
        
    except Exception as e:
        app.logger.error(f'Error deleting app: {e}')
        return jsonify({'status': 'error', 'message': f'删除失败: {str(e)}'}), 500

@app.route('/api/update_app', methods=['POST'])
@login_required
@admin_required
def update_app():
    """
    管理员更新APP信息。
    Admin update APP information.
    """
    try:
        data = request.json
        app_name = data.get('name')
        
        if not app_name:
            return jsonify({'status': 'error', 'message': '缺少APP名称'}), 400
        
        # 读取现有APP列表 / Read existing app list
        with open('apps.json', 'r', encoding='utf-8') as f:
            apps = json.load(f)
        
        # 查找并更新APP / Find and update app
        app_found = False
        for app in apps:
            if app['name'].lower() == app_name.lower():
                # 更新APP信息 / Update app information
                app.update({
                    'image': data.get('image', app.get('image')),
                    'icon': data.get('icon', app.get('icon')),
                    'description': data.get('description', app.get('description')),
                    'category_zh': data.get('category_zh', app.get('category_zh')),
                    'category_en': data.get('category_en', app.get('category_en')),
                    'default_ports': data.get('default_ports', app.get('default_ports', {})),
                    'env': data.get('env', app.get('env', [])),
                    'volumes': data.get('volumes', app.get('volumes', []))
                })
                app_found = True
                break
        
        if not app_found:
            return jsonify({'status': 'error', 'message': 'APP不存在'}), 404
        
        # 保存更新后的APP列表 / Save updated app list
        with open('apps.json', 'w', encoding='utf-8') as f:
            json.dump(apps, f, ensure_ascii=False, indent=2)
        
        app.logger.info(f'Admin {current_user.username} updated app: {app_name}')
        return jsonify({'status': 'success', 'message': 'APP更新成功'})
        
    except Exception as e:
        app.logger.error(f'Error updating app: {e}')
        return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'}), 500

@app.route('/api/get_apps')
@login_required
def get_apps():
    """
    获取应用商店APP列表。
    Get app store APP list.
    """
    try:
        with open('apps.json', 'r', encoding='utf-8') as f:
            apps = json.load(f)
        
        # 获取已安装的APP名称 / Get installed app names
        installed_names = set()
        if client:
            for c in client.containers.list(all=True):
                installed_names.add(c.name.lower())
        
        # 为每个APP添加安装状态 / Add installation status for each app
        for app in apps:
            app['installed'] = app['name'].lower() in installed_names
        
        return jsonify({'status': 'success', 'apps': apps})
        
    except Exception as e:
        app.logger.error(f'Error getting apps: {e}')
        return jsonify({'status': 'error', 'message': f'获取失败: {str(e)}'}), 500

# 文件浏览器配置
FILEBROWSER_URL = f"http://localhost:{config.FILEBROWSER_PORT}"
FILEBROWSER_ADMIN = "admin"

# 启动 filebrowser 后自动同步管理员账号密码
# 只在 ensure_filebrowser_running() 后调用
def sync_filebrowser_admin():
    if not wait_filebrowser_ready(app, FILEBROWSER_URL):
        app.logger.warning("filebrowser API 未就绪，跳过同步")
        return
    db = sqlite3.connect(DATABASE)
    cur = db.execute('SELECT username, password_hash FROM users WHERE is_admin = 1 ORDER BY id LIMIT 1')
    row = cur.fetchone()
    db.close()
    if row:
            username, password_hash = row
            # 尝试使用默认密码登录，如果失败则重置
            try:
                # 尝试使用符合长度要求的默认密码登录
                default_password = 'admin' * 4  # 12个字符
                token = get_filebrowser_token(app, FILEBROWSER_URL, 'admin', default_password)
                if token:
                    app.logger.info('使用默认密码登录FileBrowser成功')
                    # 使用默认密码创建/更新用户
                    create_filebrowser_user(app, FILEBROWSER_URL, username, default_password, default_password, is_admin=True)
                    # 然后重置密码为系统生成的安全密码
                    import secrets
                    admin_password = secrets.token_urlsafe(16)
                    reset_filebrowser_admin_password(app, 'filebrowser', 'admin', admin_password)
                    app.logger.info('FileBrowser管理员密码已重置并同步')
                else:
                    app.logger.warning('使用默认密码登录FileBrowser失败，尝试直接重置密码')
                    # 直接重置密码，不依赖API
                    import secrets
                    admin_password = secrets.token_urlsafe(16)
                    reset_filebrowser_admin_password(app, 'filebrowser', 'admin', admin_password)
                    # 使用新密码登录并创建用户
                    if get_filebrowser_token(app, FILEBROWSER_URL, 'admin', admin_password):
                        create_filebrowser_user(app, FILEBROWSER_URL, username, admin_password, admin_password, is_admin=True)
                        app.logger.info('FileBrowser管理员密码已重置并同步')
                    else:
                        app.logger.error('重置FileBrowser管理员密码后仍无法登录')
            except Exception as e:
                app.logger.error(f'同步FileBrowser管理员失败: {e}')

# 文件管理器入口跳转
@app.route('/filemanager')
def filemanager():
    return redirect("/filemanager/")

@app.route('/filemanager_auto_login')
@login_required
def filemanager_auto_login():
    return render_template('filemanager_auto_login.html')

# 先定义/static/路径的路由
@app.route('/static/<path:path>', methods=['GET'])
# 再定义/filemanager/路径的路由
@app.route('/filemanager/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/filemanager/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def filemanager_proxy(path):
    """
    文件管理器代理，转发请求到FileBrowser容器。
    File manager proxy, forward requests to FileBrowser container.
    """
    # 处理/static/路径的请求
    if request.path.startswith('/static/'):
        # 直接使用/static/路径
        url = f'http://127.0.0.1:{config.FILEBROWSER_PORT}{request.path}'
        app.logger.info(f'转发静态资源请求到: {url}')
    else:
        # 处理/filemanager/路径的请求
        if not path.startswith('/'):
            path = f'/{path}'
        url = f'http://127.0.0.1:{config.FILEBROWSER_PORT}{path}'
    
    # 复制所有请求头，保留原始Host头
    headers = dict(request.headers)
    
    # 添加X-Forwarded-*头，帮助FileBrowser正确识别请求来源
    headers['X-Forwarded-For'] = request.remote_addr
    headers['X-Forwarded-Proto'] = request.scheme
    headers['X-Forwarded-Host'] = request.host
    
    app.logger.info(f'转发请求到: {url}')
    app.logger.info(f'请求头: {headers}')
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True
    )
    app.logger.info(f'响应状态码: {resp.status_code}')
    app.logger.info(f'响应头: {resp.headers}')
    
    # 只排除必要的响应头
    excluded_headers = ['transfer-encoding', 'connection']
    response_headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, response_headers)
    return response

# ================= 程序入口 =================
def ensure_filebrowser_running():
    """
    确保FileBrowser容器正在运行。
    Ensure FileBrowser container is running.
    """
    try:
        # 确保数据目录存在 / Ensure data directory exists
        data_dir = config.FILEBROWSER_DATA_DIR
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            app.logger.info(f'Created data directory: {data_dir}')
        
        # 确保配置和数据库目录为绝对路径 / Ensure config and database directories are absolute paths
        base_dir = os.path.abspath(os.path.dirname(__file__))
        config_dir = os.path.join(base_dir, 'filebrowser', 'config')
        database_dir = os.path.join(base_dir, 'filebrowser', 'database')
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(database_dir, exist_ok=True)
        
        # 使用工具函数确保容器运行 / Use utility function to ensure container running
        result = ensure_filebrowser_container_running(
            app,
            container_name='filebrowser',
            image=config.FILEBROWSER_IMAGE,
            port=config.FILEBROWSER_PORT,
            data_dir=data_dir,
            config_dir=config_dir,
            database_dir=database_dir,
            base_url=FILEBROWSER_URL
        )
        
        if result:
            # 同步管理员密码 / Sync admin password
            sync_filebrowser_admin()
            return True
        else:
            app.logger.error('确保 filebrowser 运行失败 / Failed to ensure filebrowser is running')
            return False
    except Exception as e:
        app.logger.error(f"确保 filebrowser 运行时出错 / Error ensuring filebrowser is running: {e}")
        return False

# 在 Flask 启动前调用 / Call before Flask startup
ensure_filebrowser_running()

# 管理员修改密码时同步 filebrowser
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password():
    """
    管理员密码修改视图。
    Admin password change view.
    支持GET显示修改页，POST处理修改逻辑。
    Supports GET to display change page, POST to handle change logic.
    密码长度验证：不少于配置中指定的最小长度
    Password length validation: not less than minimum length specified in config
    Returns:
        Response: 修改页或重定向 / Change page or redirect
    """
    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']
        confirm = request.form['confirm_password']
        
        # 密码长度验证 / Password length validation
        if len(new) < config.PASSWORD_MIN_LENGTH:
            flash(_(f'新密码长度不能少于{config.PASSWORD_MIN_LENGTH}位'))
            return render_template('change_password.html')
        
        # 确认密码验证 / Confirm password validation
        if new != confirm:
            flash(_('两次输入的密码不一致'))
            return render_template('change_password.html')
        
        # 验证原密码 / Validate old password
        user = query_db('SELECT * FROM users WHERE id = ?', (current_user.id,), one=True)
        if user and check_password_hash(user[2], old):
            # 更新密码 / Update password
            db = get_db()
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (generate_password_hash(new), current_user.id))
            db.commit()
            
            # 同步 filebrowser 管理员密码 / Sync filebrowser admin password
            # 先获取当前管理员密码
            db = sqlite3.connect(DATABASE)
            cur = db.execute('SELECT password_hash FROM users WHERE username = ?', ('admin',))
            admin_row = cur.fetchone()
            db.close()
            admin_password = new if current_user.username == 'admin' else 'admin'
            
            create_filebrowser_user(app, FILEBROWSER_URL, current_user.username, new, admin_password, is_admin=True)
            if current_user.username == 'admin':
                reset_filebrowser_admin_password(app, 'filebrowser', new, 'admin')
            
            flash(_('密码修改成功'))
            return redirect(url_for('index'))
        else:
            flash(_('原密码错误'))
    return render_template('change_password.html')

@app.route('/api/resource')
def api_resource():
    cpu = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disks = []
    for part in psutil.disk_partitions(all=True):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            if usage.total < 100*1024*1024:
                continue
            disks.append({
                'device': part.device,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            })
        except Exception as e:
            print(f'Error for {part.device}:', e)
            continue
    # RAID信息同前
    raid = []
    import platform
    system = platform.system().lower()
    if system == 'windows':
        try:
            import wmi
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                raid.append({
                    'name': disk.Caption,
                    'level': getattr(disk, 'SCSIBus', ''),
                    'status': disk.Status
                })
        except Exception:
            pass
    else:
        try:
            if os.path.exists('/proc/mdstat'):
                with open('/proc/mdstat') as f:
                    lines = f.readlines()
                for line in lines:
                    if line.startswith('md'):
                        arr = line.split()
                        raid.append({
                            'name': arr[0],
                            'level': arr[3] if len(arr)>3 else '',
                            'status': arr[-1] if arr else ''
                        })
        except Exception:
            pass
    print('disks:', disks)
    return jsonify({
        'cpu': cpu,
        'mem': {
            'percent': mem.percent,
            'used': mem.used,
            'total': mem.total
        },
        'disks': disks,
        'raid': raid
    }) 

# ================= 壁纸管理 API =================
@app.route('/api/upload_wallpaper', methods=['POST'])
@login_required
def api_upload_wallpaper():
    """
    上传新壁纸
    Returns:
        JSON: 包含操作结果的JSON响应
    """
    import os
    import uuid
    from werkzeug.utils import secure_filename

    # 检查是否有文件上传
    if 'wallpaper' not in request.files:
        return jsonify({'status': 'error', 'message': '没有文件上传'})

    file = request.files['wallpaper']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '没有选择文件'})

    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in allowed_extensions:
        return jsonify({'status': 'error', 'message': '不支持的文件类型，仅支持PNG、JPG、JPEG、GIF'})

    # 验证文件大小 (限制5MB)
    if len(file.read()) > 5 * 1024 * 1024:
        return jsonify({'status': 'error', 'message': '文件大小不能超过5MB'})
    # 重置文件指针
    file.seek(0)

    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"

    # 保存文件到壁纸目录
    wallpaper_dir = os.path.join(app.static_folder, 'wallpapers')
    if not os.path.exists(wallpaper_dir):
        os.makedirs(wallpaper_dir)

    file_path = os.path.join(wallpaper_dir, unique_filename)
    try:
        file.save(file_path)
        app.logger.info(f'用户 {current_user.username} 上传了新壁纸: {unique_filename}')
        return jsonify({'status': 'success', 'message': '壁纸上传成功', 'filename': unique_filename})
    except Exception as e:
        app.logger.error(f'上传壁纸失败: {e}')
        return jsonify({'status': 'error', 'message': f'上传失败: {str(e)}'})

@app.route('/api/wallpaper_list')
@login_required
def api_wallpaper_list():
    """
    获取壁纸列表和当前壁纸
    Returns:
        JSON: 包含壁纸列表和当前壁纸的JSON响应
    """
    import os
    # 壁纸目录路径
    wallpaper_dir = os.path.join(app.static_folder, 'wallpapers')
    # 获取壁纸列表
    wallpapers = []
    for file in os.listdir(wallpaper_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            wallpapers.append(file)
    # 获取当前用户的壁纸设置
    # 这里假设从数据库中获取，实际实现可能需要调整
    current_wallpaper = query_db('SELECT wallpaper FROM users WHERE id = ?', (current_user.id,), one=True)
    current_wallpaper = current_wallpaper[0] if current_wallpaper else None
    # 如果当前壁纸不存在于壁纸列表中，则使用默认值
    if current_wallpaper and current_wallpaper not in wallpapers:
        current_wallpaper = wallpapers[0] if wallpapers else None
    return jsonify({
        'wallpapers': wallpapers,
        'current': current_wallpaper
    })

@app.route('/api/set_wallpaper', methods=['POST'])
@login_required
def api_set_wallpaper():
    """
    设置当前壁纸
    Returns:
        JSON: 包含操作结果的JSON响应
    """
    import os
    data = request.json
    wallpaper = data.get('wallpaper')
    # 验证壁纸文件是否存在
    wallpaper_dir = os.path.join(app.static_folder, 'wallpapers')
    if not wallpaper or not os.path.exists(os.path.join(wallpaper_dir, wallpaper)):
        return jsonify({'status': 'error', 'message': '无效的壁纸文件'})
    # 更新用户的壁纸设置
    try:
        db = get_db()
        db.execute('UPDATE users SET wallpaper = ? WHERE id = ?', (wallpaper, current_user.id))
        db.commit()
        return jsonify({'status': 'success', 'message': '壁纸设置成功'})
    except Exception as e:
        app.logger.error(f'设置壁纸失败: {e}')
        return jsonify({'status': 'error', 'message': '设置壁纸失败'})

if __name__ == '__main__':
    init_db()  # 初始化数据库和管理员 / Initialize database and admin
    app.run(
        host=config.APP_HOST, 
        port=config.APP_PORT, 
        debug=config.APP_DEBUG
    )  # 启动应用服务器 / Start application server
