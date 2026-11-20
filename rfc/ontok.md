# Ontok

Ontok is the shared semantic foundation for stating what an organization's work is and what that work is worth. It consists of nineteen kinds with agreed definitions, the relationships those definitions require, and narrowing, by which an organization builds increasingly specific models from the nineteen.

Ontok defines the semantics. It runs nothing, and it is defined by no programming language. Bindings express it: the Python binding expresses it through Pydantic types, and an RDF binding represents it for graph use. A binding does not redefine Ontok.

## 1. The nineteen kinds

### 1.1 Work

| Kind | Definition |
| --- | --- |
| Purpose | An intended organizational end expressed through a composition of desired outcomes. |
| Activity | A unit of work that transforms inputs into defined outcomes. |
| Process | An organized composition of activities that collectively accomplishes a purpose. |
| Role | A defined set of responsibilities associated with participation in organizational work. |
| Authority | The formally established permission or power to perform actions, make decisions, or create obligations. |
| Rule | A declarative constraint or requirement governing what is valid, permitted, required, or prohibited. |
| Decision | A determination that selects among possible outcomes according to applicable rules and available context. |
| Event | An asserted occurrence that may trigger or affect organizational work. |
| Interaction | An exchange between participants that communicates information, transfers responsibility, or coordinates work. |
| Outcome | A resulting or intended state produced or maintained through organizational activity. |

### 1.2 Value

| Kind | Definition |
| --- | --- |
| Value | The worth or significance of something relative to a need, interest, or purpose, expressed through one or more dimensions of benefit or harm. |
| Economic | Money earned, saved, preserved, or made available. |
| Time | Time saved, gained, or made available. |
| Quality | Fitness for purpose, correctness, and reliability. |
| Risk | Reduced exposure to uncertain adverse outcomes. |
| Capability | Increased ability to accomplish something. |
| Human Welfare | Satisfaction, wellbeing, safety, and fulfillment. |
| Relationships | Trust, loyalty, reputation, and strength of relationships. |
| Resources | Availability and preservation of scarce assets or materials. |

The eight dimensions specialize Value.

The nineteen definitions establish what Ontok must be able to represent. They are not a mandate to create exactly nineteen types in a model.

## 2. What the definitions require

Each definition requires certain constituents and relationships to be expressible. How a constituent is represented belongs to the binding.

**Outcome.** A state, and whether it is produced or maintained. Whether an Outcome is intended or has occurred is not part of the Outcome. The kind that contains it supplies that: inside a Purpose it is intended, and inside an Event it is asserted to have occurred. An intended result and an occurred result are therefore one kind of thing in two places.

**Purpose.** A composition of desired Outcomes, distinguishing Outcomes that are required together from Outcomes that are alternatives.

**Activity.** The inputs it admits and the outcomes related to them. Where particular inputs lead to particular outcomes, each admissible case is stated as a whole.

**Process.** Activities composed, with the dependencies among them, toward a Purpose. The Purpose is stated once. A Process does not hold a second, independent goal.

**Rule.** A context, a target, and a force. The force is one of valid, permitted, required, or prohibited.

**Role.** Responsibilities, associated with participation in work. Who occupies a Role is a separate fact from the Role. The occupant can be a person, a program, or no one yet.

**Authority.** A holder, the formal basis that establishes it, and what it grants. A grant to perform actions, a grant to make decisions, and a grant to create obligations are distinct.

**Decision.** Complete admissible cases, and one case selected. A complete case binds its context, the rule that applies, and the result, so a context from one case cannot be combined with a result from another. The permissible alternatives belong to the declaration of the Decision. A constructed Decision is one admissible selection. There is no independently populated list of alternatives that could contradict that selection.

**Event.** The occurrence that is asserted. An Event establishes what is claimed to have happened. It is not independent proof that the occurrence happened. Its effect on work is expressed by the work that depends on it. An exact time is not universal to Events.

**Interaction.** The participants in their positions, the content, and the direction or coordination structure of the exchange.

**Value.** The subject that is valued, the basis of its worth, and an assessment on one or more dimensions.

