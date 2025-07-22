from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from models.family import Family, FamilyMember
from models.user import User
from schemas.family import FamilyCreate
from services.message_service import MessageService


class FamilyService:
    def __init__(self, db: Session):
        self.db = db

    def create_family_with_invites(
        self, 
        family_data: FamilyCreate, 
        creator_id: int, 
        invite_usernames: Optional[List[str]] = None
    ) -> Family:
        """创建家庭并发送邀请"""
        # 创建家庭
        family = Family(
            family_name=family_data.family_name,
            description=family_data.description,
            created_by=creator_id,
        )
        self.db.add(family)
        self.db.commit()
        self.db.refresh(family)

        # 添加创建者为管理员
        member = FamilyMember(
            family_id=family.id,
            user_id=creator_id,
            role="admin",
        )
        self.db.add(member)
        self.db.commit()

        # 发送邀请
        if invite_usernames:
            self.send_family_invites(family.id, creator_id, invite_usernames)

        return family

    def send_family_invites(self, family_id: int, inviter_id: int, usernames: List[str]):
        """发送家庭邀请"""
        family = self.db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise ValueError("家庭不存在")

        message_service = MessageService(self.db)
        
        for username in usernames:
            # 查找用户
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                continue
            
            # 检查用户是否已在家庭中
            existing_member = self.db.query(FamilyMember).filter(
                FamilyMember.user_id == user.id
            ).first()
            
            if existing_member:
                continue  # 用户已在其他家庭中
            
            # 发送邀请消息
            message_service.create_family_invite_message(
                inviter_id=inviter_id,
                invitee_id=user.id,
                family_id=family_id,
                family_name=family.family_name
            )

    def add_member_to_family(self, family_id: int, user_id: int, role: str = "member") -> FamilyMember:
        """添加成员到家庭"""
        # 检查用户是否已在其他家庭中
        existing_member = self.db.query(FamilyMember).filter(
            FamilyMember.user_id == user_id
        ).first()
        
        if existing_member:
            raise ValueError("用户已在其他家庭中")
        
        # 检查家庭是否存在
        family = self.db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise ValueError("家庭不存在")
        
        # 添加成员
        member = FamilyMember(
            family_id=family_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        
        return member

    def remove_member_from_family(self, family_id: int, user_id: int, operator_id: int) -> bool:
        """从家庭中移除成员"""
        # 检查操作者权限
        operator_member = self.db.query(FamilyMember).filter(
            and_(FamilyMember.family_id == family_id, FamilyMember.user_id == operator_id)
        ).first()
        
        if not operator_member:
            raise ValueError("无权限操作")
        
        # 查找要移除的成员
        target_member = self.db.query(FamilyMember).filter(
            and_(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
        ).first()
        
        if not target_member:
            raise ValueError("成员不存在")
        
        # 管理员可以移除任何人，普通成员只能移除自己
        if operator_member.role != "admin" and operator_id != user_id:
            raise ValueError("无权限移除其他成员")
        
        # 不能移除最后一个管理员
        if target_member.role == "admin":
            admin_count = self.db.query(FamilyMember).filter(
                and_(FamilyMember.family_id == family_id, FamilyMember.role == "admin")
            ).count()
            
            if admin_count <= 1:
                raise ValueError("不能移除最后一个管理员")
        
        self.db.delete(target_member)
        self.db.commit()
        
        return True

    def search_users(self, query: str, exclude_user_id: Optional[int] = None) -> List[User]:
        """搜索用户（按用户名和全名模糊查询）"""
        # 支持用户名和全名的模糊查询
        search_query = self.db.query(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%")
            )
        )
        
        if exclude_user_id:
            search_query = search_query.filter(User.id != exclude_user_id)
        
        # 排除已在家庭中的用户
        users_in_families = self.db.query(FamilyMember.user_id).subquery()
        search_query = search_query.filter(~User.id.in_(users_in_families))
        
        # 按用户名排序，优先显示用户名匹配的结果
        from sqlalchemy import case
        search_query = search_query.order_by(
            case(
                (User.username.ilike(f"%{query}%"), 1),
                else_=2
            ),
            User.username
        )
        
        return search_query.limit(20).all()

    def get_user_family(self, user_id: int) -> Optional[Family]:
        """获取用户所属的家庭"""
        member = self.db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
        if member:
            return self.db.query(Family).filter(Family.id == member.family_id).first()
        return None

    def is_family_admin(self, family_id: int, user_id: int) -> bool:
        """检查用户是否为家庭管理员"""
        member = self.db.query(FamilyMember).filter(
            and_(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
        ).first()
        
        return member and member.role == "admin"

    def get_user_families(self, user_id: int) -> List[Family]:
        """获取用户所属的所有家庭"""
        # 查询该用户作为成员的所有家庭记录
        family_members = self.db.query(FamilyMember).filter(FamilyMember.user_id == user_id).all()
        if not family_members:
            return []
        
        # 提取所有家庭ID
        family_ids = [fm.family_id for fm in family_members]
        
        # 查询所有相关的家庭实体
        families = self.db.query(Family).filter(Family.id.in_(family_ids)).all()
        return families