from fastapi import HTTPException


class TooManyImages(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.images.limit_exceeded_5")


class NotEnoughImages(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(
            status_code=400, detail="error.images.no_photos_left_after_put"
        )


class ListingIsAlreadyFavorite(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.listing.already_favorite")


class UnableToFavoriteYourOwnListing(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.listing.favorite_own_listing")


class ListingNotFound(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.listing.not_found")
