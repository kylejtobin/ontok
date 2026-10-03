"""The bank the conformance tests run: its kinds, its identities, and the facts of one day."""

from datetime import UTC, datetime
from decimal import Decimal

from ontok.bank import Amount, Balance, Deposited, Withdrawn
from ontok.core import Goal, Instant, NodeId, Role, Timestamp
from ontok.events import (
    Append,
    AtVersion,
    Event,
    Events,
    Expectation,
    FromPosition,
    Initial,
    Occurrences,
    Position,
    Read,
    Start,
    State,
    StreamSubscription,
    Subscription,
    Version,
    VersionMismatch,
)

OPENING = Instant(at=Timestamp(datetime(2026, 10, 2, 9, 0, tzinfo=UTC)))

ACCOUNT_A = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a01")
ACCOUNT_B = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a02")
TELLER = Role(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a03"))
BOOKS_BALANCED = Goal(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a04"))

DEPOSIT_100 = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a11"), occurred=OPENING, amount=Amount(Decimal(100))
)
DEPOSIT_50 = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a12"), occurred=OPENING, amount=Amount(Decimal(50))
)
WITHDRAW_30 = Withdrawn(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a13"), occurred=OPENING, amount=Amount(Decimal(30))
)
DEPOSIT_10 = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a14"), occurred=OPENING, amount=Amount(Decimal(10))
)
WITHDRAW_20 = Withdrawn(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a15"), occurred=OPENING, amount=Amount(Decimal(20))
)
DEPOSIT_5A = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a16"), occurred=OPENING, amount=Amount(Decimal(5))
)
DEPOSIT_5B = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a17"), occurred=OPENING, amount=Amount(Decimal(5))
)
DEPOSIT_1 = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a18"), occurred=OPENING, amount=Amount(Decimal(1))
)
WITHDRAW_2 = Withdrawn(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a19"), occurred=OPENING, amount=Amount(Decimal(2))
)

A_EVENTS = Events(
    (
        Event(occurrence=DEPOSIT_100, stream=ACCOUNT_A, version=Version(1), position=Position(1)),
        Event(occurrence=DEPOSIT_50, stream=ACCOUNT_A, version=Version(2), position=Position(2)),
        Event(occurrence=WITHDRAW_30, stream=ACCOUNT_A, version=Version(3), position=Position(3)),
        Event(occurrence=WITHDRAW_20, stream=ACCOUNT_A, version=Version(4), position=Position(5)),
    )
)
B_EVENTS = Events(
    (
        Event(occurrence=DEPOSIT_10, stream=ACCOUNT_B, version=Version(1), position=Position(4)),
        Event(occurrence=DEPOSIT_5A, stream=ACCOUNT_B, version=Version(2), position=Position(6)),
        Event(occurrence=DEPOSIT_5B, stream=ACCOUNT_B, version=Version(3), position=Position(7)),
        Event(occurrence=WITHDRAW_2, stream=ACCOUNT_B, version=Version(4), position=Position(8)),
    )
)

MORNING_A = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a21"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_A,
    expected=Expectation.NO_STREAM,
    occurrences=Occurrences((DEPOSIT_100, DEPOSIT_50, WITHDRAW_30)),
)
MORNING_B = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a22"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_B,
    expected=Expectation.NO_STREAM,
    occurrences=Occurrences((DEPOSIT_10,)),
)
TRANSFER_OUT = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a23"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_A,
    expected=AtVersion(version=Version(3)),
    occurrences=Occurrences((WITHDRAW_20,)),
)
TRANSFER_IN = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a24"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_B,
    expected=AtVersion(version=Version(1)),
    occurrences=Occurrences((DEPOSIT_5A, DEPOSIT_5B)),
)
STALE_DEPOSIT = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a25"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_A,
    expected=AtVersion(version=Version(3)),
    occurrences=Occurrences((DEPOSIT_1,)),
)
CASH_MACHINE = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a26"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_B,
    expected=Expectation.ANY,
    occurrences=Occurrences((WITHDRAW_2,)),
)

MORNING_A_LANDS_AT = Position(3)
MORNING_B_LANDS_AT = Position(4)
TRANSFER_OUT_LANDS_AT = Position(5)
TRANSFER_IN_LANDS_AT = Position(7)
STALE_DEPOSIT_REFUSED = VersionMismatch(expected=AtVersion(version=Version(3)))
CASH_MACHINE_LANDS_AT = Position(8)

READ_A = Read(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a31"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_A,
    after=Start.BEGINNING,
)
READ_B = Read(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a32"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_B,
    after=Start.BEGINNING,
)

CLERK = Subscription(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a41"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    begins=Start.BEGINNING,
)
FRAUD_ANALYST = StreamSubscription(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a42"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    begins=Start.NOW,
    stream=ACCOUNT_A,
)
AUDITOR = StreamSubscription(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a43"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    begins=FromPosition(position=Position(6)),
    stream=ACCOUNT_B,
)

A_OPENING = Initial(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a51"), stream=ACCOUNT_A)
A_AFTER_100 = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a52"), prior=A_OPENING, event=A_EVENTS.root[0]
)
A_AFTER_50 = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a53"), prior=A_AFTER_100, event=A_EVENTS.root[1]
)
A_AFTER_30 = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a54"), prior=A_AFTER_50, event=A_EVENTS.root[2]
)
A_AFTER_20 = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a55"), prior=A_AFTER_30, event=A_EVENTS.root[3]
)

BALANCE_A = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a61")
BALANCE_A_MORNING = Balance(
    id=BALANCE_A, stream=ACCOUNT_A, position=Position(3), amount=Amount(Decimal(120))
)
BALANCE_A_AFTER_TRANSFER = Balance(
    id=BALANCE_A, stream=ACCOUNT_A, position=Position(5), amount=Amount(Decimal(100))
)

B_OPENING = Initial(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a56"), stream=ACCOUNT_B)
B_AFTER_10 = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a57"), prior=B_OPENING, event=B_EVENTS.root[0]
)
B_AFTER_5A = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a58"), prior=B_AFTER_10, event=B_EVENTS.root[1]
)
B_AFTER_5B = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a59"), prior=B_AFTER_5A, event=B_EVENTS.root[2]
)

READ_NOWHERE = Read(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a33"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a0f"),
    after=Start.BEGINNING,
)

DEPOSIT_7 = Deposited(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a1a"), occurred=OPENING, amount=Amount(Decimal(7))
)
LATE_DEPOSIT = Append(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a27"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    stream=ACCOUNT_A,
    expected=AtVersion(version=Version(4)),
    occurrences=Occurrences((DEPOSIT_7,)),
)
LATE_DEPOSIT_LANDS_AT = Position(9)
LATE_EVENT = Event(occurrence=DEPOSIT_7, stream=ACCOUNT_A, version=Version(5), position=Position(9))

BOOKKEEPER = Subscription(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a44"),
    role=TELLER,
    goal=BOOKS_BALANCED,
    begins=Start.BEGINNING,
)
