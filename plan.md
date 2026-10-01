=== MODELING A WORLD ===

Role: you transcribe entries from the account. Check: every entry quotes
the account; an entry you cannot quote, you cannot write.

Account: one external document, named here by title and location, written
by the world's practitioners, not by you. Check: it is loaded whole in
this session before the first entry; if it is not loaded, there are no
entries.

Standard: .agents/skills/python-development, read whole. Check: each
entry's kind is one of its thirteen forms.

Governing rule, restated verbatim before every entry, with the check:
  Name what exists and what it is made of. Every entry stands alone.
  Check: remove this entry; every other entry still means what it meant.

Terms, used exactly: account, thing, constituent, kind, entry
  entry = name / what it is / constituents / kind / quoted sentence

Method, one line per entry, in this order:
1. Input: one sentence of the account. Output: the thing it names, in the
   account's word. Check: the word appears in the quoted sentence.
2. Input: that sentence. Output: what the thing is made of, as other
   entries. Check: each constituent has its own entry with its own quote.
3. Input: that sentence or another quoted. Output: its kind. Check: the
   kind is an entry or a standard form.
4. Input: a sentence saying something follows. Output: the derived fact.
   Check: no derived fact without such a sentence.
5. Input: a sentence giving a reply's shape. Output: the reply as a thing
   with that shape. Check: the shape's parts are quoted.
6. Input: the finished entry. Output: kept or deleted. Check: 9 of the
   governing rule, applied now, not later.

Bound: declare the count; write entries only; stop and wait for review.
Check: output contains nothing but entries and the count.

Stop-list: no quote, deleted; fails the governing check, deleted; needs
an argument, deleted.

Exemplar, account sentence "a fill executes part of an order at a price
and quantity":
  Fill / an execution of part of an order / order, price, quantity /
  execution / "a fill executes part of an order at a price and quantity"

Name what exists and what it is made of. Every entry stands alone.
Check: remove this entry; every other entry still means what it meant.
=== END ===

=== ONTOK-EVENTS ===

World: event sourcing. Account: an external event-sourcing reference
named by title and location (EventStoreDB's documentation of events,
streams, expected version, projections, and subscriptions, or an
equivalent practitioner text). Check: loaded whole before any entry.

Kinds: ontok-core's fourteen primitives, from wiki/architecture/
ontok-core.md. Check: every entry's kind is a Core primitive, a standard
form, or another entry; an entry whose kind is none of these is deleted.

Extension to the entry form: a sixth part, the organizational fact the
account leaves implicit, in Core's word: which entity, which role toward
which goal, which occurrence it is because of, which rule in which
context. Check: the sixth part names a Core primitive or is empty; it
never names a step.

Boundary: an entry here is true of event sourcing on any provider. Check:
the quoted sentence contains no provider's name; a sentence that does
belongs to a provider package.

Propositions: list, as entries, what a provider must be able to prove:
an append under an expected version lands or is refused; a stream reads
whole; a condition is the fold of a stream; a subscription delivers each
event at least once until one of three dispositions; a read model holds
conditions as of a position. Check: each proposition quotes the account.

=== END ===

=== ONTOK-NATS ===

World: NATS JetStream. Account: NATS's own documentation, named by title
and location, for streams, subjects, publish acknowledgements and
expected-last-sequence headers, atomic batch, direct get, consumers and
acknowledgements, and key-value. Check: loaded whole before any entry.

Extension to the entry form: a sixth part, the ontok-events entry this
thing is, by name. Check: the sixth part names an Events entry, or the
entry is marked NATS-only with the quoted sentence that shows no Events
entry covers it.

Boundary: an entry here has the shape the account gives it, in the
account's words. Check: no constituent is a word the account does not
use; a constituent that is an Events word belongs in the sixth part, not
the third.

Correspondence: for each Events proposition, the entries that prove it,
by name. Check: a proposition with no entries is listed as unproven, not
argued.

Divergence: an Events thing with no NATS thing, or a NATS thing with no
Events thing, is listed as such with its quote. Check: no entry is
written to fill the gap.

=== END ===
