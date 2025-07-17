#!/usr/bin/env python3
"""
用户密码管理工具

提供用户密码重置、用户创建和用户列表查看功能。
支持通过命令行参数或交互式方式操作。
"""

import sys
import os
import argparse
from typing import Optional, Tuple
from contextlib import contextmanager

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from config.database import SessionLocal
from models.user import User
from utils.security import get_password_hash

# ==================== 配置常量 ====================
class Config:
    """配置常量类"""
    
    # 默认用户配置
    DEFAULT_USERNAME = "test"
    DEFAULT_PASSWORD = "123456"
    DEFAULT_EMAIL = "test@example.com"
    DEFAULT_FULL_NAME = "Test User"
    
    # 显示格式配置
    SEPARATOR_LENGTH = 60
    TITLE_SEPARATOR_LENGTH = 50
    USERNAME_COLUMN_WIDTH = 15
    EMAIL_COLUMN_WIDTH = 25
    ID_COLUMN_WIDTH = 3
    
    # 状态文本
    STATUS_ACTIVE = "激活"
    STATUS_INACTIVE = "未激活"
    
    # 消息文本
    class Messages:
        TOOL_TITLE = "用户密码管理工具"
        USER_NOT_FOUND = "❌ 用户 '{username}' 不存在"
        PASSWORD_RESET_SUCCESS = "✅ 用户 '{username}' 的密码已成功重置"
        PASSWORD_RESET_ERROR = "❌ 重置密码时出错: {error}"
        USER_CREATE_SUCCESS = "✅ 用户 '{username}' 创建成功"
        USER_CREATE_ERROR = "❌ 创建用户时出错: {error}"
        USER_EXISTS = "用户 '{username}' 已存在，无需创建"
        QUERY_ERROR = "❌ 查询用户时出错: {error}"
        NO_USERS = "数据库中没有用户"
        OPERATION_COMPLETE = "🎉 操作完成！"
        LOGIN_HINT = "现在您可以使用这个密码登录系统了。"

