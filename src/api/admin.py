from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_potions = :num_potions, num_green_ml = :new_green_ml, num_red_ml = :new_red_ml, num_blue_ml = :new_blue_ml, num_dark_ml = :new_dark_ml, gold = :new_gold"),
        {"num_potions": 0, "new_green_ml": 500, "new_red_ml": 0, "new_blue_ml": 0, "new_dark_ml": 0, "new_gold": 0})
        result2 = connection.execute(sqlalchemy.text("UPDATE potions SET quantity = :baseline"),{"baseline": 0})
    return result

