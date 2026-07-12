from enterprise_adapters.contracts import AdapterContext, ReadOnlyResource


def test_contract_dataclasses() -> None:
    context = AdapterContext(adapter_name="phase3", environment="test")
    resource = ReadOnlyResource(resource_id="r1", name="sample")

    assert context.adapter_name == "phase3"
    assert resource.name == "sample"
