from config.database import Base, engine
from models.user import User
from models.family import Family, FamilyMember
from models.bill import Bill, BillCategory

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()
    print("数据库表创建成功！") 