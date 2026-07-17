"""The entrypoint of the example package.

ForgeML never imports or executes this file during validation -- that is the
package system's central security guarantee. It is executed only inside the
isolated model runtime container, which a later module builds.
"""


def predict(document: dict[str, float]) -> dict[str, float]:
    """Receive one document matching input.schema, return one matching output.schema."""

    return {"score": float(document["value"]) * 2}
