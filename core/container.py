import socketio
from dependency_injector import containers, providers

from accounts.repositories import RecoveryTokenRepository, VerificationTokenRepository
from accounts.services import (
    RecoveryFacade,
    RecoveryTokenService,
    VerificationFacade,
    VerificationTokenService,
)
from admin.facade import AdminFacade
from auth.facade import AuthFacade
from auth.repositories import RefreshTokenRepository
from auth.services import AuthService
from categories.facade import CategoryFacade
from categories.repositories import CategoryRepository, SubcategoryRepository
from categories.services import CategoryService, SubcategoryService
from chats.facade import ChatFacade
from chats.repositories import (
    ChatAggregateRepository,
    ChatRepository,
    MessageRepository,
)
from chats.services import ChatAggregateService, ChatService, MessageService
from core.database import Database, UnitOfWork
from core.email_sender import EmailSender
from core.environment import env
from core.redis_client import RedisPool
from core.socketio_server import CustomSocketServer
from listings.facade import ListingFacade
from listings.repositories import (
    FavoriteListingRepository,
    ListingAggregateRepository,
    ListingRepository,
)
from listings.services import (
    FavoriteListingService,
    ListingAggregateService,
    ListingService,
)
from localization.facade import LocalizationFacade
from localization.repositories import LocalizationKeyRepository, LocalizationRepository
from localization.services import LocalizationKeyService, LocalizationService
from locations.repositories import LocationRepository
from locations.services import LocationService
from notifications.facade import NotificationFacade
from notifications.repositories import (
    FCMTokenRepository,
    NotificationRepository,
    NotificationSettingsRepository,
)
from notifications.services import (
    FCMTokenService,
    NotificationService,
    NotificationSettingsService,
)
from payments.facade import PaymentFacade
from payments.services import PaymentService
from promotions.facade import PromotionFacade
from promotions.repositories import PromotionRepository
from promotions.services import PromotionService
from ratings.facade import RatingFacade
from ratings.repositories import RatingRepository
from ratings.services import RatingService
from recommendations.facade import RecommendationFacade
from recommendations.repositories import (
    CategoryViewRepository,
    SubcategoryViewRepository,
)
from recommendations.services import CategoryViewService, SubcategoryViewService
from stats.facade import StatsFacade
from stats.repositories import StatsRepository
from stats.services import StatsService
from users.facade import UserFacade
from users.repositories import UserRepository
from users.services import UserService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "auth.router",
            "auth.depends",
            "users.router",
            "accounts.router",
            "listings.router",
            "categories.router",
            "chats.router",
            "sockets.auth",
            "sockets.chats",
            "sockets.notifications",
            "localization.router",
            "admin.router",
            "notifications.router",
            "promotions.router",
            "payments.router",
        ]
    )

    db = providers.Singleton(
        Database,
        db_url=f"{env.DATABASE_DIALECT}+asyncpg://{env.POSTGRES_USER}:{env.POSTGRES_PASSWORD}@{env.POSTGRES_HOSTNAME}:{env.POSTGRES_PORT}/{env.POSTGRES_DB}",
    )

    unit_of_work = providers.Factory(UnitOfWork, session_factory=db.provided.session)

    redis_pool = providers.Singleton(
        RedisPool,
        redis_url=f"redis://:{env.redis_password}@{env.redis_host}:{env.redis_port}/{env.redis_db}",
    )

    email_sender = providers.Singleton(
        EmailSender,
        smtp_server=env.smtp_server,
        smtp_port=env.smtp_port,
        username=env.smtp_username,
        password=env.smtp_password,
        start_tls=env.smtp_start_tls,
        start_ssl=env.smtp_start_ssl,
    )

    refresh_token_repository = providers.Factory(
        RefreshTokenRepository, session_factory=db.provided.session
    )
    user_repository = providers.Factory(
        UserRepository, session_factory=db.provided.session
    )
    verification_code_repository = providers.Factory(
        VerificationTokenRepository, session_factory=db.provided.session
    )
    recovery_code_repository = providers.Factory(
        RecoveryTokenRepository, session_factory=db.provided.session
    )
    listing_repository = providers.Factory(
        ListingRepository, session_factory=db.provided.session
    )
    listing_aggregate_repository = providers.Factory(
        ListingAggregateRepository, session_factory=db.provided.session
    )
    location_repository = providers.Factory(
        LocationRepository, session_factory=db.provided.session
    )
    category_repository = providers.Factory(
        CategoryRepository, session_factory=db.provided.session
    )
    subcategory_repository = providers.Factory(
        SubcategoryRepository, session_factory=db.provided.session
    )
    favorite_listing_repository = providers.Factory(
        FavoriteListingRepository, session_factory=db.provided.session
    )
    chat_repository = providers.Factory(
        ChatRepository, session_factory=db.provided.session
    )
    chat_aggregate_repository = providers.Factory(
        ChatAggregateRepository, session_factory=db.provided.session
    )
    message_repository = providers.Factory(
        MessageRepository, session_factory=db.provided.session
    )
    stats_repository = providers.Factory(
        StatsRepository, session_factory=db.provided.session
    )
    localization_repository = providers.Factory(
        LocalizationRepository, session_factory=db.provided.session
    )
    localization_key_repository = providers.Factory(
        LocalizationKeyRepository, session_factory=db.provided.session
    )
    rating_repository = providers.Factory(
        RatingRepository, session_factory=db.provided.session
    )
    category_view_repository = providers.Factory(
        CategoryViewRepository, session_factory=db.provided.session
    )
    subcategory_view_repository = providers.Factory(
        SubcategoryViewRepository, session_factory=db.provided.session
    )
    notification_repository = providers.Factory(
        NotificationRepository, session_factory=db.provided.session
    )
    fcm_token_repository = providers.Factory(
        FCMTokenRepository, session_factory=db.provided.session
    )
    notification_settings_repository = providers.Factory(
        NotificationSettingsRepository, session_factory=db.provided.session
    )
    promotion_repository = providers.Factory(
        PromotionRepository, session_factory=db.provided.session
    )

    auth_service = providers.Factory(AuthService, repo=refresh_token_repository)
    user_service = providers.Factory(UserService, repo=user_repository)
    verification_code_service = providers.Factory(
        VerificationTokenService, repo=verification_code_repository
    )
    recovery_token_service = providers.Factory(
        RecoveryTokenService, repo=recovery_code_repository
    )
    listing_service = providers.Factory(ListingService, repo=listing_repository)
    listing_aggregate_service = providers.Factory(
        ListingAggregateService, repo=listing_aggregate_repository
    )
    location_service = providers.Factory(LocationService, repo=location_repository)
    category_service = providers.Factory(CategoryService, repo=category_repository)
    subcategory_service = providers.Factory(
        SubcategoryService, repo=subcategory_repository
    )
    favorite_listing_service = providers.Factory(
        FavoriteListingService, repo=favorite_listing_repository
    )
    chat_service = providers.Factory(ChatService, repo=chat_repository)
    chat_aggregate_service = providers.Factory(
        ChatAggregateService, repo=chat_aggregate_repository
    )
    message_service = providers.Factory(MessageService, repo=message_repository)
    stats_service = providers.Factory(StatsService, repo=stats_repository)
    localization_service = providers.Factory(
        LocalizationService, repo=localization_repository
    )
    localization_key_service = providers.Factory(
        LocalizationKeyService, repo=localization_key_repository
    )
    rating_service = providers.Factory(RatingService, repo=rating_repository)
    notification_service = providers.Factory(
        NotificationService, repo=notification_repository
    )
    category_view_service = providers.Factory(
        CategoryViewService, repo=category_view_repository
    )
    subcategory_view_service = providers.Factory(
        SubcategoryViewService, repo=subcategory_view_repository
    )
    fcm_token_service = providers.Factory(FCMTokenService, repo=fcm_token_repository)
    notification_settings_service = providers.Factory(
        NotificationSettingsService, repo=notification_settings_repository
    )
    promotion_service = providers.Factory(
        PromotionService, promotion_repository=promotion_repository
    )
    payment_service = providers.Factory(PaymentService)
    auth_facade = providers.Factory(
        AuthFacade, user_service=user_service, auth_service=auth_service
    )
    verification_facade = providers.Factory(
        VerificationFacade,
        user_service=user_service,
        verification_code_service=verification_code_service,
    )
    recovery_facade = providers.Factory(
        RecoveryFacade,
        user_service=user_service,
        recovery_token_service=recovery_token_service,
    )
    listing_facade = providers.Factory(
        ListingFacade,
        listing_service=listing_service,
        listing_aggregate_service=listing_aggregate_service,
        location_service=location_service,
        category_service=category_service,
        subcategory_service=subcategory_service,
        favorite_listing_service=favorite_listing_service,
        uow=unit_of_work,
    )
    category_facade = providers.Factory(
        CategoryFacade,
        category_service=category_service,
        subcategory_service=subcategory_service,
    )
    chat_facade = providers.Factory(
        ChatFacade,
        chat_service=chat_service,
        message_service=message_service,
        chat_aggregate_service=chat_aggregate_service,
    )
    admin_facade = providers.Factory(
        AdminFacade,
        user_service=user_service,
        category_service=category_service,
        subcategory_service=subcategory_service,
        listing_service=listing_service,
        listing_aggregate_service=listing_aggregate_service,
        chat_service=chat_service,
        chat_aggregate_service=chat_aggregate_service,
        localization_key_service=localization_key_service,
        localization_service=localization_service,
        uow=unit_of_work,
    )
    stats_facade = providers.Factory(
        StatsFacade, user_service, listing_service, stats_service
    )
    localization_facade = providers.Factory(
        LocalizationFacade,
        localization_key_service=localization_key_service,
        localization_service=localization_service,
    )

    notification_facade = providers.Factory(
        NotificationFacade,
        notification_service=notification_service,
        category_view_service=category_view_service,
        subcategory_view_service=subcategory_view_service,
        uow=unit_of_work,
        fcm_token_service=fcm_token_service,
        notification_settings_service=notification_settings_repository,
        email_sender=email_sender,
        redis_pool=redis_pool,
    )
    recommendation_facade = providers.Factory(
        RecommendationFacade,
        category_view_service=category_view_service,
        subcategory_view_service=subcategory_view_service,
    )
    rating_facade = providers.Factory(
        RatingFacade, rating_service=rating_service, listing_service=listing_service
    )

    user_facade = providers.Factory(
        UserFacade, rating_service=rating_service, user_service=user_service
    )
    payment_facade = providers.Factory(
        PaymentFacade,
        payment_service,
        promotion_service,
        listing_service,
    )
    promotion_facade = providers.Factory(
        PromotionFacade,
        promotion_service=promotion_service,
        localization_key_service=localization_key_service,
    )

    redis_manager = providers.Singleton(
        socketio.AsyncRedisManager,
        url=f"redis://:{env.redis_password}@{env.redis_host}:{env.redis_port}/{env.redis_db}",
    )

    socketio_server = providers.Singleton(
        CustomSocketServer,
        async_mode="asgi",
        client_manager=redis_manager,
        cors_credentials=True,
    )

    socketio_app = providers.Singleton(
        socketio.ASGIApp,
        socketio_server=socketio_server,
        socketio_path="/socket.io",
    )
