from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

# Создаем движок базы данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Связи
    titles = relationship("Title", back_populates="category")

class Title(Base):
    __tablename__ = "titles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # Связи
    category = relationship("Category", back_populates="titles")
    products = relationship("Product", back_populates="title")

class Size(Base):
    __tablename__ = "sizes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price = Column(Float, default=0.0)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    photo_url = Column(String)
    title_id = Column(Integer, ForeignKey("titles.id"))
    is_active = Column(Boolean, default=True)
    
    # Связи
    title = relationship("Title", back_populates="products")
    product_sizes = relationship("ProductSize", back_populates="product")

class ProductSize(Base):
    __tablename__ = "product_sizes"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    size_id = Column(Integer, ForeignKey("sizes.id"))
    
    # Связи
    product = relationship("Product", back_populates="product_sizes")
    size = relationship("Size")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String)
    items = Column(JSON)  # [{product_id, size_id, product_name, size_name, price}]
    delivery_method = Column(String)
    delivery_price = Column(Float, default=0.0)
    total_price = Column(Float)
    discount_amount = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, paid, shipped, delivered
    payment_url = Column(String)
    payment_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    description_text = Column(Text, default="")
    desc_photo_file_id = Column(String, nullable=True)
    desc_video_file_id = Column(String, nullable=True)

def create_tables():
    """Создает все таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Получает сессию базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функции для работы с базой данных
class DatabaseManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    @staticmethod
    def get_session():
        return SessionLocal()

# Создаем таблицы при импорте модуля
create_tables()

# Ensure a default settings row exists with basic text
try:
    db = SessionLocal()
    s = db.query(Settings).filter(Settings.id == 1).first()
    if not s:
        default_text = (
            "✨Уникальный ночник ручной работы✨\n\n"
            "Сегмент СТАНДАРТ - состоит из акриловой пластины (размер стекла указан в см.) и пластиковой подставки:\n\n"
            "🎆 Пластиковая подставка доступна в черной расцветке и в двух размерах. Имеет 7 цветов и 3 режима переливания, управление с помощью пульта ДУ и кнопки:\n\n"
            "🚀 Деревянная подставка Премиум. Имеет 12 цветов свечения, более 300 режимов переливания, управление через мобильное приложение и режим эквалайзер. Доступна в двух размерах:\n\n"
            "🌠 Также данный рисунок масштабируется под большие размеры которые вешаются на стену - Настенные панели.\n"
            "Они состоят из стального фиксатора и акриловой пластины. Имеют 12 цветов свечения и более 200 режимов переливания, управление с помощью мобильного приложения"
        )
        s = Settings(id=1, description_text=default_text)
        db.add(s)
        db.commit()
finally:
    try:
        db.close()
    except Exception:
        pass



