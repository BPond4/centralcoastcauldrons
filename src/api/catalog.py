from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions WHERE quantity > 0")).fetchall()
        
    if(result):
        in_stock = dict(result)
        
    cur_items = []

    for potion in in_stock:
        cur_items.append(
            {
                "sku": potion['sku'],
                "name": potion['sku'],
                "quantity": potion['quantity'],
                "price": potion['price'],
                "potion_type": [potion['red'], potion['green'], potion['blue'], potion['dark']],
            }
        )
    
    return cur_items