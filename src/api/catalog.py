from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    cur_items = []
    count = 0
    with db.engine.begin() as connection:
        
        potions = connection.execute(sqlalchemy.text("SELECT id, sku, price, red, green, blue, dark FROM potions")).fetchall()
        for potion in potions:
            quantity = connection.execute(sqlalchemy.text("SELECT SUM(num_potions) FROM potion_ledgers WHERE potion_id = :potion_id"),{"potion_id":potion[0]}).fetchone()[0]
            if(quantity):
                if(count<6 and quantity>0):
                    cur_items.append(
                        {
                            "sku": potion[1],
                            "name": potion[1],
                            "quantity": quantity,
                            "price": potion[2],
                            "potion_type": [potion[3], potion[4], potion[5], potion[6]],
                        }
                    )
                    count+=1
       

    

    
    
    return cur_items