# Ontok — Organizational work and value — Kinds and narrowing

First edition

## Foreword

This document was prepared by the Ontok project. This is the first edition.

The structure and wording of this document follow the drafting rules of the ISO/IEC Directives, Part 2 (see Reference [1]). This document is not a publication of ISO or IEC.

In this document, the following verbal forms are used:

- "shall" indicates a requirement;
- "should" indicates a recommendation;
- "may" indicates a permission;
- "can" indicates a possibility or a capability.

## Introduction

Organizations specify their data. They specify what they have, how it is measured, and the trace that work leaves behind. They rarely specify the work: what can happen, in what state, who answers for it, under what authority, and what it is for. That meaning is spread across tools, settings and people, written many times and agreed nowhere.

This document gives that meaning one form. It establishes nineteen kinds, ten of organizational work and nine of value, and one relationship, narrowing, by which an organization makes those kinds its own. An organization states once what its work is, who answers for it, under what bounds, toward what end, and what it is worth. People, programs and agents then do the work from that one statement, and a result can be measured against it.

The kinds are defined by their meanings and by what each is composed of. They are defined by no notation and no programming language. A data model, a schema or program code can be produced from them, and this document replaces none of those.

This document specifies what can be declared. It runs nothing.

## 1 Scope

This document defines nineteen kinds of organizational work and value, and the terms needed to state them.

This document specifies:

- the constituents that each of the nineteen kinds requires;
- narrowing, the relationship by which an organization declares its own kinds from the nineteen;
- the conditions under which a set of declarations, or a representation of the nineteen kinds, conforms.

This document is applicable to any organization that declares its work and the value of that work, and to any notation, schema language or programming language in which such declarations are represented.

This document does not specify a notation, a programming language, a data model, storage, or the execution of work. This document does not specify the kinds that an organization declares for its own subject matter.

## 2 Normative references

There are no normative references in this document.

## 3 Terms and definitions

For the purposes of this document, the following terms and definitions apply.

### 3.1 Kinds and their construction

**3.1.1**\
**kind**\
category of thing determined by what each thing in it is composed of

**3.1.2**\
**position**\
named place within a *kind* (3.1.1) that is filled in each thing of that kind

Note 1 to entry: Holder, sender, recipient, subject and input are positions. A position is not a kind.

**3.1.3**\
**constituent**\
part that fills a *position* (3.1.2)

**3.1.4**\
**construction**\
composition of *constituents* (3.1.3) that satisfies a *kind* (3.1.1)

**3.1.5**\
**alternative**\
one of two or more *kinds* (3.1.1) of which exactly one fills a given *position* (3.1.2) in any one *construction* (3.1.4)

**3.1.6**\
**declaration**\
statement that establishes a *kind* (3.1.1)

**3.1.7**\
**narrowing**\
specialization of a *kind* (3.1.1) by restricting its permissible *constituents* (3.1.3), their kinds, cardinalities or relationships, or its *alternatives* (3.1.5), without changing the meaning of the kind

**3.1.8**\
**parent kind**\
*kind* (3.1.1) that a *narrowing* (3.1.7) specializes

**3.1.9**\
**narrowed kind**\
*kind* (3.1.1) that results from a *narrowing* (3.1.7)

**3.1.10**\
**foundational kind**\
*kind* (3.1.1) listed in Table 1

**3.1.11**\
**domain kind**\
*kind* (3.1.1), declared by an organization for its own subject matter, that is neither a *foundational kind* (3.1.10) nor a *narrowed kind* (3.1.9) derived from one

EXAMPLE A monetary amount in a stated currency, a customer account, a unit of a resource.

### 3.2 Work

**3.2.1**\
**state**\
condition in which something is

**3.2.2**\
**outcome**\
resulting or intended *state* (3.2.1) produced or maintained through organizational activity

Note 1 to entry: Whether an outcome is intended or has occurred is given by the kind that contains it. An outcome in a *purpose* (3.2.3) is intended. An outcome asserted by an *event* (3.2.13) is claimed to have occurred.

**3.2.3**\
**purpose**\
intended organizational end expressed through a composition of desired *outcomes* (3.2.2)