# ==================== 数据库会话管理 ====================
@contextmanager
def get_db_session():
    """数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ==================== 核心功能函数 ====================
def reset_user_password(username: str, new_password: str) -> bool:
    """
    重置指定用户的密码
    
    Args:
        username: 用户名
        new_password: 新密码
        
    Returns:
        bool: 操作是否成功
    """
    with get_db_session() as db:
        try:
            # 查找用户
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(Config.Messages.USER_NOT_FOUND.format(username=username))
                return False
            
            # 显示用户信息
            _display_user_info(user)
            
            # 生成新密码的哈希值并更新
            user.password_hash = get_password_hash(new_password)
            db.commit()
            
            print(Config.Messages.PASSWORD_RESET_SUCCESS.format(username=username))
            return True
            
        except Exception as e:
            print(Config.Messages.PASSWORD_RESET_ERROR.format(error=e))
            return False

def create_user(username: str, password: str, email: str, full_name: str) -> bool:
    """
    创建新用户
    
    Args:
        username: 用户名
        password: 密码
        email: 邮箱
        full_name: 全名
        
    Returns:
        bool: 操作是否成功
    """
    with get_db_session() as db:
        try:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                print(Config.Messages.USER_EXISTS.format(username=username))
                return True
            
            # 创建新用户
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=get_password_hash(password),
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            
            print(Config.Messages.USER_CREATE_SUCCESS.format(username=username))
            _display_user_credentials(username, password, email)
            return True
            
        except Exception as e:
            print(Config.Messages.USER_CREATE_ERROR.format(error=e))
            return False

def list_all_users() -> None:
    """列出所有用户"""
    with get_db_session() as db:
        try:
            users = db.query(User).all()
            
            if not users:
                print(Config.Messages.NO_USERS)
                return
            
            _display_users_table(users)
            
        except Exception as e:
            print(Config.Messages.QUERY_ERROR.format(error=e))

# ==================== 显示辅助函数 ====================
def _display_user_info(user: User) -> None:
    """显示用户详细信息"""
    status = Config.STATUS_ACTIVE if user.is_active else Config.STATUS_INACTIVE
    print(f"找到用户: {user.username} (ID: {user.id})")
    print(f"邮箱: {user.email}")
    print(f"全名: {user.full_name}")
    print(f"状态: {status}")

def _display_user_credentials(username: str, password: str, email: str) -> None:
    """显示用户凭据信息"""
    print(f"用户名: {username}")
    print(f"密码: {password}")
    print(f"邮箱: {email}")

def _display_users_table(users: list[User]) -> None:
    """显示用户列表表格"""
    print(f"数据库中的所有用户 (共 {len(users)} 个):")
    print("-" * Config.SEPARATOR_LENGTH)
    
    for user in users:
        status = Config.STATUS_ACTIVE if user.is_active else Config.STATUS_INACTIVE
        print(f"ID: {user.id:{Config.ID_COLUMN_WIDTH}d} | "
              f"用户名: {user.username:{Config.USERNAME_COLUMN_WIDTH}s} | "
              f"邮箱: {user.email:{Config.EMAIL_COLUMN_WIDTH}s} | "
              f"状态: {status}")

def _print_separator(title: str = "") -> None:
    """打印分隔符"""
    if title:
        print(f"\n{title}")
    print("=" * Config.TITLE_SEPARATOR_LENGTH)

# ==================== 命令行参数处理 ====================
def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="用户密码管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                                    # 交互式模式，重置默认test用户
  %(prog)s --list                             # 列出所有用户
  %(prog)s --reset admin newpass123           # 重置admin用户密码
  %(prog)s --create newuser pass123 user@example.com "New User"  # 创建新用户
        """
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有用户"
    )
    
    parser.add_argument(
        "--reset", "-r",
        nargs=2,
        metavar=("USERNAME", "PASSWORD"),
        help="重置指定用户的密码"
    )
    
    parser.add_argument(
        "--create", "-c",
        nargs=4,
        metavar=("USERNAME", "PASSWORD", "EMAIL", "FULL_NAME"),
        help="创建新用户"
    )
    
    return parser.parse_args()

# ==================== 主函数 ====================
def main() -> None:
    """主函数"""
    args = parse_arguments()
    
    _print_separator(Config.Messages.TOOL_TITLE)
    
    # 根据命令行参数执行相应操作
    if args.list:
        list_all_users()
        return
    
    if args.reset:
        username, password = args.reset
        list_all_users()
        _print_separator()
        print(f"正在重置用户 '{username}' 的密码...")
        success = reset_user_password(username, password)
        if success:
            _print_separator(Config.Messages.OPERATION_COMPLETE)
            print(f"用户名: {username}")
            print(f"密码: {password}")
            print(f"\n{Config.Messages.LOGIN_HINT}")
        return
    
    if args.create:
        username, password, email, full_name = args.create
        success = create_user(username, password, email, full_name)
        if success:
            _print_separator(Config.Messages.OPERATION_COMPLETE)
            print(f"\n{Config.Messages.LOGIN_HINT}")
        return
    
    # 默认行为：交互式模式重置test用户
    _run_interactive_mode()

def _run_interactive_mode() -> None:
    """运行交互式模式"""
    # 先列出所有用户
    list_all_users()
    _print_separator()
    
    # 重置默认test用户密码
    username = Config.DEFAULT_USERNAME
    password = Config.DEFAULT_PASSWORD
    
    print(f"正在重置用户 '{username}' 的密码...")
    success = reset_user_password(username, password)
    
    if not success:
        print(f"\n用户不存在，正在创建 {username} 用户...")
        create_success = create_user(
            username=username,
            password=password,
            email=Config.DEFAULT_EMAIL,
            full_name=Config.DEFAULT_FULL_NAME
        )
        if not create_success:
            print("❌ 创建用户失败")
            return
    
    _print_separator(Config.Messages.OPERATION_COMPLETE)
    print(f"用户名: {username}")
    print(f"密码: {password}")
    print(f"\n{Config.Messages.LOGIN_HINT}")

if __name__ == "__main__":
    main()