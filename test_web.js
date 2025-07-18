// test_web.js
// 嵌入式轻NAS管理软件前端自动化测试脚本
// Frontend E2E test script for Embedded Lite NAS Management Software
//
// 覆盖登录、首页、应用商店、用户管理、文件管理器、国际化等主要页面和流程
// 所有测试用例均有详细中英文注释，便于团队维护

const { test, expect } = require('@playwright/test');

// 测试登录流程和首页展示
// Test login flow and homepage display
// 步骤：访问登录页，输入账号密码，点击登录，检查首页内容
// Steps: visit login page, input credentials, click login, check homepage content
test('登录流程和首页展示', async ({ page }) => {
  // 访问登录页 Visit login page
  await page.goto('http://localhost:5000/login');
  // 输入用户名 Fill username
  await page.fill('input[name="username"]', 'admin');
  // 输入密码 Fill password
  await page.fill('input[name="password"]', 'admin123456789');
  // 点击登录 Click login button
  await page.click('button[type=submit]');
  // 检查首页内容 Check homepage content
  await expect(page).toHaveURL(/.*index.*/);
  await expect(page.locator('#cpu-val')).toBeVisible();
});

// 测试应用商店页面可访问
// Test app store page accessibility
test('应用商店页面可访问', async ({ page }) => {
  // 需先登录 Login first
  await page.goto('http://localhost:5000/login');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123456789');
  await page.click('button[type=submit]');
  // 跳转到应用商店 Go to app store page
  await page.goto('http://localhost:5000/appstore');
  // 检查页面包含APP文本 Check page contains APP text
  await expect(page.locator('text=APP')).toBeVisible();
});

// 测试用户管理页面增删查
// Test user management page add/delete/query
// 步骤：登录，进入用户管理，新增用户，删除用户
// Steps: login, enter user management, add user, delete user
test('用户管理页面增删查', async ({ page }) => {
  // 登录 Login
  await page.goto('http://localhost:5000/login');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123456789');
  await page.click('button[type=submit]');
  // 跳转用户管理 Go to user management
  await page.goto('http://localhost:5000/users');
  // 检查用户表格 Check user table
  await expect(page.locator('text=用户')).toBeVisible();
  // 新增用户 Add user
  await page.fill('input[name="username"]', 'testuser2');
  await page.fill('input[name="password"]', 'testpass2');
  await page.click('button[type=submit]');
  await expect(page.locator('text=testuser2')).toBeVisible();
  // 删除用户 Delete user
  await page.click(`button[data-username="testuser2"][data-action="delete"]`);
  await expect(page.locator('text=testuser2')).not.toBeVisible();
});

// 测试文件管理器自动登录入口
// Test file manager auto-login entry
test('文件管理器自动登录入口', async ({ page }) => {
  // 登录 Login
  await page.goto('http://localhost:5000/login');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123456789');
  await page.click('button[type=submit]');
  // 跳转文件管理器自动登录页 Go to file manager auto-login page
  await page.goto('http://localhost:5000/filemanager_auto_login');
  // 检查filebrowser页面元素 Check filebrowser page element
  await expect(page.locator('text=File Browser')).toBeVisible();
});

// 测试国际化切换
// Test i18n (language) switch
test('国际化切换', async ({ page }) => {
  await page.goto('http://localhost:5000/login');
  // 切换到英文 Switch to English
  await page.click('button#lang-en');
  await expect(page.locator('text=Login')).toBeVisible();
  // 切换回中文 Switch back to Chinese
  await page.click('button#lang-zh');
  await expect(page.locator('text=登录')).toBeVisible();
});