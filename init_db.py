import os
import subprocess
import sys

def run_command(command):
    """运行命令并打印输出"""
    print(f"执行命令: {command}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        universal_newlines=True
    )
    
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    if process.returncode != 0:
        print(f"命令执行失败，返回码: {process.returncode}")
        return False
    return True

def main():
    """主函数，执行数据库初始化和创建管理员账号"""
    print("=== 开始初始化数据库和创建管理员账号 ===")
    
    # 检查是否在虚拟环境中
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("警告: 未检测到虚拟环境，建议在虚拟环境中运行此脚本")
        response = input("是否继续? (y/n): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    # 初始化数据库
    if not run_command("flask init-db"):
        print("数据库初始化失败")
        return
    
    # 创建管理员账号
    if not run_command("flask create-admin"):
        print("创建管理员账号失败")
        return
    
    # 询问是否创建测试数据
    response = input("是否创建测试数据? (y/n): ")
    if response.lower() == 'y':
        if not run_command("flask create-test-data"):
            print("创建测试数据失败")
            return
    
    print("\n=== 初始化完成 ===")
    print("现在您可以使用以下命令启动应用:")
    print("flask run")

if __name__ == "__main__":
    main() 