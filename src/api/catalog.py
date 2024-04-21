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
        in_stock = connection.execute(sqlalchemy.text("SELECT sku, quantity, price, red, green, blue, dark FROM potions WHERE quantity > 0")).fetchall()
       

    cur_items = []

    for potion in in_stock:
        cur_items.append(
            {
                "sku": potion[0],
                "name": potion[0],
                "quantity": potion[1],
                "price": potion[2],
                "potion_type": [potion[3], potion[4], potion[5], potion[6]],
            }
        )
    
    return cur_items