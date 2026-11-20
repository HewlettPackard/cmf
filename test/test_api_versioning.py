from server.app.api.v1.metadata import router as metadata_router
from server.app.api.v1.pipelines import router as pipelines_router
from server.app.api.v1.servers import router as servers_router


def test_versioned_routers_are_registered():
    routes = []
    for router in (metadata_router, pipelines_router, servers_router):
        routes.extend(route.path for route in router.routes if hasattr(route, "path"))

    assert "/v1/mlmd/push" in routes
    assert "/v1/mlmd/pull" in routes
    assert "/v1/pipelines" in routes
    assert "/v1/servers/register" in routes
    assert "/v1/servers/sync" in routes
    assert "/v1/executions" in routes
    assert "/v1/executions/stages" in routes
    assert "/v1/artifacts" in routes
    assert "/v1/artifacts/types" in routes
    assert "/v1/schedules" in routes
    assert "/v1/schedules/{schedule_id}" in routes
    assert "/v1/lineage/execution/{uuid}/{pipeline_name}" in routes
    assert "/v1/lineage/artifact/{pipeline_name}" in routes
