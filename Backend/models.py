from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String, nullable=False)

    # Academic
    tenth = Column(Float)
    twelfth = Column(Float)
    be_cgpa = Column(Float)

    # Skills
    skills = Column(String)
    domain = Column(String)

    # Experience
    projects = Column(Integer)
    hackathons = Column(Integer)
    papers = Column(Integer)

    # Placement
    placed = Column(Boolean, default=False)
    company = Column(String)
    salary = Column(Float)
    company_type = Column(String)

    def __repr__(self):
        return f"<Student(name={self.name}, cgpa={self.be_cgpa})>"
