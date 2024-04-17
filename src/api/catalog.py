from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    green_potions = 0
    blue_potions = 0
    red_potions = 0
    with db.engine.begin() as connection:
        green_potions = (connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone())[0]
        blue_potions = (connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).fetchone())[0]
        red_potions = (connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).fetchone())[0]

    print(red_potions)
    print(green_potions)
    print(blue_potions)
    cur_items = []

    if(red_potions >0):
        cur_items.append(
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        )
    if(green_potions>0):
        cur_items.append(
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        )
    if(blue_potions>0):
        cur_items.append(
            {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": blue_potions,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }
        )

    return cur_items