**3.2.4**\
**activity**\
unit of work that transforms inputs into defined *outcomes* (3.2.2)

**3.2.5**\
**process**\
organized composition of *activities* (3.2.4) that collectively accomplishes a *purpose* (3.2.3)

**3.2.6**\
**rule**\
declarative constraint or requirement governing what is valid, permitted, required, or prohibited

**3.2.7**\
**force**\
\<rule\> status of valid, permitted, required or prohibited that a *rule* (3.2.6) gives its target in its context

**3.2.8**\
**responsibility**\
duty, attached to participation in organizational work, stated as a *rule* (3.2.6) whose *force* (3.2.7) is required

**3.2.9**\
**role**\
defined set of *responsibilities* (3.2.8) associated with participation in organizational work

**3.2.10**\
**participation**\
association of an occupant with a *role* (3.2.9)

Note 1 to entry: The occupant can be a person or software.

**3.2.11**\
**authority**\
formally established permission or power to perform actions, make decisions, or create obligations

**3.2.12**\
**decision**\
determination that selects among possible *outcomes* (3.2.2) according to applicable *rules* (3.2.6) and available context

**3.2.13**\
**event**\
asserted occurrence that can trigger or affect organizational work

Note 1 to entry: An event states what is claimed to have happened. It is not proof that the occurrence happened.

**3.2.14**\
**interaction**\
exchange between participants that communicates information, transfers *responsibility* (3.2.8), or coordinates work

### 3.3 Value

**3.3.1**\
**need**\
condition or *state* (3.2.1) that its holder requires

**3.3.2**\
**interest**\
concern or stake that its holder has in something

**3.3.3**\
**value**\
worth or significance of something relative to a *need* (3.3.1), *interest* (3.3.2), or *purpose* (3.2.3), expressed through one or more *dimensions* (3.3.4) of benefit or harm

**3.3.4**\
**dimension**\
\<value\> aspect of worth in which benefit or harm is assessed separately from every other such aspect

**3.3.5**\
**assessment**\
\<value\> finding, on one *dimension* (3.3.4), of benefit, harm or no change, together with the detail that supports the finding

**3.3.6**\
**economic value**\
economic\
*value* (3.3.3) in money earned, saved, preserved, or made available

**3.3.7**\
**time value**\
time\
*value* (3.3.3) in time saved, gained, or made available

**3.3.8**\
**quality value**\
quality\
*value* (3.3.3) in fitness for purpose, correctness, and reliability

**3.3.9**\
**risk value**\
risk\
*value* (3.3.3) in reduced exposure to uncertain adverse outcomes

**3.3.10**\
**capability value**\
capability\
*value* (3.3.3) in increased ability to accomplish something

**3.3.11**\
**human welfare value**\
human welfare\
*value* (3.3.3) in satisfaction, wellbeing, safety, and fulfillment

**3.3.12**\
**relationship value**\
relationships\
*value* (3.3.3) in trust, loyalty, reputation, and strength of relationships

**3.3.13**\
**resource value**\
resources\
*value* (3.3.3) in availability and preservation of scarce assets or materials

## 4 General requirements

### 4.1 Foundational kinds

This document establishes the nineteen foundational kinds listed in Table 1.

**Table 1 — Foundational kinds**

| Foundational kind | Defined in | Parent kind | Constituents specified in |
| --- | --- | --- | --- |
| outcome | 3.2.2 | none | 6.1 |
| purpose | 3.2.3 | none | 6.2 |
| activity | 3.2.4 | none | 6.3 |
| process | 3.2.5 | activity | 6.4 |
| rule | 3.2.6 | none | 6.5 |
| role | 3.2.9 | none | 6.6 |
| authority | 3.2.11 | none | 6.7 |
| decision | 3.2.12 | none | 6.8 |
| event | 3.2.13 | none | 6.9 |
| interaction | 3.2.14 | none | 6.10 |
| value | 3.3.3 | none | 7.1 |
| economic value | 3.3.6 | value | 7.3 |
| time value | 3.3.7 | value | 7.4 |
| quality value | 3.3.8 | value | 7.5 |
| risk value | 3.3.9 | value | 7.6 |
| capability value | 3.3.10 | value | 7.7 |
| human welfare value | 3.3.11 | value | 7.8 |
| relationship value | 3.3.12 | value | 7.9 |
| resource value | 3.3.13 | value | 7.10 |

