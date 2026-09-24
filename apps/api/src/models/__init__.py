"""SQLAlchemy models. Import every model here so Alembic autogenerate and
Base.metadata.create_all() can discover them via a single import."""

from src.core.db import Base
from src.models.auth_session import AuthSession
from src.models.availability import ExperienceAvailability
from src.models.category import ExperienceCategory
from src.models.conversation_message import ConversationMessage
from src.models.conversation_session import ConversationSession
from src.models.embedding import ExperienceEmbedding
from src.models.experience import Experience
from src.models.location import Location
from src.models.opening_hour import ExperienceOpeningHour
from src.models.provider import Provider
from src.models.traveler import Traveler
from src.models.user import User
from src.models.interaction import TravelerInteraction
from src.models.preference import TravelerPreference
from src.models.affinity import TravelerAffinity

__all__ = [
    "Base",
    "User",
    "Traveler",
    "Provider",
    "ExperienceCategory",
    "Location",
    "Experience",
    "ExperienceOpeningHour",
    "AuthSession",
    "ExperienceAvailability",
    "ConversationSession",
    "ConversationMessage",
    "ExperienceEmbedding",
    "TravelerInteraction",
    "TravelerPreference",
    "TravelerAffinity",
]
