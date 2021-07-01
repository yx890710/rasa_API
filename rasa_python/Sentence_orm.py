#coding:utf-8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, UniqueConstraint, Index # 元素/主key
from sqlalchemy import Integer, String, VARCHAR, TEXT, DATE, NVARCHAR,Text, DATETIME
from sqlalchemy.orm import sessionmaker, relationship, backref # 創接口/建立關系relationship(table.ID)
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool# sqlalchemy 查詢前連結，结束後，調用 session.close() 關閉連結
from sqlalchemy import desc,asc #降序
import os, shutil
import configparser
#create view 套件
from sqlalchemy_utils import create_view
from sqlalchemy import select, func


config = configparser.ConfigParser()
config.read('set.conf')
user = config["DB"]["user"]
password = config["DB"]["password"]
host = config["DB"]["host"]
DB_name = config["DB"]["DB_name"]

DBInfo = "mysql+pymysql://"+ user +":"+password+ "@" + host+ "/" + DB_name+"?charset=utf8mb4"
# user = config["MSDB"]["user"]
# password = config["MSDB"]["password"]
# host = config["MSDB"]["host"]
# DB_name = config["MSDB"]["DB_name"]
# Driver = config["MSDB"]["Windows_driver"]
# # DBInfo = "mysql+pymysql:#"+ user +":"+password+ "@" + host+ "/" + DB_name+"?charset=utf8mb4"
# DBInfo = "mssql+pyodbc:#"+ user +":"+password+ "@" + host+ ":1433/" + DB_name+"?driver="+Driver
DBLink = create_engine(DBInfo, poolclass=NullPool)# 創建一個空的資料庫
Base = declarative_base()# 創數據結構放資料


# 存放意圖
class Intent(Base):
    __tablename__ = "Intent"
    IntentID = Column(Integer, primary_key=True, autoincrement=True)
    Intent = Column(VARCHAR(100))
    Tag = Column(TEXT, default="0")
    IntentClass = Column(VARCHAR(100), default="General")
    Category = Column(VARCHAR(100), default="Text")
    DeleteStatus = Column(VARCHAR(1), nullable=True, default="0")
    
    def __init__(self, Intent, Tag, IntentClass, Category, **kwargs):
        self.Intent = Intent
        self.Tag = Tag
        self.IntentClass = IntentClass
        self.Category = Category
        self.DeleteStatus = kwargs["DeleteStatus"] if "DeleteStatus" in kwargs else None


## 用戶問句列表
class IntentUserQuestion(Base):
    __tablename__ = "IntentUserQuestion"
    UserQuestionID = Column(Integer, primary_key=True, autoincrement=True)
    IntentID = Column(Integer)
    UserQuestion = Column(TEXT, default="0")
    English_UserQuestion = Column(TEXT, default="0") # 英_用戶問句(內含實體key)
    DeleteStatus = Column(VARCHAR(1), nullable=True, default="0") # 刪除

    def __init__(self, IntentID, UserQuestion, English_UserQuestion, **kwargs):
        self.IntentID = IntentID
        self.UserQuestion = UserQuestion
        self.English_UserQuestion = English_UserQuestion
        self.DeleteStatus = kwargs["DeleteStatus"] if "DeleteStatus" in kwargs else None


# 實體類表
class EntityClass(Base):
    __tablename__ = "EntityClass"
    EntityClassID = Column(Integer, primary_key=True, autoincrement=True) # 實體類
    EntityClass = Column(VARCHAR(100), nullable=True, default="0") # 實體key
    EntityClassName = Column(VARCHAR(100), nullable=True, default="0") # 實體類名
    DeleteStatus = Column(VARCHAR(1), nullable=True, default="0")# 刪除

    def __init__(self, EntityClass, EntityClassName, **kwargs):
        self.EntityClass = EntityClass
        self.EntityClassName = EntityClassName
        self.DeleteStatus = kwargs["DeleteStatus"] if "DeleteStatus" in kwargs else None


# 實體表
class Entity(Base):
    __tablename__ = "Entity"
    EntityID  = Column(Integer, primary_key=True, autoincrement=True)
    zh_Entity = Column(VARCHAR(100), nullable=True, default="0") # 中實體
    en_Entity = Column(VARCHAR(100), nullable=True, default="0") # 英實體
    EntityClassID = Column(Integer) # 對應類ID
    DeleteStatus = Column(VARCHAR(1), nullable=True, default="0")# 刪除

    def __init__(self, zh_Entity, en_Entity, EntityClassID,**kwargs):
        self.zh_Entity = zh_Entity
        self.en_Entity = en_Entity
        self.EntityClassID = EntityClassID
        self.DeleteStatus = kwargs["DeleteStatus"] if "DeleteStatus" in kwargs else None

# 用戶問句實體類之關聯表
class EntityRelation(Base):
    __tablename__ = "EntityRelation"
    EntityRelationID = Column(Integer, primary_key=True, autoincrement=True)
    IntentID = Column(Integer) # 對應意圖ID
    UserQuestionID = Column(Integer) # 對應用戶問句
    EntityClassID = Column(Integer) # 實際用戶句使用之實體
    UserSetWord = Column(VARCHAR(100), nullable=True, default="0") # 後台端用戶問句設定詞
    English_UserSetWord = Column(VARCHAR(100), nullable=True, default="0")# 後台端用戶英文問句設定詞
    DeleteStatus = Column(VARCHAR(1), nullable=True, default="0")# 刪除

    def __init__(self, IntentID, UserQuestionID, EntityClassID, UserSetWord, English_UserSetWord, **kwargs): 
        self.IntentID= IntentID
        self.UserQuestionID = UserQuestionID
        self.EntityClassID = EntityClassID
        self.UserSetWord = UserSetWord
        self.English_UserSetWord = English_UserSetWord 
        self.DeleteStatus = kwargs["DeleteStatus"] if "DeleteStatus" in kwargs else None


