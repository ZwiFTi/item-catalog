from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

catalog1 = Catalog(name="Accounting")
catalog2 = Catalog(name="Derivatives")
catalog3 = Catalog(name="Credit Risk Management")
catalog4 = Catalog(name="Finance")
catalog5 = Catalog(name="Financial Risk Management")
catalog6 = Catalog(name="Economics")
catalog7 = Catalog(name="Quantitative Methods")
catalog8 = Catalog(name="Heavy Beer Drinking")

session.add(catalog1)
session.add(catalog2)
session.add(catalog3)
session.add(catalog4)
session.add(catalog5)
session.add(catalog6)
session.add(catalog7)
session.add(catalog8)
session.commit()
