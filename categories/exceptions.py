from fastapi import HTTPException


class CategoryNotFound(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.category.not_found")


class SubcategoryNotFound(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.subcategory.not_found")


class CategoryChildExists(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.category.child_objects_exist")


class SubcategoryChildExists(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(
            status_code=400, detail="error.subcategory.child_objects_exist"
        )