The meaning of each foundational kind is its definition in Clause 3. A declaration shall not change that meaning.

State, force, responsibility, participation, need, interest, dimension and assessment are defined in Clause 3 because the foundational kinds are composed of them. They are not foundational kinds.

### 4.2 Single statement

A kind shall state each fact once.

Where the validity of a construction would depend on two constituents agreeing with each other, the kind shall be declared so that only one of them is a constituent.

EXAMPLE 1 A process has no goal in addition to its purpose (see 6.4).

EXAMPLE 2 A decision has no list of options in addition to its alternatives (see 6.8).

### 4.3 Exclusion by form

A combination of constituents that is not valid shall not satisfy any declared kind.

A declaration shall exclude such a combination through the positions, kinds, cardinalities and alternatives that it states. A declaration shall not rely on a check applied to a completed construction.

### 4.4 Declaration, construction and occurrence

A declaration establishes a kind. It does not state that anything of that kind exists or has happened.

A construction of an activity or of a process states an admissible case of work. It does not state that the work was performed.

A construction of an event states a claim that an occurrence happened. It does not establish that the claim is true.

A construction of an authority states that a permission or power is held. It does not establish that the permission or power was validly conferred, or that it was exercised.

### 4.5 Identity and time

A foundational kind, and any narrowed kind derived from one, shall not have a constituent that identifies the construction.

A domain kind for a person, for a program, or for the thing being worked on may have an identifier as a constituent.

A kind shall not have a constituent that states when a declaration or a construction was made or changed. Such times belong to the record in which declarations and constructions are kept. This document does not specify that record.

NOTE Change is the history of what was recorded.

## 5 Narrowing

### 5.1 Relationship

Narrowing relates a narrowed kind to its parent kind.

Every construction that satisfies a narrowed kind shall satisfy its parent kind.

The definition given in Clause 3 for a foundational kind applies without change to every narrowed kind derived from it.

A narrowing of a narrowed kind is also a narrowing of every kind from which that narrowed kind is derived.

Declaring a narrowing does not establish a foundational kind.

EXAMPLE A refund purpose narrows purpose to a composition of exactly two outcomes: refund issued, and customer informed.

### 5.2 Permitted restrictions

A narrowing shall be made only by one or more of the following restrictions:

a) restricting the kind admitted in a position to a narrowed kind derived from the kind that the parent kind admits there;

b) where the parent kind does not restrict the kind admitted in a position, restricting that position to a stated kind;

c) restricting the number of constituents in a composition to a number or a range that the parent kind admits;

d) restricting a set of alternatives to a subset of it;

e) restricting which constituents occur together, by replacing a kind with alternatives each of which is a narrowed kind that admits one consistent combination.

### 5.3 Excluded changes

A narrowing shall not:

a) add a position that the parent kind does not have;

b) remove a position that the parent kind has;

c) admit a kind, a number of constituents, or an alternative that the parent kind does not admit;

d) change the meaning of the parent kind.

### 5.4 Domain kinds

A position whose kind this document does not restrict may be filled by a domain kind.

This document does not specify domain kinds. A domain kind shall satisfy Clause 4.

EXAMPLE 1 A monetary amount in a stated currency fills the extent position of an economic value (see 7.3).

EXAMPLE 2 A customer account fills the subject position of a value (see 7.1).

### 5.5 Admission of kinds

A kind should be declared only where it preserves a distinction of constituents or of meaning that no kind already declared preserves. A different name is not such a distinction.

A position shall not be declared as a kind.

A condition or a dependency shall be stated through the constituents and alternatives of the kinds concerned. It shall not be declared as a kind of its own.

## 6 Work

### 6.1 Outcome

An outcome shall have a state as a constituent. This document does not restrict the kind of the state.

An outcome shall be exactly one of the following alternatives:

a) a produced outcome, in which the state is brought about;

b) a maintained outcome, in which the state holds throughout a stated extent.

A maintained outcome shall have, as a constituent, the extent throughout which the state holds.

An outcome shall not have a constituent that states whether it is intended or has occurred.

