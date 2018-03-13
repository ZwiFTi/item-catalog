# Objectives

1. List out all catalogs

Folder: `/`

2. Add link to edit and delete each catalog



3.  Create new catalogs

Folder `/new`

Form to create new catalog name -> post request


4. Rename a catalog

The edit link

Folder `/id/edit`

5. Detele a catalog

Folder `/id/delete`
Confirmation page




>>> from sqlalchemy import create_engine
>>> from sqlalchemy.orm import sessionmaker
>>> from database_setup import Base, Catalog, CatalogItem

>>> from database_setup import Base, Catalog, CatalogItem
>>> Base.metadata.bind = engine

>>> engine = create_engine('sqlite:///catalog.db')
>>> Base.metadata.bind = engine
>>> DBSession = sessionmaker(bind = engine)
>>> session = DBSession()
>>> myFirstCatalog = Catalog(name = "Snowboarding")
>>> session.add(myFirstCatalog)
>>> session.commit()
>>> session.query(Catalog).all()
[<database_setup.Catalog object at 0xb69b1e0c>]
>>> myFirstCatalogItem = CatalogItem(name = "Snowboarding", description="This is a plain description")
>>> session.add(myFirstCatalogItem)
>>> session.commit()
>>> session.query(CatalogItem).all()
[<database_setup.CatalogItem object at 0xb69b1dcc>]
>>> session.query(CatalogItem).all().name
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'list' object has no attribute 'name'
>>> session.query(CatalogItem).all().name()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'list' object has no attribute 'name'
>>> for i in session.query(Catalog).all():
... print(i)
  File "<stdin>", line 2
    print(i)
        ^
IndentationError: expected an indented block
>>> for i in session.query(Catalog).all():
...     print(i)
...
<database_setup.Catalog object at 0xb69b1e0c>
>>> for i in session.query(Catalog).all():
...     print(i.name)
...
Snowboarding
