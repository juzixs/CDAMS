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

## 环境要求

- Python 3.11+
- pip
- Git

## 部署指南

### 1. 克隆项目

```bash
git clone https://github.com/juzixs/CDAMS.git
cd CDAMS
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/MacOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件并添加以下内容：

```plaintext
SECRET_KEY=your-secret-key-here
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db
```

### 5. 初始化数据库

```bash
# 初始化数据库迁移环境
flask db init

# 创建首次迁移
flask db migrate -m "Initial migration"

# 应用迁移并创建数据库表
python init_db.py

# 初始化管理员账号
python init_admin.py
```

如果之后需要更新数据库结构，请使用以下命令：

```bash
# 创建新的迁移（在修改模型后）
flask db migrate -m "描述此次变更"

# 应用迁移
flask db upgrade
```

### 6. 启动应用

```bash
# 开发环境
flask run --host=0.0.0.0 --port=5000

# 生产环境
# 仅本机访问
gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app

# 局域网访问（将 YOUR_IP 替换为服务器IP）
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# 如果需要指定工作目录和日志
gunicorn -w 4 -b 0.0.0.0:5000 --chdir /path/to/your/app --access-logfile access.log --error-logfile error.log wsgi:app
```

访问方式：
- 本机访问：http://127.0.0.1:5000
- 局域网访问：http://YOUR_IP:5000（将 YOUR_IP 替换为服务器实际IP地址）

**注意事项：**
1. 使用 0.0.0.0 绑定地址时，请确保防火墙已开放对应端口（默认5000）
2. 生产环境建议配置反向代理（如 Nginx）并启用 HTTPS
3. 可以根据服务器配置调整 gunicorn 的工作进程数（-w 参数）

## 初始管理员账号

完成上述步骤后，可使用以下默认管理员账号登录系统：

- 用户名：admin
- 密码：admin
- 邮箱：admin@chidafeiji.com

**注意：** 首次登录后请立即修改默认密码！

## 常见问题

### 数据库初始化失败

如果遇到数据库初始化失败，请检查：
1. 确保已安装所有依赖包
2. 检查数据库文件权限
3. 确保 `.env` 文件中的 `DATABASE_URL` 配置正确
4. 检查 migrations 文件夹是否存在且权限正确

### 数据库迁移问题

如果遇到数据库迁移相关问题：
1. 确保 migrations 文件夹存在且完整
2. 如果迁移失败，可以尝试删除 migrations 文件夹和数据库文件，重新执行初始化步骤
3. 在应用迁移前，建议备份数据库
4. 检查迁移脚本是否有冲突

### 访问问题

如果遇到访问相关问题：
1. 确保服务正在运行且端口未被占用
2. 检查防火墙设置是否允许对应端口的访问
3. 验证服务器IP地址是否正确
4. 如果使用反向代理，检查代理配置是否正确

### 管理员账号创建失败

如果遇到管理员账号创建失败，请检查：
1. 确保数据库已正确初始化
2. 检查数据库连接是否正常
3. 确保没有重复运行初始化脚本

## 安全提示

1. 部署到生产环境前请修改所有默认密码
2. 确保 `.env` 文件不被提交到版本控制系统
3. 生产环境建议使用更安全的数据库系统（如MySQL/PostgreSQL）
4. 建议启用HTTPS保护传输安全
5. 定期备份数据库和迁移文件
6. 限制生产环境的IP访问范围
7. 配置防火墙规则保护服务器安全

## 数据库维护

### 备份

建议定期备份以下内容：
1. 数据库文件（app.db）
2. migrations 文件夹
3. .env 配置文件

### 版本控制

- 将数据库迁移文件（migrations文件夹）纳入版本控制
- 不要将数据库文件和.env文件提交到版本控制系统

### 数据库升级

在升级系统版本时：
1. 先备份数据库和迁移文件
2. 拉取最新代码
3. 执行 `flask db upgrade` 更新数据库结构
4. 测试系统功能
