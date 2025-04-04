from pydantic import BaseModel


class UserCategoryViewFromORM(BaseModel):
    id: int
    user_id: int
    view_count: int
    category_id: int


class UserView(BaseModel):
    user_id: int
    view_count: int


class UserSubcategoryViewFromORM(BaseModel):
    id: int
    user_id: int
    view_count: int
    subcategory_id: int