- The basis is a need, an interest, or a purpose.
- Benefit and harm are determined relative to that basis. The direction of a measurement is not its value: the same change can be a benefit relative to one basis and a harm relative to another.
- An assessment can find benefit, harm, or no change.
- Value on several dimensions is a composition of assessments. The dimensions are never collapsed into one number.

**Relationships among the kinds.**

- A requirement, which is a Rule whose force is required, is what a responsibility is and what an Authority's power to create obligations concerns.
- Purpose is the end of a Process, a basis of worth, and the counterpart of fitness in Quality and of fulfillment in Human Welfare.
- Activity is what a Process composes and what Capability concerns.
- Outcome is what a Purpose composes, what an Event can assert, and what Risk regards as adverse.
- For Relationships, the relationship being valued is the subject of the Value, stated once.

## 3. Foundational kinds, constituents, positions, and domain types

Four things are kept distinct.

**Foundational kinds.** The nineteen kinds in Clause 1 and the semantic relationships they require.

**Necessary semantic constituents.** Decomposing the definitions reveals further meanings needed to express them faithfully. A necessary constituent is not another foundational kind.

- State: the condition that an Outcome concerns. Its content is supplied by the domain, not by a universal vocabulary of states.
- Responsibility: a duty associated with participation. It can specify an end without prescribing a method.
- Need: a holder and what the holder requires.
- Interest: a holder and the holder's concern.

**Positions.** Holder, sender, recipient, subject, and input are positions within relationships. A position does not by its presence justify an independent kind.

**Domain-specific types.** Money, quantities, currencies, particular resource units, customer accounts, and similar types are constructed when modeling a particular domain. Ontok supports their precise representation and does not prescribe their existence or their structure.

Conditions and dependencies are essential. They are expressed structurally, through the composition, constraints, and relationships of kinds. They are not promoted into additional top-level kinds.

The mechanisms of a binding, such as primitives, constrained scalars, tuples, unions, and inheritance, express these meanings. Their presence creates no additional ontological commitment.

### 3.1 Admission

Before a constituent type is introduced, establish what semantic distinction it represents and whether that distinction is necessary to preserve the meaning of the kind being modeled. Then determine whether it is:

- a general constituent required by Ontok's agreed semantics;
- a specialization or composition of existing constituents;
- a domain-specific type needed for a particular model;
- an implementation mechanism that creates no new ontological meaning.

A type does not join Ontok's universal vocabulary because it was useful in an example. A necessary distinction is not eliminated because it can be implemented with a primitive or another type.

## 4. Narrowing

Narrowing is the specialization of an existing kind by restricting its permissible constituents, types, cardinalities, relationships, or alternatives without changing the underlying meaning of the kind.

A narrowed kind admits a subset of the valid constructions admitted by its parent. Anything valid as the narrowed kind is valid as its parent. A narrowed kind can require additional constituents and remain valid under its parent: the requirement is semantic substitutability, not an identical layout.

A narrowed kind can become increasingly specific to a business or a domain without introducing another foundational kind.

Narrowing is an ontological relationship. Inheritance, typed composition, and constrained unions are mechanisms a binding uses to express it.

## 5. Valid construction

The meaning of a model is established bottom-up, through its constituents, relationships, permissible alternatives, and constraints. Its valid construction establishes its structural semantics.

- **Required together, or alternative.** Constituents that are required together are stated together. Legitimate alternatives are stated as alternatives, each a complete case.
- **Nothing is said twice.** If two statements would have to agree, one of them is removed.
- **A wrong combination has no form.** An invalid combination is excluded by how things are built. Constraints are placed on the constituents and are not deferred to a later check.
- **Declaring is not doing, and asserting is not proving.** A defined Activity has not been performed. A recorded Event is a claim about the world. A stated Authority is a claim that a permission or power is held.
- **Identity belongs to particulars, and time belongs to the record.** A person, a program, and the thing being worked on carry identity. Definitions do not. Change is the history of what was recorded.

## 6. Bindings

Ontok defines the semantics. A binding expresses them in a particular language or representation, and no binding redefines them.
