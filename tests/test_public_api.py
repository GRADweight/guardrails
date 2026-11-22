from __future__ import annotations

import inspect

import gradweight_guardrails


def test_public_names_exist_and_are_documented() -> None:
    for name in gradweight_guardrails.__all__:
        obj = getattr(gradweight_guardrails, name)
        if name == "__version__":
            assert isinstance(obj, str)
            continue
        assert inspect.getdoc(obj), f"{name} ohne Docstring"


def test_public_functions_are_annotated() -> None:
    for name in gradweight_guardrails.__all__:
        obj = getattr(gradweight_guardrails, name)
        if inspect.isfunction(obj):
            signature = inspect.signature(obj)
            assert signature.return_annotation is not inspect.Signature.empty, name
            for parameter in signature.parameters.values():
                assert parameter.annotation is not inspect.Parameter.empty, (name, parameter.name)
