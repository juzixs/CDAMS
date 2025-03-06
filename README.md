# 行政管理系统

这是一个基于 Flask 的行政管理系统，包含用户管理、车辆管理等功能。

## 功能特点

- 用户管理：注册、登录、个人资料管理
- 车辆管理：车牌申请、审批、查询
- 系统设置：PDF 生成设置等

## 安装指南

### 环境要求

- Python 3.8+
- pip
- 虚拟环境（推荐）

### 安装步骤

1. 克隆代码库

```bash
git clone <repository-url>
cd xingzhengsys
```

2. 创建并激活虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 设置环境变量

```bash
# Windows
set FLASK_APP=app
set FLASK_ENV=development

# Linux/Mac
export FLASK_APP=app
export FLASK_ENV=development
```

## 数据库初始化

### 方法一：使用初始化脚本（推荐）

运行初始化脚本，一键完成数据库初始化和管理员账号创建：

```bash
python init_db.py
```

### 方法二：使用 Flask 命令

1. 初始化数据库

```bash
flask init-db
```

2. 创建管理员账号

```bash
flask create-admin
```

3. （可选）创建测试数据

```bash
flask create-test-data
```

## 启动应用

```bash
flask run
```

应用将在 http://127.0.0.1:5000/ 运行。

## 默认管理员账号

- 用户名：admin
- 密码：admin123
- 邮箱：admin@example.com

## 数据库结构

### 用户表 (users)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | Integer | 主键 |
| username | String | 用户名，唯一 |
| email | String | 邮箱，唯一 |
| password_hash | String | 密码哈希 |
| employee_id | String | 工号，唯一 |
| name | String | 姓名 |
| department | String | 部门 |
| phone | String | 电话 |
| is_admin | Boolean | 是否管理员 |

### 车辆表 (vehicle)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | Integer | 主键 |
| plate_number | String | 车牌号，唯一 |
| vehicle_type | String | 车辆类型 |
| owner_name | String | 车主姓名 |
| department | String | 部门 |
| remarks | Text | 备注信息 |
| status | String | 状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| issued_at | DateTime | 发放时间 |
| user_id | Integer | 用户ID，外键 |

### PDF设置表 (pdf_settings)

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | Integer | 主键 |
| module | String | 模块名称 |
| background_image | String | 背景图路径 |
| font_family | String | 字体 |
| font_size | Integer | 字体大小 |
| font_bold | Boolean | 是否加粗 |
| text_x | Integer | 文字X坐标 |
| text_y | Integer | 文字Y坐标 |
| text_color | String | 文字颜色 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 | 