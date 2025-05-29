from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(256), nullable=False) # Will store hashed password
    name = Column(String(50), nullable=True)  # Making this optional
    email = Column(String(100), unique=True, nullable=True)  # Making this optional
    
    incomes = relationship("Income", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    financial_goals = relationship("FinancialGoal", back_populates="user")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    category_type = Column(String(20))  # 'income' or 'expense'
    
    expenses = relationship("Expense", back_populates="category")
    budgets = relationship("Budget", back_populates="category")

class Income(Base):
    __tablename__ = 'incomes'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    description = Column(String(200), nullable=False)  # Main text field for income source
    date = Column(Date, default=datetime.datetime.now().date)
    source = Column(String(100), nullable=True)  # Making source nullable for backward compatibility
    
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="incomes")

class Expense(Base):
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    description = Column(String(200))
    date = Column(Date, default=datetime.datetime.now().date)
    
    # APR tracking fields
    has_apr = Column(Integer, default=0)  # Boolean flag (0 = no, 1 = yes)
    apr = Column(Float, default=0.0)    # Annual Percentage Rate
    
    user_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

def init_db():
    """Initialize the database, creating all tables."""
    engine = create_engine('sqlite:///budget.db')
    Base.metadata.create_all(engine)
    return engine
