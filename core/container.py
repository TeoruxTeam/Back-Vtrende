import socketio
from dependency_injector import containers, providers

from accounts.repositories import RecoveryTokenRepository, VerificationTokenRepository
from accounts.services import (
    RecoveryFacade,
    RecoveryTokenService,
    VerificationFacade,
    VerificationTokenService,
)
from auth.facade import AuthFacade
from auth.repositories import RefreshTokenRepository
from auth.services import AuthService
from core.database import Database, UnitOfWork
from core.email_sender import EmailSender
from core.environment import env
from users.repositories import UserRepository
from users.services import UserService
from favorites.repositories import FavoriteRepository
from favorites.services import FavoriteService
from items.repositories import ItemRepository
from items.services import ItemService

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "auth.router",
            "auth.depends",
            "users.router",
            "accounts.router",
            "favorites.router",
            "items.router",
        ]
    )

    db = providers.Singleton(
        Database,
        db_url=f"{env.DATABASE_DIALECT}+asyncpg://{env.POSTGRES_USER}:{env.POSTGRES_PASSWORD}@{env.POSTGRES_HOSTNAME}:{env.POSTGRES_PORT}/{env.POSTGRES_DB}",
    )

    unit_of_work = providers.Factory(UnitOfWork, session_factory=db.provided.session)

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
    favorite_repository = providers.Factory(
        FavoriteRepository, session_factory=db.provided.session
    )
    item_repository = providers.Factory(
        ItemRepository, session_factory=db.provided.session
    )

    auth_service = providers.Factory(AuthService, repo=refresh_token_repository)
    user_service = providers.Factory(UserService, repo=user_repository)
    verification_code_service = providers.Factory(
        VerificationTokenService, repo=verification_code_repository
    )
    recovery_token_service = providers.Factory(
        RecoveryTokenService, repo=recovery_code_repository
    )
    favorite_service = providers.Factory(
        FavoriteService,
        fav_repo=favorite_repository,
        item_repo=item_repository,
        user_repo=user_repository
    )
    item_service = providers.Factory(
        ItemService,
        repo=item_repository
    )

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