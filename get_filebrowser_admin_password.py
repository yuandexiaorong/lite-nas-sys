import re
import subprocess
import sys

def get_filebrowser_admin_password(container_name):
    """
    获取FileBrowser容器初始化时生成的管理员密码
    """
    try:
        print(f"正在获取FileBrowser容器 '{container_name}' 的管理员密码...")
        # 获取容器日志
        logs_result = subprocess.run([
            "docker", "logs", container_name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)

        if logs_result.returncode != 0:
            print(f"获取容器日志失败: {logs_result.stderr}")
            return None

        # 从日志中提取管理员密码
        log_content = logs_result.stdout
        # 使用更宽松的正则表达式模式
        patterns = [
            r'User \'admin\' initialized with randomly generated password: (\w+)',
            r'admin password: (\w+)',
            r'password for admin: (\w+)',
            r'admin: (\w+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, log_content)
            if match:
                admin_password = match.group(1)
                print(f"找到管理员密码: {admin_password}")
                print("用户名: admin")
                return admin_password

        print("未在日志中找到管理员密码")
        return None
    except Exception as e:
        print(f"获取管理员密码时出错: {str(e)}")
        return None

if __name__ == "__main__":
    # 默认参数
    container_name = "filebrowser"

    # 获取管理员密码
    get_filebrowser_admin_password(container_name)