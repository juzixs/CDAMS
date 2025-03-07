# CHIDA行政管理系统 (CDAMS)

[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)

## 项目简介

CDAMS（CHIDA行政管理系统）是一个公司行政管理平台。

## 技术栈

- **后端框架**：Flask
- **数据库**：SQLite（可扩展至MySQL/PostgreSQL）
- **前端框架**：Bootstrap 5
- **图标库**：Font Awesome
- **表单处理**：Flask-WTF
- **用户认证**：Flask-Login
- **数据库迁移**：Flask-Migrate

## 核心特性

- **权限分级管理**：三级权限结构 (普通级、授权级、管理级)
- **用户认证与授权**：安全的登录系统与模块访问权限控制
- **响应式界面设计**：适配各种设备屏幕尺寸
- **动态导航菜单**：根据用户权限动态显示功能模块
- **数据导入导出**：支持Excel格式数据批量处理
- **文档生成能力**：自动生成PDF格式报表和证件


### 环境要求
- Python 3.11+
- pip