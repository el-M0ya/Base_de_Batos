"""Unit tests for authentication, token resolution and capabilities (E4-01).

The tests use only ``unittest`` and the application/domain layers. No FastAPI,
psycopg or PostgreSQL is imported, so they also verify that the use cases remain
independent from the delivery mechanism.
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fakes.fake_security_services import FakePasswordHasher, FakeTokenService
from fakes.in_memory_authorisation_repository import InMemoryAuthorisationRepository
from fakes.in_memory_user_repository import InMemoryUserRepository

from app.application.dto.actor import ActorDTO, CapabilitiesDTO
from app.application.dto.auth_dto import LoginInputDTO
from app.application.exceptions import (
    AuthenticationFailed,
    ExpiredToken,
    InvalidToken,
)
from app.application.services.user_session_service import UserSessionService
from app.application.use_cases.authenticate_user import AuthenticateUserUseCase
from app.application.use_cases.resolve_session import ResolveSessionUseCase
from app.domain.entities.authorisation import Authorisation
from app.domain.entities.user import User
from app.domain.value_objects.user_role import UserRole


def _user(
    *,
    id_user: int,
    role: UserRole,
    active: bool = True,
    email: str | None = None,
    password: str = "correct-password",
) -> User:
    return User(
        id_user=id_user,
        name=f"User {id_user}",
        email=email or f"user{id_user}@example.com",
        password_hash=f"fake:{password}",
        role=role,
        active=active,
    )


class AuthenticationUseCaseTests(unittest.IsolatedAsyncioTestCase):
    """Login and token-resolution behaviour shared by every role."""

    def _authenticate(
        self,
        users: InMemoryUserRepository,
        authorisations: InMemoryAuthorisationRepository,
    ) -> AuthenticateUserUseCase:
        return AuthenticateUserUseCase(
            users,
            FakePasswordHasher(),
            FakeTokenService(),
            UserSessionService(authorisations),
        )

    def _resolve(
        self,
        users: InMemoryUserRepository,
        authorisations: InMemoryAuthorisationRepository,
    ) -> ResolveSessionUseCase:
        return ResolveSessionUseCase(
            users,
            FakeTokenService(),
            UserSessionService(authorisations),
        )

    async def test_valid_credentials_issue_token_and_derive_capabilities(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER)]
        )
        authorisations = InMemoryAuthorisationRepository(
            [
                Authorisation(
                    id_trainer=7,
                    id_workout_program=1,
                    can_validate=True,
                    start_date=date.today(),
                ),
                Authorisation(
                    id_trainer=7,
                    id_workout_program=2,
                    can_validate=True,
                    start_date=date.today(),
                ),
                Authorisation(
                    id_trainer=7,
                    id_workout_program=3,
                    can_generate=True,
                    start_date=date.today() - timedelta(days=10),
                    end_date=date.today() - timedelta(days=1),
                ),
            ]
        )

        result = await self._authenticate(users, authorisations).execute(
            LoginInputDTO(email="USER7@EXAMPLE.COM", password="correct-password")
        )

        self.assertEqual(result.token_type, "bearer")
        self.assertTrue(result.access_token)
        self.assertGreater(result.expires_in, 0)
        self.assertEqual(result.user.id_user, 7)
        self.assertEqual(result.user.role, UserRole.TRAINER)
        self.assertFalse(result.user.capabilities.can_generate)
        self.assertTrue(result.user.capabilities.can_validate)

    async def test_invalid_password_is_rejected(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER)]
        )

        with self.assertRaises(AuthenticationFailed):
            await self._authenticate(
                users, InMemoryAuthorisationRepository()
            ).execute(
                LoginInputDTO(email="user7@example.com", password="wrong-password")
            )

    async def test_unknown_email_is_rejected(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER)]
        )

        with self.assertRaises(AuthenticationFailed):
            await self._authenticate(
                users, InMemoryAuthorisationRepository()
            ).execute(
                LoginInputDTO(email="unknown@example.com", password="correct-password")
            )

    async def test_inactive_account_is_rejected_even_with_correct_password(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER, active=False)]
        )

        with self.assertRaises(AuthenticationFailed) as context:
            await self._authenticate(
                users, InMemoryAuthorisationRepository()
            ).execute(
                LoginInputDTO(email="user7@example.com", password="correct-password")
            )

        self.assertIn("inactive", context.exception.detail.lower())

    async def test_admin_and_client_have_no_generation_or_validation_capability(self) -> None:
        for role in (UserRole.ADMIN, UserRole.CLIENT):
            with self.subTest(role=role):
                users = InMemoryUserRepository([_user(id_user=9, role=role)])
                result = await self._authenticate(
                    users, InMemoryAuthorisationRepository()
                ).execute(
                    LoginInputDTO(email="user9@example.com", password="correct-password")
                )

                self.assertEqual(
                    result.user.capabilities,
                    CapabilitiesDTO(can_generate=False, can_validate=False),
                )

    async def test_expired_token_is_rejected(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER)]
        )

        with self.assertRaises(ExpiredToken):
            await self._resolve(
                users, InMemoryAuthorisationRepository()
            ).execute("expired")

    async def test_invalid_token_is_rejected(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER)]
        )

        with self.assertRaises(InvalidToken):
            await self._resolve(
                users, InMemoryAuthorisationRepository()
            ).execute("not-a-token")

    async def test_token_for_deactivated_user_is_rejected(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER, active=False)]
        )

        with self.assertRaises(InvalidToken):
            await self._resolve(
                users, InMemoryAuthorisationRepository()
            ).execute("token:7")

    async def test_token_resolution_reloads_capabilities_from_authorisations(self) -> None:
        users = InMemoryUserRepository(
            [_user(id_user=7, role=UserRole.TRAINER)]
        )
        authorisations = InMemoryAuthorisationRepository()
        resolver = self._resolve(users, authorisations)

        before = await resolver.execute("token:7")
        self.assertFalse(before.capabilities.can_validate)

        await authorisations.create(
            Authorisation(
                id_trainer=7,
                id_workout_program=1,
                can_validate=True,
                start_date=date.today(),
            )
        )

        after = await resolver.execute("token:7")
        self.assertTrue(after.capabilities.can_validate)


class ActorCapabilitiesTests(unittest.TestCase):
    """The actor DTO remains backwards compatible and exposes capabilities."""

    def test_defaults_to_no_capabilities(self) -> None:
        actor = ActorDTO(id_user=3, role=UserRole.TRAINER)

        self.assertEqual(
            actor.capabilities,
            CapabilitiesDTO(can_generate=False, can_validate=False),
        )
        self.assertFalse(actor.can_generate())
        self.assertFalse(actor.can_validate())

    def test_keeps_explicit_capabilities(self) -> None:
        actor = ActorDTO(
            id_user=3,
            role=UserRole.TRAINER,
            capabilities=CapabilitiesDTO(can_generate=True, can_validate=True),
        )

        self.assertTrue(actor.can_generate())
        self.assertTrue(actor.can_validate())