The outcome in a purpose and the outcome asserted by an event may be of the same kind.

NOTE An intended outcome and an occurred outcome are one kind of thing in two places. A result can therefore be measured against a purpose.

### 6.2 Purpose

A purpose shall be a composition of one or more outcomes. It shall have no other constituent.

Outcomes that are jointly intended shall each fill a position in the composition.

Where any one of several outcomes satisfies the purpose at a position, those outcomes shall be alternatives at that position.

A group of like outcomes may fill a position as a nested composition with a stated cardinality.

### 6.3 Activity

An activity shall have the following constituents:

a) its inputs;

b) its outcomes.

The outcomes of an activity shall be an outcome, a composition of outcomes, or a purpose.

An activity may have no inputs.

A declared activity shall be one admissible case: every combination of inputs and outcomes that satisfies it shall be valid. Where only some outcomes follow from some inputs, each admissible combination shall be declared as a separate kind, and those kinds shall be alternatives.

Work that depends on other work shall have that work, or an event that asserts its outcome, among its inputs. Order among activities shall not be stated by any other means.

### 6.4 Process

A process is a narrowed kind derived from activity.

The inputs of a process shall be a composition of activities.

The outcomes of a process shall be a purpose. A process shall not have a purpose or a goal in any other position.

Activities that are jointly required shall each fill a position in the composition. Activities of which any one suffices shall be alternatives. An activity that depends on another activity shall have that activity among its inputs, as specified in 6.3.

NOTE A composition of jointly required activities does not state that they are performed at the same time.

### 6.5 Rule

A rule shall have the following constituents:

a) the context in which it applies;

b) the target that it governs;

c) its force.

The force of a rule shall be exactly one of the following:

- valid: the target is valid in the context;
- permitted: the target is permitted in the context;
- required: the target is required in the context;
- prohibited: the target is prohibited in the context.

### 6.6 Role

A responsibility shall be a rule whose force is required. Its target shall be work, an outcome, or a maintained outcome.

A responsibility may have an outcome as its target without any activity being stated.

A role shall be a composition of one or more responsibilities.

A role shall not have its occupant as a constituent.

A participation shall have the following constituents:

a) the occupant;

b) the role.

This document does not restrict the kind of the occupant.

NOTE A role can exist with no participation.

### 6.7 Authority

An authority shall have the following constituents:

a) the holder;

b) the basis on which it is formally established;

c) exactly one grant.

The grant shall be exactly one of the following alternatives:

- a permission to perform stated work, which is a rule whose force is permitted;
- a power to make decisions within a stated scope;
- a power to create a stated obligation, the obligation being a rule whose force is required.

This document does not restrict the kind of the holder.

### 6.8 Decision

The alternatives of a decision shall be complete cases. Each case shall bind together:

a) the context;

b) the rule that applies in that context;

c) the outcome that follows.

A construction of a decision shall be exactly one case.

A decision shall not have, as a constituent, a list of its alternatives or a separate statement of which alternative was selected.

NOTE The alternatives belong to the kind. A construction is one admissible selection.

### 6.9 Event

An event shall have, as a constituent, the occurrence that it asserts.

The occurrence may be an outcome, an interaction, or any other occurrence inside or outside the organization.

This document does not require an event to state when the occurrence happened or where it originated. The time of the occurrence and the evidence for it can be stated as constituents of the kind that fills the occurrence position.

An event shall not fill a position in a purpose.

An event may be an input of an activity.

### 6.10 Interaction

An interaction shall be exactly one of the following alternatives:

a) a communication, which shall have a sender, one or more recipients, and the content communicated;

b) a transfer of responsibility, which shall have a source, a destination, and the responsibility transferred, stated once;

c) a coordination, which shall have two or more participants and the work coordinated.

The same participant may fill more than one position of an interaction where the narrowed kind admits it.

NOTE An interaction is the exchange. An event can assert that an interaction occurred.

## 7 Value

### 7.1 Value

A value shall have the following constituents:

a) the subject that is valued;

b) the basis relative to which it is valued;

c) an assessment.

The basis shall be exactly one of a need, an interest, or a purpose.

A need shall have a holder and the condition or state that the holder requires.

