from .models import Rating
from .schemas import RatingFromORM, RatingWithUserAndListingData, RatingWithUserData


class RatingMapper:

    @staticmethod
    def to_rating_from_orm(rating: Rating) -> RatingFromORM:
        return RatingFromORM(
            id=rating.id,
            listing_id=rating.listing_id,
            comment=rating.comment,
            rating=rating.rating,
            user_id=rating.user_id,
            verified=rating.verified,
            created_at=rating.created_at,
        )

    @staticmethod
    def to_rating_with_user_data_from_orm(rating: Rating) -> RatingWithUserData:
        return RatingWithUserData(
            id=rating.id,
            listing_id=rating.listing_id,
            comment=rating.comment,
            rating=rating.rating,
            user_id=rating.user_id,
            verified=rating.verified,
            created_at=rating.created_at,
            avatar=rating.user.avatar,
            username=(rating.user.name if rating.user.name else "")
            + " "
            + (rating.user.surname if rating.user.surname else ""),
        )

    @staticmethod
    def to_rating_with_user_and_listing_data_from_orm(
        rating: Rating, listing_image: str
    ) -> RatingWithUserAndListingData:
        return RatingWithUserAndListingData(
            id=rating.id,
            listing_id=rating.listing_id,
            comment=rating.comment,
            rating=rating.rating,
            user_id=rating.user_id,
            verified=rating.verified,
            created_at=rating.created_at,
            avatar=rating.user.avatar,
            username=(rating.user.name if rating.user.name else "")
            + " "
            + (rating.user.surname if rating.user.surname else ""),
            listing_title=rating.listing.title,
            listing_price=rating.listing.price,
            listing_image=listing_image,
        )
