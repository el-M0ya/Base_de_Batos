"""Application DTOs for training session registration and consultation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Optional

from app.application.dto.actor import ActorDTO
from app.domain.entities.training_session import TrainingSession


@dataclass(frozen=True)
class RegisterTrainingSessionInputDTO:
    actor: ActorDTO
    id_assignment: int
    session_date: date
    start_time: time
    end_time: time
    intensity_perceived: int
    completed: bool
    observations: Optional[str] = None


@dataclass(frozen=True)
class TrainingSessionOutputDTO:
    id_session: int
    id_assignment: int
    session_date: date
    start_time: time
    end_time: time
    intensity_perceived: Optional[int]
    completed: bool
    observations: Optional[str]

    @classmethod
    def from_entity(cls, session: TrainingSession) -> "TrainingSessionOutputDTO":
        if session.id_session is None:
            raise ValueError("A session output requires a persisted session.")
        return cls(
            id_session=session.id_session,
            id_assignment=session.id_assignment,
            session_date=session.session_date,
            start_time=session.start_time,
            end_time=session.end_time,
            intensity_perceived=session.intensity_perceived,
            completed=session.completed,
            observations=session.observations,
        )