An interest shall have a holder and the concern or stake of the holder.

A construction of a value shall satisfy exactly one of the kinds specified in 7.3 to 7.10. Each of those kinds is a narrowed kind derived from value that restricts the detail of the assessment.

Value on more than one dimension shall be stated as a composition of values, one for each dimension. Values on different dimensions shall not be combined into a single quantity.

### 7.2 Assessment

An assessment shall state exactly one of benefit, harm, or no change, together with the detail specified for its dimension in 7.3 to 7.10.

Where only some details are consistent with benefit, with harm, or with no change, a narrowing shall admit only the consistent combinations, as alternatives.

EXAMPLE A removal of exposure whose supporting detail is that the path of exposure remains open satisfies no kind.

The definitions in 3.3.6 to 3.3.13 name the change that is ordinarily a benefit. The opposite change on the same dimension is assessed on that dimension as well.

The direction of a change does not determine whether it is a benefit or a harm. The same change can be a benefit relative to one basis and a harm relative to another.

An extent, an appraisal or a standing may be qualitative, provided that its kind is stated.

### 7.3 Economic value

The detail of an assessment of economic value shall state:

a) the financial change, which is money earned, saved, preserved, or made available, or the opposite of one of these;

b) the extent of the change, as a monetary amount or as a stated qualitative extent.

### 7.4 Time value

The detail of an assessment of time value shall state:

a) the temporal change, which is time saved, gained, or made available, or the opposite of one of these;

b) the extent of the change, as a duration or as a stated temporal condition.

### 7.5 Quality value

The detail of an assessment of quality value shall be exactly one of the following alternatives:

a) fitness, which shall state a purpose and its attainment;

b) correctness, which shall state a rule whose force is required and the conformity to it;

c) reliability, which shall state a context, the outcome required in that context, and the observation of whether it was attained.

### 7.6 Risk value

The detail of an assessment of risk value shall state the adverse outcome concerned, which shall be an outcome, and exactly one of the following alternatives:

a) a change in the likelihood of the adverse outcome, with its extent;

b) a change in the consequence of the adverse outcome, with its extent;

c) the removal or the introduction of exposure to the adverse outcome, with the evidence for it.

### 7.7 Capability value

The detail of an assessment of capability value shall state:

a) the work concerned, which shall be an activity;

b) the change in the ability to accomplish that work, which is an increase or a decrease;

c) the evidence for the change.

### 7.8 Human welfare value

The detail of an assessment of human welfare value shall be exactly one of the following alternatives:

a) satisfaction, which shall state an expectation and its appraisal;

b) wellbeing, which shall state a condition of the person or persons concerned;

c) safety, which shall state a threat and the protection against it;

d) fulfillment, which shall state a purpose and its attainment.

### 7.9 Relationship value

The subject of a relationship value shall be the relationship or the related parties.

The detail of an assessment of relationship value shall be exactly one of the following alternatives:

a) trust, which shall state the conduct expected and its appraisal;

b) loyalty, which shall state a commitment and its appraisal;

c) reputation, which shall state an audience and the standing with that audience;

d) strength, which shall state an appraisal of the strength of the relationship.

### 7.10 Resource value

The subject of a resource value shall be the scarce asset or material concerned.

The detail of an assessment of resource value shall be exactly one of the following alternatives:

a) availability, which shall state the extent that is accessible;

b) preservation, which shall state the condition that is retained.

## 8 Conformance

### 8.1 Declarations

A set of declarations conforms to this document if all of the following hold:

a) each kind that it establishes is a foundational kind, a narrowed kind derived from a foundational kind, or a domain kind;

b) each foundational kind that it uses satisfies Clause 6 or Clause 7, as applicable;

c) each narrowing in it satisfies Clause 5;

d) the set satisfies Clause 4.

### 8.2 Representations

A representation of the foundational kinds in a notation, a schema language or a programming language conforms to this document if both of the following hold:

a) every construction that the representation admits satisfies this document;

b) every construction that satisfies this document can be stated in the representation.

## Bibliography

[1] ISO/IEC Directives, Part 2, *Principles and rules for the structure and drafting of ISO and IEC documents*. Ninth edition, 2021
