# ontok-bus

The provider-independent event transport domain for ONTOK.

## Namespace

`ontok.bus`

## Responsibility

Makes the ideas required to publish, deliver, route, acknowledge, and recover constructed facts explicit without making any event platform the semantic authority. ONTOK classes and successfully constructed facts remain the source of meaning; provider accounts of transporting them stay in provider packages.

It depends one-way on `ontok-core` and remains independent of other extension packages. Provider packages depend inward on it and implement its declared contracts. It is not a broker client, provider bundle, generic message envelope, or ontology registry.

## Status

Withheld from publication. The build plan lives in [PLAN.md](PLAN.md).