# ---------以上為實體及使用者對話--- 

# Intent+IntentUserQuestion
stmt = select([
    Intent.IntentID,Intent.Intent,
    IntentUserQuestion.UserQuestionID,
    IntentUserQuestion.UserQuestion,
    IntentUserQuestion.English_UserQuestion
]).select_from(Intent.__table__.outerjoin(IntentUserQuestion, IntentUserQuestion.IntentID == Intent.IntentID))

# attaches the view to the metadata using the select statement
view = create_view('test', stmt, Base.metadata)

# provides an ORM interface to the view
class Test(Base):
    __table__ = view

# At this point running the following yields 0, as expected,
# indicating that the view has been constructed on the server 
DBLink.execute(select([func.count('*')], from_obj=Test)).scalar()


# EntityRelation+EntityClass

stmt2 = select([
    EntityRelation.UserQuestionID,
    EntityRelation.EntityClassID,
    EntityClass.EntityClass
]).select_from(EntityRelation.__table__.outerjoin(EntityClass, EntityClass.EntityClassID == EntityRelation.EntityClassID))

# attaches the view to the metadata using the select statement
view2 = create_view('test2', stmt2, Base.metadata)

# provides an ORM interface to the view
class Test2(Base):
    __table__ = view2

# At this point running the following yields 0, as expected,
# indicating that the view has been constructed on the server 
DBLink.execute(select([func.count('*')], from_obj=Test2)).scalar()


# test2 + test

stmt4 = select([
    Test.IntentID,
    Test.Intent,
    Test.UserQuestionID,
    Test.UserQuestion,
    Test.English_UserQuestion,
    Test2.EntityClassID,
    Test2.EntityClass
]).select_from(Test.__table__.outerjoin(Test2, Test.UserQuestionID == Test2.UserQuestionID))

# attaches the view to the metadata using the select statement
view4 = create_view('rasa_view', stmt4, Base.metadata)

# provides an ORM interface to the view
class Rasa_View(Base):
    __table__ = view4

# At this point running the following yields 0, as expected,
# indicating that the view has been constructed on the server 
DBLink.execute(select([func.count('*')], from_obj=Rasa_View)).scalar()


# Entity+EntityClass

stmt5 = select([
    Entity.EntityID,
    Entity.zh_Entity,
    Entity.en_Entity,
    Entity.EntityClassID,
    EntityClass.EntityClass

]).select_from(Entity.__table__.outerjoin(Entity, EntityClass.EntityClassID == Entity.EntityClassID))

# attaches the view to the metadata using the select statement
view5 = create_view('entity_view', stmt5, Base.metadata)

# provides an ORM interface to the view
class Entity_View(Base):
    __table__ = view5

# At this point running the following yields 0, as expected,
# indicating that the view has been constructed on the server 
DBLink.execute(select([func.count('*')], from_obj=Entity_View)).scalar()



# ---------以上為create View部分--- 



def init_db():
    Base.metadata.create_all(DBLink)

def drop_db():
    Base.metadata.drop_all(DBLink)

# init_db()
# drop_db()

# 新增DB
'''CREATE DATABASE (DBname) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'''
    

# Intent+IntentUserQuestion = test 
'''
CREATE VIEW test AS
    SELECT 
        intent.IntentID,intent.Intent,
        intent_u_q.UserQuestionID,intent_u_q.UserQuestion,intent_u_q.English_UserQuestion
    FROM
        Intent intent
            INNER JOIN
        IntentUserQuestion intent_u_q ON intent.IntentID = intent_u_q.IntentID
    WHERE 
        intent.DeleteStatus=0 and intent_u_q.DeleteStatus=0
    ORDER BY intent.IntentID DESC;



# EntityRelation + EntityClass

CREATE VIEW test2 AS
    SELECT 
        er.UserQuestionID,er.EntityClassID,
        ec.EntityClass
    FROM
        EntityRelation er
            INNER JOIN
        EntityClass ec ON er.EntityClassID = ec.EntityClassID
    WHERE 
        er.DeleteStatus=0 and ec.DeleteStatus=0
    ORDER BY er.UserQuestionID;

# test + test2

CREATE VIEW rasa_view AS
    SELECT 
        t.IntentID,t.Intent,t.UserQuestionID,t.UserQuestion,t.English_UserQuestion,
        t2.EntityClassID,t2.EntityClass
    FROM
        test t
            LEFT JOIN
        test2 t2 ON t.UserQuestionID = t2.UserQuestionID
    ORDER BY t.UserQuestionID;

## Entity+EntityClass表另外查

CREATE VIEW entity_view AS
    SELECT 
        e.EntityID,e.zh_Entity,e.en_Entity,e.EntityClassID,
        ec.EntityClass
    FROM
        Entity e
            INNER JOIN
        EntityClass ec ON e.EntityClassID = ec.EntityClassID
    WHERE 
        e.DeleteStatus=0 and ec.DeleteStatus=0
    ORDER BY e.EntityID;


'''





