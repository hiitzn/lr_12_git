from sqlalchemy.orm import Session
from app.models.recipe import Recipe
from app.models.menu import MenuItem

class RecipeRepository:
    @staticmethod
    def get_by_menu_item_id(db: Session, menu_item_id: int) -> Recipe | None:
        return db.query(Recipe).filter(Recipe.menu_item_id == menu_item_id).first()

    @staticmethod
    def get_all_with_menu(db: Session):
        return db.query(Recipe).join(MenuItem).all()

    @staticmethod
    def create(db: Session, menu_item_id: int, ingredients: str, instructions: str, cooking_time: int) -> Recipe:
        recipe = Recipe(
            menu_item_id=menu_item_id,
            ingredients=ingredients,
            instructions=instructions,
            cooking_time=cooking_time
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return recipe

    @staticmethod
    def update(db: Session, recipe: Recipe, ingredients: str, instructions: str, cooking_time: int) -> Recipe:
        recipe.ingredients = ingredients
        recipe.instructions = instructions
        recipe.cooking_time = cooking_time
        db.commit()
        db.refresh(recipe)
        return recipe

    @staticmethod
    def delete(db: Session, recipe: Recipe) -> None:
        db.delete(recipe)
        db.commit()