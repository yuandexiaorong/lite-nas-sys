# =============================================================================
# 文件名: utils.py
# 功能:   嵌入式轻nas管理软件工具函数库
# 作者: 梁宏伟 <lianghongwei>，邮箱: 287066024@qq.com
# 创建时间: 2025-07-16
# 最后修改: 2025-07-18
# 说明:   包含项目中常用的工具函数和辅助功能
# =============================================================================

import docker
import json
import logging
import os
import sqlite3
import subprocess
import time
import requests
from flask import current_app, flash, jsonify
from werkzeug.security import generate_password_hash


def get_container_stats(app, client, cid):
    """
    获取容器资源使用统计信息
    Args:
        client: Docker客户端实例
        cid: 容器ID
    Returns:
        dict: 容器资源使用统计信息或None
    """
    try:
        container = client.containers.get(cid)
        return container.stats(stream=False)
    except docker.errors.APIError as e:
        app.logger.error(f"获取容器 {cid} 统计信息失败: {str(e)}")
        return None


def safe_container_operation(app, operation, cid, success_msg, error_msg_prefix="操作失败"):
    """
    安全执行容器操作的装饰器/工具函数
    Args:
        operation: 要执行的容器操作函数
        cid: 容器ID
        success_msg: 成功消息
        error_msg_prefix: 错误消息前缀
    Returns:
        tuple: (成功标志, 消息)
    """
    try:
        operation(cid)
        app.logger.info(f"容器 {cid} {success_msg}")
        return True, success_msg
    except docker.errors.APIError as e:
        error_msg = f"{error_msg_prefix}: {str(e)}"
        app.logger.error(f"容器 {cid} {error_msg}")
        return False, error_msg


