from ontok.core import Work
from ontok.events.responsibility import ConjunctionResponsibility, Responsibility
from ontok.events.type import WorkTypeName


class Policy(Work):
    """The standing undertaking of a responsibility that derives occurrences from an entity's
    condition and an occurrence."""

    @property
    def responsibility(self) -> Responsibility:
        return Responsibility.model_validate(self.action, from_attributes=True)

    @property
    def work_type(self) -> WorkTypeName:
        return self.responsibility.work_type


class Conjunction(Work):
    """The standing undertaking of a responsibility that derives occurrences when two kinds of
    occurrence about one entity have both happened."""

    @property
    def responsibility(self) -> ConjunctionResponsibility:
        return ConjunctionResponsibility.model_validate(self.action, from_attributes=True)

    @property
    def work_type(self) -> WorkTypeName:
        return self.responsibility.work_type


class Projection(Work):
    """The standing undertaking of a responsibility that maintains a read model and derives no
    occurrences."""

    @property
    def responsibility(self) -> Responsibility:
        return Responsibility.model_validate(self.action, from_attributes=True)

    @property
    def work_type(self) -> WorkTypeName:
        return self.responsibility.work_type
