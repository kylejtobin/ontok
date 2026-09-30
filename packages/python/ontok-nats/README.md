# ontok-nats

The NATS JetStream realization of `ontok-events`: memory, delivery, and acknowledgement on one stream, with one interpreter per Events action and nothing of the organization inside.

- **Import:** `ontok.nats`
- **Python:** 3.14 or later
- **Depends on:** `ontok-events`, `nats-py`, `pydantic-settings`
- **Server:** NATS 2.14.6 or later, with the `EVENTS` stream declared by the deployment
- **Status:** pre-alpha
- **Architecture:** [wiki/architecture/ontok-nats.md](https://github.com/kylejtobin/ontok/blob/main/wiki/architecture/ontok-nats.md)

## Install

```bash
pip install "ontok-nats @ git+https://github.com/kylejtobin/ontok.git#subdirectory=packages/python/ontok-nats"
```

## Package

`ontok` is a PEP 420 implicit namespace: no `ontok/__init__.py` exists in any distribution. The wheel carries the source, `py.typed`, `LICENSE`, and `NOTICE`; distribution metadata is the sole version authority.
