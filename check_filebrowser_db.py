import sqlite3
import os
import struct

# 数据库文件路径
db_path = r'd:\aiCoding\dockerManager\filebrowser\database\filebrowser.db'

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

# 检查文件是否为有效的SQLite数据库
try:
    with open(db_path, 'rb') as f:
        header = f.read(16)
        # SQLite数据库文件头部应该以"SQLite format 3"开头
        if header[:16] != b'SQLite format 3\x00':
            print(f"文件 {db_path} 不是有效的SQLite数据库")
            exit(1)
        else:
            print(f"文件 {db_path} 是有效的SQLite数据库")

except Exception as e:
    print(f"检查文件格式时出错: {str(e)}")
    exit(1)

try:
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    if tables:
        print("数据库中的表:")
        for table in tables:
            print(f"- {table[0]}")

        # 检查是否有用户表
        user_table_exists = any(table[0] == 'users' for table in tables)
        if user_table_exists:
            print("\n用户表存在，查询用户信息:")
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()

            if users:
                print("ID | 用户名 | 密码哈希")
                print("-" * 60)
                for user in users:
                    print(f"{user[0]} | {user[1]} | {user[2]}")
            else:
                print("用户表为空")
        else:
            print("\n用户表不存在")
    else:
        print("数据库中没有表")

    # 关闭连接
    conn.close()

except Exception as e:
    print(f"查询数据库时出错: {str(e)}")
    # 打印异常的详细信息
    import traceback
    traceback.print_exc()