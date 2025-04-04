from fastapi import HTTPException


class RatingAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.listing.rating.already_exists")


class CantRateYourself(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400, detail="error.listing.rating.cant_rate_yourself"
        )


class RatingNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.listing.rating.not_found")
