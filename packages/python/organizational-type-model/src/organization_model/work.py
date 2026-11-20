"""Declarative organizational concepts built from typed constituents.

Generic classes are authoring templates. A concrete specialization supplies the
actual domain, including every allowed case. Construction validates a declared
structure; it does not establish the truth of an external-world assertion.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .scalars import MODEL_CONFIG, ROOT_CONFIG


class Outcome[State](BaseModel, frozen=True):
    """A state resulting from, or intended through, organizational work."""

    model_config = MODEL_CONFIG
    state: State


class ProducedOutcome[State](Outcome[State], frozen=True):
    """An outcome in which the specified state is brought about."""

    kind: Literal["produced"] = "produced"


class MaintainedOutcome[State, Scope](Outcome[State], frozen=True):
    """An outcome in which a state holds throughout a specified scope."""

    kind: Literal["maintained"] = "maintained"
    throughout: Scope


class Purpose(RootModel[Annotated[tuple[object, ...], Field(min_length=1)]], frozen=True):
    """An intended end constituted by a nonempty composition of desired outcomes.

    Use an exact tuple for jointly required goals; use a union at a tuple position
    for alternatives, and constrained nested tuples for groups of like goals.
    """

    model_config = ROOT_CONFIG
    root: Annotated[tuple[object, ...], Field(min_length=1)]


class Rule[Context, Target](BaseModel, frozen=True):
    """A normative or validity relation with a typed scope and content."""

    model_config = MODEL_CONFIG
    context: Context
    target: Target


class Validity[Context, Target](Rule[Context, Target], frozen=True):
    """The target is valid in the declared context."""

    force: Literal["valid"] = "valid"


class Permission[Context, Target](Rule[Context, Target], frozen=True):
    """The target is permitted in the declared context."""

    force: Literal["permitted"] = "permitted"


class Requirement[Context, Target](Rule[Context, Target], frozen=True):
    """The target is required in the declared context."""

    force: Literal["required"] = "required"


class Prohibition[Context, Target](Rule[Context, Target], frozen=True):
    """The target is prohibited in the declared context."""

    force: Literal["prohibited"] = "prohibited"


class Responsibility(RootModel[Requirement[object, object]], frozen=True):
    """A duty associated with participation, including its applicability and end.

    The target can be specified work, a desired outcome, or a maintained condition;
    an outcome responsibility does not require an independently prescribed method.
    """

    model_config = ROOT_CONFIG
    root: Requirement[object, object]


class Role(RootModel[Annotated[tuple[Responsibility, ...], Field(min_length=1)]], frozen=True):
    """A nonempty composition of responsibilities, independent of its occupant."""

    model_config = ROOT_CONFIG
    root: Annotated[tuple[Responsibility, ...], Field(min_length=1)]


class Activity[Inputs, Outputs](BaseModel, frozen=True):
    """One admissible input/outcome case of a unit of organizational work.

    Where inputs and outcomes are correlated, declare separate complete subclasses
    and a tagged union of those subclasses. The declaration is not an occurrence.
    """

    model_config = MODEL_CONFIG
    inputs: Inputs
    outcomes: Outputs


class Process[Work, End: Purpose](Activity[Work, End], frozen=True):
    """A composite Activity whose desired outcome composition is its Purpose.

    Work is the concrete structure of prerequisite activities. Nest exact cases for
    dependencies, use products for jointly required work, and sums for alternatives.
    The end is represented once, in outcomes. Construction does not assert success.
    """


class Decision[Cases: BaseModel](RootModel[Cases], frozen=True):
    """A selection of one complete admissible context/rule/outcome case.

    The concrete Cases union is the alternative set. There is no independent list
    of alternatives and no independent selection field to reconcile with it.
    """

    model_config = ROOT_CONFIG


class DecisionPower[Scope](BaseModel, frozen=True):
    """Power to determine matters within a declared decision scope."""

    model_config = MODEL_CONFIG
    kind: Literal["decision_power"] = "decision_power"
    scope: Scope


class ObligationPower[Duty: Requirement[object, object]](BaseModel, frozen=True):
    """Power to establish the scoped duty; not an assertion it was imposed."""

    model_config = MODEL_CONFIG
    kind: Literal["obligation_power"] = "obligation_power"
    imposable: Duty


class ActionPermission[Context, Work](Permission[Context, Work], frozen=True):
    """Permission to perform work, used as one form of authority grant."""

    kind: Literal["action_permission"] = "action_permission"


type Grant = (
    ActionPermission[object, object]
    | DecisionPower[object]
    | ObligationPower[Requirement[object, object]]
)


class Authority[Holder, Basis, Power: Grant](BaseModel, frozen=True):
    """A formally established permission or power held within a typed scope."""

    model_config = MODEL_CONFIG
    holder: Holder
    established_by: Basis
    grant: Power


class Participation[Occupant, Position: Role](BaseModel, frozen=True):
    """An occupant participating under a role; no human/software restriction."""

    model_config = MODEL_CONFIG
    occupant: Occupant
    role: Position


class Communication[Sender, Recipients: tuple[object, ...], Content](BaseModel, frozen=True):
    """Information exchanged from a sender to one or more recipients."""

    model_config = MODEL_CONFIG
    kind: Literal["communication"] = "communication"
    sender: Sender
    recipients: Annotated[Recipients, Field(min_length=1)]
    content: Content


class ResponsibilityTransfer[Source, Destination, Duty: Responsibility](BaseModel, frozen=True):
    """A responsibility exchanged between two participation positions."""

    model_config = MODEL_CONFIG
    kind: Literal["responsibility_transfer"] = "responsibility_transfer"
    source: Source
    destination: Destination
    responsibility: Duty


class Coordination[Participants: tuple[object, ...], Work](BaseModel, frozen=True):
    """An exchange coordinating work among at least two participant positions."""

    model_config = MODEL_CONFIG
    kind: Literal["coordination"] = "coordination"
    participants: Annotated[Participants, Field(min_length=2)]
    work: Work


type Exchange = (
    Communication[object, tuple[object, ...], object]
    | ResponsibilityTransfer[object, object, Responsibility]
    | Coordination[tuple[object, ...], object]
)


class Interaction[Content: Exchange](RootModel[Content], frozen=True):
    """An exchange whose participant relationships are constituents of its form."""

    model_config = ROOT_CONFIG


class Event[Occurrence](BaseModel, frozen=True):
    """An assertion of what occurred, whether internal or external to the work.

    An Event can be a required constituent of later work. Timing and evidence can
    be added by domain specialization when meaningful; exact time is not universal.
    """

    model_config = MODEL_CONFIG
    occurred: Occurrence