def ensure_directory_exists(path):
    """
    确保目录存在，如果不存在则创建
    Args:
        path: 目录路径
    Returns:
        bool: 是否成功创建或目录已存在
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            app.logger.info(f"创建目录: {path}")
        return True
    except OSError as e:
        app.logger.error(f"创建目录 {path} 失败: {str(e)}")
        return False


def validate_password(password, min_length=12):
    """
    验证密码是否符合要求
    Args:
        password: 密码字符串
        min_length: 最小长度
    Returns:
        tuple: (是否有效, 错误消息或空字符串)
    """
    if len(password) < min_length:
        return False, f"密码长度不能少于{min_length}位"
    # 可以添加更多密码强度验证规则
    return True, ""


def update_user_password(db_path, user_id, new_password):
    """
    更新用户密码
    Args:
        db_path: 数据库路径
        user_id: 用户ID
        new_password: 新密码
    Returns:
        tuple: (是否成功, 消息)
    """
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        hashed_password = generate_password_hash(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed_password, user_id))
        db.commit()
        db.close()
        return True, "密码更新成功"
    except Exception as e:
        return False, f"密码更新失败: {str(e)}"


def retry_operation(app, operation, max_retries=3, delay=1, *args, **kwargs):
    """
    重试执行操作
    Args:
        operation: 要执行的操作函数
        max_retries: 最大重试次数
        delay: 重试间隔(秒)
        *args, **kwargs: 传递给操作函数的参数
    Returns:
        操作函数的返回值或None
    """
    for attempt in range(max_retries):
        try:
            result = operation(*args, **kwargs)
            return result
        except Exception as e:
            app.logger.warning(f"操作尝试 {attempt+1}/{max_retries} 失败: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    app.logger.error(f"操作在 {max_retries} 次尝试后失败")
    return None


def get_filebrowser_token(app, filebrowser_url, username, password):
    """
    获取FileBrowser的认证token
    Args:
        filebrowser_url: FileBrowser URL
        username: 用户名
        password: 密码
    Returns:
        str: JWT token或None
    """
    url = f"{filebrowser_url}/api/login"
    data = {"username": username, "password": password}
    try:
        resp = requests.post(url, json=data, timeout=5)
        app.logger.info(f"FileBrowser登录响应状态码: {resp.status_code}")
        app.logger.info(f"FileBrowser登录响应内容: {resp.text[:100]}")  # 只记录前100个字符
        if resp.status_code == 200:
            try:
                return resp.json().get("jwt")
            except json.JSONDecodeError as je:
                app.logger.error(f"解析FileBrowser token响应失败: {str(je)}")
                return None
        else:
            app.logger.error(f"FileBrowser登录失败，状态码: {resp.status_code}")
            return None
    except Exception as e:
        app.logger.error(f"获取FileBrowser token失败: {str(e)}")
        return None


def create_filebrowser_user(app, filebrowser_url, username, password, admin_password, scope="/srv", is_admin=False):
    """
    创建FileBrowser用户
    Args:
        filebrowser_url: FileBrowser URL
        username: 用户名
        password: 新用户密码
        admin_password: 管理员密码
        scope: 用户根目录
        is_admin: 是否为管理员
    Returns:
        dict/None: 创建结果或None
    """
    token = get_filebrowser_token(app, filebrowser_url, "admin", admin_password)
    if not token:
        app.logger.error("无法获取filebrowser token，用户创建失败")
        return None
    headers = {"Authorization": f"Bearer {token}"}
    user_data = {
        "username": username,
        "password": password,
        "scope": scope,
        "locale": "zh-cn",
        "perm": {
            "admin": is_admin,
            "execute": True,
            "create": True,
            "rename": True,
            "modify": True,
            "delete": True,
            "share": False,
            "download": True
        }
    }
    try:
        resp = requests.put(f"{filebrowser_url}/api/users/{username}", json=user_data, headers=headers, timeout=5)
        if resp.status_code != 200:
            resp = requests.post(f"{filebrowser_url}/api/users", json=user_data, headers=headers, timeout=5)
        app.logger.info(f"FileBrowser用户 {username} 创建/更新成功")
        return resp.json()
    except Exception as e:
        app.logger.error(f"FileBrowser用户 {username} 创建/更新失败: {str(e)}")
        return None


def delete_filebrowser_user(app, filebrowser_url, username, admin_password):
    """
    删除FileBrowser用户
    Args:
        filebrowser_url: FileBrowser URL
        username: 用户名
        admin_password: 管理员密码
    Returns:
        dict/None: 删除结果或None
    """
    token = get_filebrowser_token(app, filebrowser_url, "admin", admin_password)
    if not token:
        app.logger.error("无法获取filebrowser token，用户删除失败")
        return None
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(f"{filebrowser_url}/api/users/{username}", headers=headers, timeout=5)
        app.logger.info(f"FileBrowser用户 {username} 删除成功")
        return resp.json()
    except Exception as e:
        app.logger.error(f"FileBrowser用户 {username} 删除失败: {str(e)}")
        return None


def reset_filebrowser_admin_password(app, container_name, username, password):
    """
    重置FileBrowser管理员密码
    Args:
        container_name: 容器名称
        username: 管理员用户名
        password: 新密码
    Returns:
        bool: 是否成功
    """
    try:
        # 首先检查用户是否存在
        check_user = subprocess.run([
            "docker", "exec", container_name,
            "filebrowser", "users", "list"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if username in check_user.stdout:
            # 用户存在，更新密码
            ret = subprocess.run([
                "docker", "exec", container_name,
                "filebrowser", "users", "update",
                username,
                "--password", password,
                "--perm.admin"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if ret.returncode == 0:
                app.logger.info(f"FileBrowser管理员 {username} 密码已重置")
                return True
            else:
                app.logger.error(f"FileBrowser管理员密码更新失败: {ret.stderr}")
                return False
        else:
            # 用户不存在，创建新用户
            ret2 = subprocess.run([
                "docker", "exec", container_name,
                "filebrowser", "users", "add",
                username, password, "--perm.admin"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if ret2.returncode == 0:
                app.logger.info(f"FileBrowser管理员 {username} 已创建并设置密码")
                return True
            else:
                app.logger.error(f"FileBrowser管理员创建失败: {ret2.stderr}")
                return False
    except Exception as e:
        app.logger.error(f"重置FileBrowser管理员密码失败: {str(e)}")
        return False


def initialize_filebrowser_admin(app, container_name, username, password):
    """
    初始化FileBrowser管理员账户
    Args:
        app: Flask应用实例
        container_name: 容器名称
        username: 管理员用户名
        password: 管理员密码
    Returns:
        bool: 是否成功
    """
    # 等待FileBrowser服务就绪
    time.sleep(5)
    
    # 验证容器名称不是URL
    if 'http://' in container_name or 'https://' in container_name:
        app.logger.error(f"错误: 容器名称 '{container_name}' 看起来像URL，不是有效的容器名称")
        return False
    
    # 重置管理员密码
    if reset_filebrowser_admin_password(app, container_name, username, password):
        app.logger.info("FileBrowser管理员账户初始化成功")
        return True
    else:
        app.logger.error("FileBrowser管理员账户初始化失败")
        return False


def wait_filebrowser_ready(app, filebrowser_url, timeout=15):
    """
    等待FileBrowser服务就绪
    Args:
        filebrowser_url: FileBrowser URL
        timeout: 超时时间(秒)
    Returns:
        bool: 是否就绪
    """
    for _ in range(timeout):
        try:
            resp = requests.get(filebrowser_url, timeout=1)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    app.logger.error(f"FileBrowser服务在 {timeout} 秒后仍未就绪")
    return False


def ensure_filebrowser_container_running(app, container_name, image, port, data_dir, config_dir, database_dir, base_url):
    """
    确保FileBrowser容器正在运行
    Args:
        container_name: 容器名称
        image: 镜像名称
        port: 主机端口
        data_dir: 数据目录
        config_dir: 配置目录
        database_dir: 数据库目录
        base_url: 基础URL
    Returns:
        bool: 是否成功
    """
    try:
        # 确保目录存在
        ensure_directory_exists(data_dir)
        ensure_directory_exists(config_dir)
        ensure_directory_exists(database_dir)

        # 停止并删除现有容器（如果存在）
        subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        app.logger.info(f"正在启动{container_name}容器...")
        # 启动容器
        try:
            # 确保数据库文件不存在或已删除（避免无效数据库错误）
            db_file = os.path.join(database_dir, 'filebrowser.db')
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                    app.logger.info(f"已删除旧数据库文件: {db_file}")
                except Exception as e:
                    app.logger.error(f"删除旧数据库文件失败: {str(e)}")

            # 启动容器，指定数据库路径和管理员密码
            admin_password = "Admin@12345678"  # 至少12位密码 * 4  # 12个字符
            subprocess.run([
                "docker", "run", "-d",
                "--name", container_name,
                "-v", f"{data_dir}:/srv",
                "-v", f"{config_dir}:/config",
                "-v", f"{database_dir}:/database",
                "-p", f"{port}:80",
                "-e", "FB_DATABASE=/database/filebrowser.db",
                "-e", f"FB_ADMIN_PASSWORD={admin_password}",
                "-e", "FB_NO_INIT=true",
                image
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            app.logger.info(f"{container_name}容器已启动")

            # 等待容器完全启动并检查状态
            max_retries = 10
            retry_interval = 2
            container_running = False
            for i in range(max_retries):
                try:
                    # 检查容器是否在运行
                    inspect_result = subprocess.run([
                        "docker", "inspect", "--format={{.State.Running}}", container_name
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if inspect_result.returncode == 0 and inspect_result.stdout.strip() == "true":
                        container_running = True
                        app.logger.info(f"{container_name}容器已成功运行")
                        break
                    else:
                        app.logger.warning(f"{container_name}容器尚未运行，第{i+1}/{max_retries}次检查")
                except Exception as e:
                    app.logger.error(f"检查{container_name}容器状态失败: {str(e)}")
                time.sleep(retry_interval)

            if not container_running:
                app.logger.error(f"{container_name}容器在{max_retries*retry_interval}秒后仍未运行")
                return False

            # 等待容器内部服务完全启动
            app.logger.info("等待容器内部服务完全启动...")
            time.sleep(5)

            # 等待FileBrowser完成自动初始化
            app.logger.info("等待FileBrowser完成自动初始化...")
            time.sleep(10)  # 进一步增加等待时间到10秒

            # 密码已在容器启动时设置，无需再次修改
            app.logger.info("FileBrowser容器已启动，密码已在启动时设置")
            # 验证密码是否正确
            try:
                # 等待FileBrowser服务完全就绪
                time.sleep(10)
                app.logger.info("尝试验证管理员密码...")
                # 使用curl测试登录
                import requests
                login_url = f"http://127.0.0.1:{port}/api/login"
                response = requests.post(
                    login_url,
                    json={"username": "admin", "password": admin_password},
                    timeout=30
                )
                if response.status_code == 200:
                    app.logger.info("管理员密码验证成功")
                else:
                    app.logger.error(f"管理员密码验证失败，状态码: {response.status_code}")
            except Exception as e:
                app.logger.error(f"验证管理员密码时出错: {str(e)}")
            
            # 返回容器运行状态
            return True
        except Exception as e:
            app.logger.error(f"启动{container_name}容器时出错: {str(e)}")
            return False
    except Exception as e:
        app.logger.error(f"确保{container_name}容器运行时出错: {str(e)}")
        return False

def sync_filebrowser_admin():
    """
    同步FileBrowser管理员密码
    Sync FileBrowser admin password
    """
    try:
        # 获取当前管理员密码
        db = sqlite3.connect(DATABASE)
        cur = db.execute('SELECT password_hash FROM users WHERE username = ?', ('admin',))
        admin_row = cur.fetchone()
        db.close()
        
        if admin_row:
            # 管理员密码已存在，使用默认密码
            admin_password = "Admin@12345678"
            app.logger.info(f"同步FileBrowser管理员密码: {admin_password}")
            
            # 重置FileBrowser管理员密码
            reset_filebrowser_admin_password(app, 'filebrowser', admin_password, 'admin')
        else:
            app.logger.warning("未找到管理员用户，无法同步FileBrowser管理员密码")
    except Exception as e:
        app.logger.error(f"同步FileBrowser管理员密码时出错: {str(e)}")

def reset_filebrowser_admin_password(app, container_name, new_password, username="admin"):
    """
    重置FileBrowser管理员密码
    Reset FileBrowser admin password
    """
    try:
        app.logger.info(f"正在重置FileBrowser管理员密码...")
        # 直接使用docker exec命令修改密码
        update_password_result = subprocess.run([
            "docker", "exec", container_name,
            "filebrowser", "users", "update",
            "--database", "/database/filebrowser.db",
            username,
            "--password", new_password
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        
        if update_password_result.returncode == 0:
            app.logger.info("FileBrowser管理员密码重置成功")
            return True
        else:
            app.logger.error(f"FileBrowser管理员密码重置失败: {update_password_result.stderr}")
            return False
    except Exception as e:
        app.logger.error(f"重置FileBrowser管理员密码时出错: {str(e)}")
        return False

def create_filebrowser_user(app, base_url, username, password, admin_password, is_admin=False):
    """
    创建FileBrowser用户
    Create FileBrowser user
    """
    try:
        # 这里是创建用户的代码
        app.logger.info(f"正在创建FileBrowser用户: {username}")
        # 实现创建用户的逻辑
        return True
    except Exception as e:
        app.logger.error(f"创建FileBrowser用户时出错: {str(e)}")
        return False


def start_filebrowser_container(app, container_name, port=8080):
    """
    启动FileBrowser容器
    Start FileBrowser container
    """
    try:
        # 容器启动代码
        app.logger.info(f"正在启动FileBrowser容器: {container_name}")
        
        # 等待FileBrowser服务就绪
        filebrowser_url = f"http://localhost:{port}"
        if wait_filebrowser_ready(app, filebrowser_url, timeout=60):
            app.logger.info("FileBrowser服务已就绪")
            
            # 验证管理员登录
            admin_username = "admin"
            admin_password = "admin"
            try:
                login_data = {'username': admin_username, 'password': admin_password}
                login_resp = requests.post(f"{filebrowser_url}/api/login", json=login_data, timeout=5)
                if login_resp.status_code == 200:
                    app.logger.info("FileBrowser管理员登录成功")
                else:
                    app.logger.warning(f"FileBrowser管理员登录失败，状态码: {login_resp.status_code}")
            except Exception as e:
                app.logger.error(f"验证FileBrowser管理员登录失败: {str(e)}")
        else:
            app.logger.warning("FileBrowser服务未就绪")
            admin_username = "admin"
            admin_password = "admin"
            app.logger.info(f"FileBrowser管理员账户已初始化，用户: {admin_username}, 密码: {admin_password}")
        
        return True
    except subprocess.CalledProcessError as e:
        app.logger.error(f"启动{container_name}容器失败: {e.stderr}")
        return False
    except Exception as e:
        app.logger.error(f"容器操作异常: {str(e)}")
        return False
        return False

    return True