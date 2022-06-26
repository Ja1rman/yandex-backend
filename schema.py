from sre_constants import CATEGORY
from sqlalchemy import (
    Column, Date, Enum as PgEnum, ForeignKey, Integer, MetaData,
    String, Table
)
from sqlalchemy.dialects.postgresql import UUID
import db

metadata = MetaData()

class Type:
    OFFER = 'offer'
    CATEGORY = 'category'

    def from_string(s):
        if s.lower() == 'offer':
            return Type.OFFER
        elif s.lower() == 'category':
            return Type.CATEGORY
        else:
            return None

items_table = Table(
    'items',
    metadata,
    autoload=True,
    autoload_with=db.engine
)

relations_table = Table(
    'relations',
    metadata,
    autoload=True,
    autoload_with=db.engine
)