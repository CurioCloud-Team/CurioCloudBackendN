#!/usr/bin/env python3
"""
CurioCloud Backend - LandPPT用户同步脚本（最终版本）

同步CurioCloud用户到LandPPT，并为每个用户创建API Key
"""

import sys
import os
from pathlib import Path

# 设置工作目录
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# CurioCloud imports
from app.core.database import get_db
from app.models import User as CurioCloudUser
from sqlalchemy.orm import Session

# LandPPT imports
landppt_path = current_dir.parent / 'LandPPT' / 'src'
sys.path.insert(0, str(landppt_path))

try:
    from landppt.database.database import engine as landppt_engine
    from landppt.database.models import User as LandPPTUser, ApiKey as LandPPTApiKey
    from landppt.auth.auth_service import AuthService
except ImportError as e:
    print(f"❌ 无法导入LandPPT模块: {e}")
    print("请确保LandPPT项目路径正确")
    sys.exit(1)
from sqlalchemy.orm import sessionmaker

# 创建LandPPT数据库会话
LandPTTSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=landppt_engine)


def sync_users_with_api_keys():
    """同步用户并为每个用户创建API Key"""

    print("=== CurioCloud用户同步到LandPPT（含API Key） ===\n")

    # 获取数据库会话
    curio_db = next(get_db())
    landppt_db = LandPTTSessionLocal()

    try:
        # 初始化LandPPT认证服务
        auth_service = AuthService()

        # 获取所有CurioCloud用户
        curio_users = curio_db.query(CurioCloudUser).all()
        print(f"找到 {len(curio_users)} 个CurioCloud用户")

        synced_count = 0
        api_key_count = 0

        for curio_user in curio_users:
            try:
                print(f"\n处理用户: {curio_user.username} ({curio_user.email})")

                # 1. 检查LandPPT中是否已存在该用户
                landppt_user = landppt_db.query(LandPPTUser).filter_by(
                    email=curio_user.email
                ).first()

                if not landppt_user:
                    # 创建新用户
                    landppt_user = LandPPTUser(
                        username=curio_user.username,
                        email=curio_user.email,
                        full_name=curio_user.full_name,
                        hashed_password=curio_user.hashed_password,  # 直接使用相同的哈希密码
                        is_active=curio_user.is_active,
                        is_verified=curio_user.is_verified
                    )
                    landppt_db.add(landppt_user)
                    landppt_db.flush()  # 获取ID
                    print(f"  ✅ 创建LandPPT用户: {landppt_user.username}")
                else:
                    # 更新现有用户信息
                    landppt_user.username = curio_user.username
                    landppt_user.full_name = curio_user.full_name
                    landppt_user.hashed_password = curio_user.hashed_password
                    landppt_user.is_active = curio_user.is_active
                    landppt_user.is_verified = curio_user.is_verified
                    print(f"  ✅ 更新LandPPT用户: {landppt_user.username}")

                # 2. 检查是否已有API Key
                existing_api_key = landppt_db.query(LandPPTApiKey).filter_by(
                    user_id=landppt_user.id
                ).first()

                if not existing_api_key:
                    # 创建新的API Key
                    api_key_obj = auth_service.create_api_key(landppt_db, landppt_user, f"CurioCloud-{landppt_user.username}")
                    print(f"  ✅ 创建API Key: {api_key_obj.api_key[:20]}...")

                    # 3. 更新CurioCloud用户的landppt_api_key字段
                    curio_user.landppt_api_key = api_key_obj.api_key
                    api_key_count += 1
                else:
                    # 确保CurioCloud用户有对应的API Key
                    if not curio_user.landppt_api_key:
                        curio_user.landppt_api_key = existing_api_key.api_key
                        print(f"  ✅ 关联现有API Key: {existing_api_key.api_key[:20]}...")
                    else:
                        print(f"  ✅ API Key已存在并关联")

                synced_count += 1

            except Exception as e:
                print(f"  ❌ 处理用户失败: {e}")
                landppt_db.rollback()
                continue

        # 提交所有更改
        landppt_db.commit()
        curio_db.commit()

        print("\n=== 同步完成 ===")
        print(f"✅ 同步用户数量: {synced_count}")
        print(f"✅ 创建API Key数量: {api_key_count}")

        # 验证结果
        print("\n=== 验证结果 ===")
        verify_sync(curio_db, landppt_db)

    except Exception as e:
        print(f"❌ 同步过程出错: {e}")
        landppt_db.rollback()
        curio_db.rollback()
    finally:
        landppt_db.close()
        curio_db.close()


def verify_sync(curio_db: Session, landppt_db):
    """验证同步结果"""
    print("验证用户同步结果...")

    # 获取所有用户和API密钥
    curio_users = curio_db.query(CurioCloudUser).all()
    landppt_users = landppt_db.query(LandPPTUser).all()
    api_keys = landppt_db.query(LandPPTApiKey).all()

    print(f"CurioCloud用户数量: {len(curio_users)}")
    print(f"LandPPT用户数量: {len(landppt_users)}")
    print(f"LandPPT API密钥数量: {len(api_keys)}")

    print("\n用户和API密钥对应关系:")
    for curio_user in curio_users:
        landppt_user = landppt_db.query(LandPPTUser).filter_by(email=curio_user.email).first()
        api_key_record = None
        if landppt_user:
            api_key_record = landppt_db.query(LandPPTApiKey).filter_by(user_id=landppt_user.id).first()

        curio_api_key = curio_user.landppt_api_key[:20] + "..." if curio_user.landppt_api_key else "无"
        landppt_api_key = api_key_record.api_key[:20] + "..." if api_key_record else "无"

        status = "✅" if curio_user.landppt_api_key and api_key_record and curio_user.landppt_api_key == api_key_record.api_key else "❌"
        print(f"  {status} {curio_user.username}: CurioCloud={curio_api_key}, LandPPT={landppt_api_key}")


if __name__ == "__main__":
    sync_users_with_api_keys()