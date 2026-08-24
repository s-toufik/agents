from agentic.adapter.inbound.web.schema.agent_request_schema import AgentRequestSchema
from agentic.domain.model.agent_request import AgentRequest


def test_to_domain_maps_fields_one_to_one():
    schema = AgentRequestSchema(message="hi", model_name="gpt", request_id="req-1")

    domain = schema.to_domain()

    assert isinstance(domain, AgentRequest)
    assert domain.message == "hi"
    assert domain.model_name == "gpt"
    assert domain.request_id == "req-1"
