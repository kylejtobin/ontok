# ROUGH PLAN: ontok-eventcatalog

Preserved as written, before any modeling. This is the idea, not the design; the design is written as an architecture page when the module is built, under the project-knowledge protocol.

---

EventCatalog is probably the most interesting one for you. It visualizes domains, systems, services, messages, flows, owners, dependencies, and business flows, and can generate views from AsyncAPI/OpenAPI/schema registries. It is open source and exposes an SDK/visualizer ecosystem.

ONTOK could visualize organizational causality.

That is a much richer object then what is normally visualized in event visualization tools.

Once ONTOK Events is running, you don't merely know:

> Service A emitted OrderPaid, Consumer B received it.

You can potentially know:

> This OrderPaid occurrence changed the remembered history of this Order, activated this Responsibility, acting through this Role toward this Goal, under this organizational context, which emitted OrderShipped, with explicit provenance back to the causal occurrence.

That gives you views existing EDA tools largely cannot produce.

I think the eventual ONTOK visualization naturally breaks into three coordinated views:

1. Organization map. The relatively stable model: Entity → Relation → Role → Goal → Rule → Work → Concept. This is the declared organization.

2. Live operating graph. What is happening now: events flowing into responsibilities, work firing, state changing, effects executing, humans/software/models participating. This is the organization running.

3. Entity history / causal trace. Click one customer/order/project/incident and see: Event → State → Responsibility → Decision/Work → Event → State, with provenance and causation intact. This is basically a distributed trace for organizational reality, rather than merely a distributed trace for software calls.

And I would not immediately build all the infrastructure UI yourself.

The really attractive path is probably: ONTOK → projections → existing visualization systems.

For example:

- project ONTOK event contracts to AsyncAPI;
- project services/messages/flows into EventCatalog;
- let NATS tooling expose broker-level health;
- let OpenTelemetry/Grafana expose infrastructure execution;
- build only the ONTOK-specific semantic layer that none of those tools understands.

EventCatalog is especially interesting because its current product direction is almost eerily adjacent to what you're thinking: domains, systems, services, messages, business flows, connected architecture, Git-backed modeling, and a standalone visualizer.

Where ONTOK goes beyond it is that EventCatalog primarily describes architecture. ONTOK's graph can be the thing actually executing.

That's the part I think is potentially visually extraordinary: not another architecture diagram, but a live, navigable model of the organization where declared structure and actual execution occupy the same graph.

And the licensing is favorable enough that I would seriously consider it.

The important distinction is that I would not start by forking all of EventCatalog and turning it into ONTOK. I'd build an ONTOK integration against the parts EventCatalog deliberately exposes for this purpose.

EventCatalog's main repository explicitly says it uses a mixed-license model: most of the repository is MIT, while particular paid-feature directories use their commercial license. It also publishes @eventcatalog/sdk for programmatic catalog management and a standalone @eventcatalog/visualiser React component, and their docs explicitly say you can use the SDK to build custom plugins.

So I think the clean architecture is something like:

```text
ONTOK
  │
  ├── declared ontology
  ├── responsibilities / work
  ├── events / provenance
  ├── runtime state
  │
  ▼
ontok-eventcatalog
  │
  ├── projects ONTOK kinds → EventCatalog resources
  ├── projects responsibilities → flows
  ├── projects events → messages
  ├── projects roles → ownership / actors
  └── adds ONTOK-specific metadata
  │
  ▼
EventCatalog
  │
  ├── architecture browser
  ├── search / navigation
  ├── static topology
  └── visualization
```

Then add one custom ONTOK visualization layer for the part EventCatalog doesn't natively understand:

```text
Declared graph          Runtime graph
──────────────          ─────────────
Role                    Event instance
Goal                    Delivery
Responsibility          Provenance
Event kind              Causation
Rule                    Current state
Entity kind             Execution status
```

That is where you'd get the interesting live experience.

## Licensing

For the MIT-licensed portions, yes: you can use them, modify them, redistribute them, include them in a commercial product, and build derivative works. The normal MIT obligation is essentially preserving the copyright and license notice.

Where you need to be careful is that the EventCatalog ecosystem is not uniformly MIT. The main monorepo contains commercially licensed feature directories, and some separate EventCatalog plugins/products use AGPL, BSL, or commercial terms. For example, their EventBridge generator is AGPL/commercial dual-licensed, while some other components explicitly require commercial licensing for proprietary use.

So the rule I'd use is: depend only on components whose license you have explicitly checked. Do not infer the license of an EventCatalog plugin from the license of EventCatalog Core.

For ONTOK specifically, I think the safest and architecturally best route is:

- ONTOK remains Apache 2.0.
- ontok-eventcatalog is your own Apache 2.0 integration.
- It consumes the public EventCatalog SDK / MIT components and emits EventCatalog-native resources. If you need deeper UI behavior, use or fork only the MIT visualizer/core portions and retain their notices.

That keeps a very clean legal boundary.

There is also a product reason I like this more than a hard fork: EventCatalog remains a projection of ONTOK, not part of ONTOK's ontology or runtime. If EventCatalog disappears tomorrow, the organizational model survives untouched. You could replace the visualization layer without changing what the organization means.

And technically, EventCatalog is already unusually well positioned for this. Its current model includes domains, systems, services, messages, flows, entities, data stores, ownership, schemas, and custom documentation. It also has custom MDX components and a standalone visualizer.

The one thing I would not confuse it with is a runtime observability system. EventCatalog is primarily architecture/catalog visualization. For the live ONTOK view, you'd probably add a component that subscribes to an ONTOK runtime projection and overlays: what exists → what is happening → why it happened.

That combination could be extremely good. EventCatalog gives you 70–80% of the boring architecture-navigation work, while ONTOK supplies the part that actually makes the visualization novel.
