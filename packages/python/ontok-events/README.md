# ontok-events

An organization's memory and its work upon it, in ONTOK: occurrences about entities, the responsibilities that respond to them, delivery, and recording, stated as strict, frozen Pydantic facts in the `ontok` namespace.

- **Import:** `ontok.events`
- **Python:** 3.14 or later
- **Depends on:** `ontok-core`, `pydantic>=2.9,<3`; a provider realizes its actions
- **Status:** pre-alpha
- **Architecture:** [wiki/architecture/ontok-events.md](https://github.com/kylejtobin/ontok/blob/main/wiki/architecture/ontok-events.md)

## Install

```bash
pip install "ontok-events @ git+https://github.com/kylejtobin/ontok.git#subdirectory=packages/python/ontok-events"
```

## Package

`ontok` is a PEP 420 implicit namespace: no `ontok/__init__.py` exists in any distribution. The wheel carries the source, `py.typed`, `LICENSE`, and `NOTICE`; distribution metadata is the sole version authority.
