#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用商店管理功能测试脚本
Test script for app store management functionality
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123456789"

def login():
    """登录获取会话"""
    session = requests.Session()
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✅ 登录成功")
        return session
    else:
        print("❌ 登录失败")
        return None

def test_get_apps(session):
    """测试获取APP列表"""
    print("\n=== 测试获取APP列表 ===")
    response = session.get(f"{BASE_URL}/api/get_apps")
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print(f"✅ 获取APP列表成功，共 {len(data['apps'])} 个APP")
            return data['apps']
        else:
            print(f"❌ 获取APP列表失败: {data.get('message', '未知错误')}")
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
    return []

def test_add_app(session):
    """测试添加APP"""
    print("\n=== 测试添加APP ===")
    app_data = {
        "name": "TestApp",
        "image": "nginx:alpine",
        "icon": "bi-gear",
        "description": "这是一个测试APP",
        "category_zh": "测试",
        "category_en": "Test",
        "default_ports": {"80/tcp": 8080},
        "env": ["TEST_VAR=test_value"],
        "volumes": ["/data/testapp:/app/data"]
    }
    
    response = session.post(f"{BASE_URL}/api/add_app", 
                           json=app_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print("✅ 添加APP成功")
            return True
        else:
            print(f"❌ 添加APP失败: {data.get('message', '未知错误')}")
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
    return False

def test_update_app(session):
    """测试更新APP"""
    print("\n=== 测试更新APP ===")
    app_data = {
        "name": "TestApp",
        "image": "nginx:latest",
        "icon": "bi-cloud",
        "description": "这是更新后的测试APP",
        "category_zh": "测试更新",
        "category_en": "Test Updated",
        "default_ports": {"80/tcp": 8081},
        "env": ["TEST_VAR=updated_value"],
        "volumes": ["/data/testapp:/app/data"]
    }
    
    response = session.post(f"{BASE_URL}/api/update_app", 
                           json=app_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print("✅ 更新APP成功")
            return True
        else:
            print(f"❌ 更新APP失败: {data.get('message', '未知错误')}")
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
    return False

def test_delete_app(session):
    """测试删除APP"""
    print("\n=== 测试删除APP ===")
    app_data = {"name": "TestApp"}
    
    response = session.post(f"{BASE_URL}/api/delete_app", 
                           json=app_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print("✅ 删除APP成功")
            return True
        else:
            print(f"❌ 删除APP失败: {data.get('message', '未知错误')}")
    else:
        print(f"❌ 请求失败，状态码: {response.status_code}")
    return False

def main():
    """主测试函数"""
    print("🚀 开始测试应用商店管理功能")
    
    # 登录
    session = login()
    if not session:
        return
    
    # 获取APP列表
    apps = test_get_apps(session)
    
    # 添加APP
    if test_add_app(session):
        # 验证添加结果
        apps_after_add = test_get_apps(session)
        if len(apps_after_add) > len(apps):
            print("✅ APP添加验证成功")
        else:
            print("❌ APP添加验证失败")
    
    # 更新APP
    test_update_app(session)
    
    # 删除APP
    if test_delete_app(session):
        # 验证删除结果
        apps_after_delete = test_get_apps(session)
        if len(apps_after_delete) == len(apps):
            print("✅ APP删除验证成功")
        else:
            print("❌ APP删除验证失败")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main() 