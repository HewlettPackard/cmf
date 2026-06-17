from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from server.app.db.dbconfig import get_db
from sqlalchemy import select, func, text, String, Double, bindparam, case, distinct, insert, update, or_
from server.app.db.dbmodels import (
    artifact, 
    artifactproperty, 
    context, 
    parentcontext, 
    attribution, 
    type_table, 
    association,
    execution,
    executionproperty,
    event,
    registered_servers,
    label_content,
    scheduled_syncs,
    sync_logs
)
import time
from sqlalchemy.dialects.postgresql import insert as pg_insert


async def register_server_details(db: AsyncSession, server_name: str, server_url: str):
    """
    Register server details in the database.
    """
    # Check duplicate server name.
    query_name_check = select(registered_servers.c.id).where(
        registered_servers.c.server_name == server_name
    )
    result = await db.execute(query_name_check)
    exists_name = result.scalar()

    if exists_name:
        return {"message": "Server name already exists. Please use a unique server name"}

    # Step 2: Insert new server
    query_insert = insert(registered_servers).values(
        server_name=server_name,
        host_info=server_url,
    )
    await db.execute(query_insert)
    await db.commit()

    return {"message": "Server registered successfully"}


async def get_registered_server_details(db: AsyncSession = Depends(get_db())):
    """
    Get all registered server details from the database.
    """
    query = select(registered_servers)
    result = await db.execute(query)
    return result.mappings().all()


async def get_registered_server_by_id(db: AsyncSession, server_id: int):
    """Return one registered server row by primary key, or None."""
    query = select(registered_servers).where(registered_servers.c.id == server_id)
    result = await db.execute(query)
    row = result.mappings().first()
    return row


async def get_registered_server_by_name_url(db: AsyncSession, server_name: str, server_url: str):
    """Fetch one registered server row by server name and host URL."""
    query = select(registered_servers).where(
        (registered_servers.c.server_name == server_name) & (registered_servers.c.host_info == server_url)
    )
    result = await db.execute(query)
    return result.mappings().first()
    

async def get_sync_status(db: AsyncSession, server_name: str, server_url: str):
    """
    Get the sync status from the database.
    """
    query = select(registered_servers.c.last_sync_time).where(
        (registered_servers.c.server_name == server_name) & 
        (registered_servers.c.host_info == server_url)
    )
    result = await db.execute(query)
    return result.mappings().all()


async def update_sync_status(db: AsyncSession, current_utc_time: int, server_name: str, server_url: str):
    """Update last sync timestamp for a server identified by name and URL."""
    query = update(registered_servers).where(
        (registered_servers.c.server_name == server_name) & 
        (registered_servers.c.host_info == server_url)
    ).values(last_sync_time=current_utc_time)
    await db.execute(query)
    await db.commit()  # Commit the transaction


# Deprecated legacy query (unused by current stage-based UI/API flow).
# Kept for reference to support possible rollback to /artifacts/{pipeline_name}/{artifact_type}.
# async def fetch_artifacts(
#     db: AsyncSession,   # Used to interact with the database
#     pipeline_name: str, 
#     artifact_type: str, 
#     filter_value: str, 
#     active_page: int = 1, 
#     page_size: int = 5,  # Number of records per page
#     sort_column: str = "name", 
#     sort_order: str = "ASC"
# ):
#     # Step 1: Get relevant contexts
#     relevant_contexts_cte = select(
#         parentcontext.c.context_id
#     ).join(
#         context, parentcontext.c.parent_context_id == context.c.id
#     ).where(
#         context.c.name == pipeline_name
#     ).cte("relevant_contexts_cte")

#     # Early check: are there any relevant contexts for the given pipeline?
#     res = await db.execute(select(relevant_contexts_cte.c.context_id))
#     context_ids = res.scalars().all()
#     if not context_ids:
#         # No relevant contexts found, return empty result
#         return {"total_items": 0, "items": []}

#     # Step 2: Fetch execution IDs based on pipeline name
#     execution_ids_cte = (
#         select(
#             execution.c.id.label("execution_id")
#         )
#         .join(
#             association, execution.c.id == association.c.execution_id
#         )
#         .where(
#             association.c.context_id.in_(context_ids)
#         )
#         .cte("execution_ids_cte")
#     )

#     # Fetch all execution IDs for the relevant pipeline contexts
#     res = await db.execute(select(execution_ids_cte.c.execution_id))
#     execution_ids = res.scalars().all()
#     if not execution_ids:
#         # No executions found for the pipeline, return empty result
#         return {"total_items": 0, "items": []}

#     # Step 3: Based on execution ids list fetching equvalent artifact lists from event_path table
#     artifact_ids_cte = (
#         select(distinct(event.c.artifact_id).label("artifact_id"))
#         .where(event.c.execution_id.in_(execution_ids))
#         .cte("artifact_ids_cte")
#     )

#     # Fetch all artifact IDs for the relevant executions
#     res = await db.execute(select(artifact_ids_cte.c.artifact_id))
#     artifact_ids = res.scalars().all()
#     if not artifact_ids:
#         # No artifacts found for the executions, return empty result
#         return {"total_items": 0, "items": []}

#     # Step 4: Aggregate artifact properties into JSON
#     artifact_properties_agg_cte = (
#         select(
#             artifactproperty.c.artifact_id,
#             func.json_agg(
#                 func.json_build_object(
#                     "name", artifactproperty.c.name,
#                     "value", func.coalesce(
#                         artifactproperty.c.string_value,
#                         func.cast(artifactproperty.c.bool_value, String),
#                         func.cast(artifactproperty.c.double_value, String),
#                         func.cast(artifactproperty.c.int_value, String),
#                         func.cast(artifactproperty.c.byte_value, String),
#                         func.cast(artifactproperty.c.proto_value, String),
#                         text("NULL")
#                     )
#                 )
#             ).label("artifact_properties")
#         )
#         .where(artifactproperty.c.artifact_id.in_(artifact_ids)) # Filter by artifact IDs
#         .group_by(artifactproperty.c.artifact_id)
#         .cte("artifact_properties_agg_cte")
#     )

#     # Step 5: Aggregate execution type names per artifact
#     artifact_execution_types_agg_cte = (
#         select(
#             event.c.artifact_id,
#             func.string_agg(func.distinct(context.c.name), ', ').label("execution")
#         )
#         .join(execution, event.c.execution_id == execution.c.id)
#         .join(association, execution.c.id == association.c.execution_id)
#         .join(context, association.c.context_id == context.c.id)
#         .where(event.c.artifact_id.in_(artifact_ids))
#         .group_by(event.c.artifact_id)
#         .cte("artifact_execution_types_agg_cte")
#     )

#     # Step 6: Base artifact metadata
#     artifact_metadata_cte = (
#         select(
#             artifact.c.id.label('artifact_id'),
#             artifact.c.name,
#             artifact.c.uri,
#             func.to_char(
#                 func.timezone('GMT', func.to_timestamp(artifact.c.create_time_since_epoch / 1000)),
#                 'Dy, DD Mon YYYY HH24:MI:SS GMT'
#             ).label('create_time_since_epoch'),
#             artifact.c.last_update_time_since_epoch
#         )
#         .join(type_table, artifact.c.type_id == type_table.c.id)
#         .join(attribution, artifact.c.id == attribution.c.artifact_id)
#         .join(context, attribution.c.context_id == context.c.id)
#         .where(
#             artifact.c.id.in_(artifact_ids),
#             type_table.c.name == artifact_type
#         )
#         .cte("artifact_metadata_cte")
#     )

#     # Step 7: Query for fetching paginated data
#     query = (
#         select(
#             artifact_metadata_cte.c.artifact_id,
#             artifact_metadata_cte.c.name,
#             artifact_execution_types_agg_cte.c.execution,
#             artifact_metadata_cte.c.uri,
#             artifact_metadata_cte.c.create_time_since_epoch,
#             artifact_metadata_cte.c.last_update_time_since_epoch,
#             artifact_properties_agg_cte.c.artifact_properties,
#             func.count().over().label("total_records")  # Total records for pagination
#         )
#         .select_from(artifact_metadata_cte)
#         .outerjoin(artifact_properties_agg_cte, artifact_metadata_cte.c.artifact_id == artifact_properties_agg_cte.c.artifact_id)
#         .outerjoin(artifact_execution_types_agg_cte, artifact_metadata_cte.c.artifact_id == artifact_execution_types_agg_cte.c.artifact_id)
#         .where(
#             # Apply search filter to all columns of artifact_metadata_cte
#             (artifact_metadata_cte.c.artifact_id.cast(String).ilike(f"%{filter_value}%")) |
#             (artifact_metadata_cte.c.name.ilike(f"%{filter_value}%")) |
#             (artifact_execution_types_agg_cte.c.execution.ilike(f"%{filter_value}%")) |
#             (artifact_metadata_cte.c.uri.ilike(f"%{filter_value}%")) |
#             (artifact_metadata_cte.c.create_time_since_epoch.cast(String).ilike(f"%{filter_value}%")) |
#             (artifact_metadata_cte.c.last_update_time_since_epoch.cast(String).ilike(f"%{filter_value}%")) |
#             # Apply search filter to artifact properties aggregation
#             (artifact_properties_agg_cte.c.artifact_properties.cast(String).ilike(f"%{filter_value}%"))
#         )
#         .limit(page_size)  # Limit the number of records per page
#         .offset((active_page - 1) * page_size)  # Offset for pagination
#     )

#     # Step 8: Apply sorting (order by the specified column and order)
#     if sort_order.lower() == "desc":
#         query = query.order_by(getattr(artifact_metadata_cte.c, sort_column).desc())
#     else:
#         query = query.order_by(getattr(artifact_metadata_cte.c, sort_column).asc())

#     # Step 9: Execute the query
#     result = await db.execute(query)
#     rows = result.mappings().all()

#     # Step 10: Extract total records and format results
#     total_records = rows[0]["total_records"] if rows else 0
#     return {
#         "total_items": total_records,
#         "items": [dict(row) for row in rows]
#     }    


# Deprecated legacy query (unused by current stage-based UI/API flow).
# Kept for reference to support possible rollback to /executions/{pipeline_name}.
# async def fetch_executions(
#     db: AsyncSession, 
#     pipeline_name: str, 
#     filter_value: str, 
#     active_page: int = 1, 
#     record_per_page: int = 5,
#     sort_column: str = "Context_Type", 
#     sort_order: str = "ASC"
# ):
#     # Step 1: Get relevant contexts
#     relevant_contexts = select(
#         parentcontext.c.context_id
#     ).join(
#         context, parentcontext.c.parent_context_id == context.c.id
#     ).where(
#         context.c.name == pipeline_name
#     ).subquery("relevant_contexts")

#     # Step 2: Aggregate execution properties into JSON
#     execution_properties_agg = (
#         select(
#             executionproperty.c.execution_id,
#             func.json_agg(
#                 func.json_build_object(
#                     "name", executionproperty.c.name,
#                     "value", func.coalesce(
#                         executionproperty.c.string_value,
#                         func.cast(executionproperty.c.bool_value, String), 
#                         func.cast(executionproperty.c.double_value, String),
#                         func.cast(executionproperty.c.int_value, String),
#                         func.cast(executionproperty.c.byte_value, String),
#                         func.cast(executionproperty.c.proto_value, String),
#                         text("NULL") 
#                     )
#                 )
#             ).label("execution_properties")
#         )
#         .group_by(executionproperty.c.execution_id)
#         .subquery()
#     )

#     # Step 3: Base data query (executions and associations)
#     base_data = (
#         select(
#             execution.c.id.label("execution_id")
#         )
#         .join(
#             type_table, execution.c.type_id == type_table.c.id
#         )
#         .join(
#             association, execution.c.id == association.c.execution_id
#         )
#         .join(
#             context, association.c.context_id == context.c.id
#         )
#         .where(
#             association.c.context_id.in_(select(relevant_contexts.c.context_id))
#         )
#         .subquery("base_data")
#     )

#     # Step 4: Final query with execution properties aggregation
#     query = (
#         select(
#             base_data.c.execution_id,
#             execution_properties_agg.c.execution_properties,
#             func.count().over().label("total_records")
#         )
#         .select_from(base_data)
#         .outerjoin(
#             execution_properties_agg, base_data.c.execution_id == execution_properties_agg.c.execution_id
#         )
#         .where(
#             func.lower(execution_properties_agg.c.execution_properties.cast(String)).ilike(f"%{filter_value}%")  # Filter based on execution_properties using ILIKE
#         )
#         .limit(record_per_page)
#         .offset((active_page - 1) * record_per_page)
#     )

#     # Step 5: Execute the query for paginated results
#     result = await db.execute(query)
#     rows = result.mappings().all()

#     # Step 6: Extract total records from the first row (since it's constant across all rows)
#     total_record = rows[0]["total_records"] if rows else 0

#     # Return the results in the specified format
#     return {
#         "total_items": total_record,
#         "items": [dict(row) for row in rows]
#     }


def _get_pipeline_execution_ids_subquery(pipeline_name: str):
    """
    Helper function to build the common subqueries for getting execution IDs by pipeline.
    
    Args:
        pipeline_name: Name of the pipeline
        
    Returns:
        Tuple of (relevant_contexts subquery, execution_ids subquery)
    """
    # Get relevant contexts for the pipeline
    relevant_contexts = select(
        parentcontext.c.context_id
    ).join(
        context, parentcontext.c.parent_context_id == context.c.id
    ).where(
        context.c.name == pipeline_name
    ).subquery("relevant_contexts")

    # Get execution IDs associated with the pipeline contexts
    execution_ids_query = (
        select(
            distinct(execution.c.id).label("execution_id")
        )
        .join(
            association, execution.c.id == association.c.execution_id
        )
        .where(
            association.c.context_id.in_(select(relevant_contexts.c.context_id))
        )
        .subquery("execution_ids")
    )
    
    return relevant_contexts, execution_ids_query


async def _get_stage_artifact_ids(
    db: AsyncSession,
    pipeline_name: str,
    stage_name: str,
):
    """
    Resolve artifact IDs for artifacts produced or consumed by executions in a
    given pipeline stage.

    Returns:
        List of artifact IDs associated with the pipeline and stage.
    """
    relevant_contexts, pipeline_execution_ids = _get_pipeline_execution_ids_subquery(pipeline_name)

    # Fail fast if the pipeline has no related contexts.
    result = await db.execute(select(relevant_contexts.c.context_id))
    context_ids = result.scalars().all()
    if not context_ids:
        return []

    execution_ids_with_stage = (
        select(
            distinct(executionproperty.c.execution_id).label("execution_id")
        )
        .where(
            executionproperty.c.name == "Context_Type"
        )
        .where(
            executionproperty.c.string_value == stage_name
        )
        .where(
            executionproperty.c.execution_id.in_(select(pipeline_execution_ids.c.execution_id))
        )
        .subquery("execution_ids_with_stage")
    )

    result = await db.execute(select(execution_ids_with_stage.c.execution_id))
    execution_ids = result.scalars().all()
    if not execution_ids:
        return []

    artifact_ids_cte = (
        select(distinct(event.c.artifact_id).label("artifact_id"))
        .where(event.c.execution_id.in_(execution_ids))
        .cte("artifact_ids_cte")
    )

    result = await db.execute(select(artifact_ids_cte.c.artifact_id))
    return result.scalars().all()


async def fetch_unique_execution_stages(
    db: AsyncSession,
    pipeline_name: str
):
    """
    Fetch unique execution stages (Context_Type values) for a given pipeline.
    
    Args:
        db: Database session
        pipeline_name: Name of the pipeline to filter by
        
    Returns:
        List of unique stage names
    """
    # Use helper function to get common subqueries
    relevant_contexts, execution_ids_query = _get_pipeline_execution_ids_subquery(pipeline_name)

    # Fetch unique Context_Type values from execution properties
    stages_query = (
        select(
            distinct(executionproperty.c.string_value).label("stage_name")
        )
        .where(
            executionproperty.c.execution_id.in_(select(execution_ids_query.c.execution_id))
        )
        .where(
            executionproperty.c.name == "Context_Type"
        )
        .where(
            executionproperty.c.string_value.isnot(None)
        )
        .order_by("stage_name")
    )

    # Execute the query
    result = await db.execute(stages_query)
    stages = result.scalars().all()

    # #print(stages)
    # Return the list of unique stages
    return {
        "stages": list(stages),
        "total_stages": len(stages)
    }


async def fetch_executions_by_stage(
    db: AsyncSession,
    pipeline_name: str,
    stage_name: str,
    active_page: int = 1,
    record_per_page: int = 5,
    sort_order: str = "DESC",
    filter_value: str = ""
):
    """
    Fetch executions filtered by pipeline and stage name (Context_Type).
    
    Args:
        db: Database session
        pipeline_name: Name of the pipeline
        stage_name: Stage name (Context_Type value) to filter by
        active_page: Page number for pagination
        record_per_page: Number of records per page
        
    Returns:
        Dictionary with total_items and items (list of executions with properties)
    """
    # Use helper function to get common subqueries
    _, pipeline_execution_ids = _get_pipeline_execution_ids_subquery(pipeline_name)

    # Get execution IDs for the specified stage
    execution_ids_with_stage = (
        select(
            distinct(executionproperty.c.execution_id).label("execution_id")
        )
        .where(
            executionproperty.c.name == "Context_Type"
        )
        .where(
            executionproperty.c.string_value == stage_name
        )
        .where(
            # Only get executions that belong to this pipeline
            executionproperty.c.execution_id.in_(select(pipeline_execution_ids.c.execution_id))
        )
        .subquery("execution_ids_with_stage")
    )

    # Aggregate execution properties into JSON
    execution_properties_agg = (
        select(
            executionproperty.c.execution_id,
            func.json_agg(
                func.json_build_object(
                    "name", executionproperty.c.name,
                    "value", func.coalesce(
                        executionproperty.c.string_value,
                        func.cast(executionproperty.c.bool_value, String),
                        func.cast(executionproperty.c.double_value, String),
                        func.cast(executionproperty.c.int_value, String),
                        func.cast(executionproperty.c.byte_value, String),
                        func.cast(executionproperty.c.proto_value, String),
                        text("NULL")
                    )
                )
            ).label("execution_properties")
        )
        .group_by(executionproperty.c.execution_id)
        .subquery()
    )

    # Subquery to get original_create_time_since_epoch for sorting
    # Note: The value is stored as string_value, so we need to cast it to numeric
    create_time_subquery = (
        select(
            executionproperty.c.execution_id,
            func.max(func.cast(executionproperty.c.string_value, Double)).label("create_time")
        )
        .where(executionproperty.c.name == "original_create_time_since_epoch")
        .where(
            executionproperty.c.execution_id.in_(select(execution_ids_with_stage.c.execution_id))
        )
        .group_by(executionproperty.c.execution_id)
        .subquery("create_time_subquery")
    )

    # Apply search filter across execution_id, aggregated properties, and UTC date tokens.
    search_predicate = None
    if filter_value:
        created_at_utc = func.timezone("UTC", func.to_timestamp(create_time_subquery.c.create_time / 1000.0))
        search_predicate = func.concat(
            func.cast(execution_ids_with_stage.c.execution_id, String),
            func.coalesce(
                func.cast(execution_properties_agg.c.execution_properties, String),
                ""
            ),
            # Canonical and alias formats to support inputs like 2026-09-12 8:49:11, 2026, 19, 5/19, and 5/19/2026.
            func.coalesce(func.to_char(created_at_utc, "YYYY-MM-DD HH24:MI:SS"), ""),
            func.coalesce(func.to_char(created_at_utc, "FMMM/FMDD/YYYY"), ""),
            func.coalesce(func.to_char(created_at_utc, "YYYY"), ""),
            func.coalesce(func.to_char(created_at_utc, "FMMM"), ""),
            func.coalesce(func.to_char(created_at_utc, "FMDD"), "")
        ).ilike(f"%{filter_value}%")

    # Step 3: Fetch paginated executions with properties and total count, sorted by create_time.
    final_query = (
        select(
            execution_ids_with_stage.c.execution_id,
            execution_properties_agg.c.execution_properties,
            func.count().over().label("total_records")
        )
        .select_from(execution_ids_with_stage)
        .outerjoin(
            execution_properties_agg,
            execution_ids_with_stage.c.execution_id == execution_properties_agg.c.execution_id
        )
        .outerjoin(
            create_time_subquery,
            execution_ids_with_stage.c.execution_id == create_time_subquery.c.execution_id
        )
    )

    if search_predicate is not None:
        final_query = final_query.where(search_predicate)

    # Apply sorting based on create_time from the subquery, with nulls last to handle executions that may not have the original_create_time_since_epoch property.
    final_query = (
        final_query
        .order_by(
            create_time_subquery.c.create_time.asc().nullslast()
            if sort_order.upper() == "ASC"
            else create_time_subquery.c.create_time.desc().nullslast()
        )
        .limit(record_per_page)
        .offset((active_page - 1) * record_per_page)
    )

    result = await db.execute(final_query)
    rows = result.mappings().all()
    total_records = rows[0]["total_records"] if rows else 0
    items = []
    for row in rows:
        row_dict = dict(row)
        row_dict.pop("total_records", None)
        items.append(row_dict)

    # #print(rows)

    return {
        "total_items": total_records,
        "items": items
    }


async def fetch_artifacts_by_stage(
    db: AsyncSession,
    pipeline_name: str,
    stage_name: str,
    artifact_type: str,
    filter_value: str = "",
    active_page: int = 1,
    page_size: int = 5,
    record_per_page: int | None = None,
    sort_column: str = "name",
    sort_order: str = "ASC"
):
    """
    Fetch artifacts filtered by pipeline, stage (Context_Type), and artifact type.
    
    Args:
        db: Database session
        pipeline_name: Name of the pipeline
        stage_name: Stage name (Context_Type value) to filter by
        artifact_type: Type of artifacts to fetch
        filter_value: Search filter value
        active_page: Page number for pagination
        page_size: Number of records per page (legacy name)
        record_per_page: Number of records per page (preferred name)
        sort_column: Column to sort by
        sort_order: Sort order (ASC or DESC)
        
    Returns:
        Dictionary with total_items and items list
    """
    artifact_ids = await _get_stage_artifact_ids(db, pipeline_name, stage_name)
    if not artifact_ids:
        return {"total_items": 0, "items": []}

    effective_page_size = record_per_page if record_per_page is not None else page_size

    # Step 1a: Aggregate property VALUES only into a space-separated string - used for search.
    # Searches values only (not full JSON keys) to avoid false matches on the structural
    # key "name" that appears in every property object.
    # e.g. artifact_id=5 - property_values = "https://github.com/org/repo abc123 4KB"
    artifact_property_values_subquery = (
        select(
            artifactproperty.c.artifact_id,
            func.string_agg(
                func.coalesce(
                    artifactproperty.c.string_value,
                    func.cast(artifactproperty.c.bool_value, String),
                    func.cast(artifactproperty.c.double_value, String),
                    func.cast(artifactproperty.c.int_value, String),
                    func.cast(artifactproperty.c.byte_value, String),
                    func.cast(artifactproperty.c.proto_value, String),
                    text("''")  # Fallback empty string so string_agg never receives NULL
                ),
                ' '
            ).label("property_values")
        )
        .where(artifactproperty.c.artifact_id.in_(artifact_ids))
        .group_by(artifactproperty.c.artifact_id)
        .subquery()
    )

    # Step 1b: Aggregate properties into a JSON array - used for display in the UI.
    # e.g. [{"name": "git_repo", "value": "https://..."}, {"name": "Commit", "value": "abc123"}]
    artifact_properties_agg_cte = (
        select(
            artifactproperty.c.artifact_id,
            func.json_agg(
                func.json_build_object(
                    "name", artifactproperty.c.name,
                    "value", func.coalesce(
                        artifactproperty.c.string_value,
                        func.cast(artifactproperty.c.bool_value, String),
                        func.cast(artifactproperty.c.double_value, String),
                        func.cast(artifactproperty.c.int_value, String),
                        func.cast(artifactproperty.c.byte_value, String),
                        func.cast(artifactproperty.c.proto_value, String),
                        text("NULL")
                    )
                )
            ).label("artifact_properties")
        )
        .where(artifactproperty.c.artifact_id.in_(artifact_ids))
        .group_by(artifactproperty.c.artifact_id)
        .subquery()
    )

    # Step 2: Filter by artifact type via JOIN on type_table.
    # e.g. artifact_type="Dataset" - only Dataset rows are kept.
    artifact_type_cte = (
        select(
            artifact.c.id.label("artifact_id"),
            artifact.c.name,
            artifact.c.create_time_since_epoch
        )
        .join(
            type_table, artifact.c.type_id == type_table.c.id
        )
        .where(
            artifact.c.id.in_(artifact_ids)
        )
        .where(
            type_table.c.name == artifact_type
        )
        .cte("artifact_type_cte")
    )

    # Build search predicate: concatenates artifact_id, name, date in multiple formats,
    # and property values into one string, then applies a single ILIKE check.
    # e.g. filter_value="data.xml" - matches artifacts whose name contains "data.xml"
    #      filter_value="2026"     - matches artifacts created in year 2026
    # For Label type: also searches the indexed CSV file content via an EXISTS subquery.
    # e.g. filter_value="cat", artifact_type="Label" - matches metadata OR CSV content.
    search_predicate = None
    if filter_value:
        created_at_utc = func.timezone("UTC", func.to_timestamp(artifact_type_cte.c.create_time_since_epoch / 1000.0))
        search_predicate = func.concat(
            func.cast(artifact_type_cte.c.artifact_id, String),
            func.cast(artifact_type_cte.c.name, String),
            # Canonical format: '2026-09-12 08:49:11' (matches partial or full timestamp search)
            func.coalesce(func.to_char(created_at_utc, "YYYY-MM-DD HH24:MI:SS"), ""),
            # Month/Day/Year, e.g. '5/19/2026' (matches partial or US-style date search)
            func.coalesce(func.to_char(created_at_utc, "FMMM/FMDD/YYYY"), ""),
            # Year only, e.g. '2026' (matches year search)
            func.coalesce(func.to_char(created_at_utc, "YYYY"), ""),
            # Month only, e.g. '5' (matches month search)
            func.coalesce(func.to_char(created_at_utc, "FMMM"), ""),
            # Day only, e.g. '19' (matches day search)
            func.coalesce(func.to_char(created_at_utc, "FMDD"), ""),
            # Search only property VALUES, not the full JSON (which contains the
            # structural key "name" in every entry and would cause false positives).
            func.coalesce(artifact_property_values_subquery.c.property_values, "")
        ).ilike(f"%{filter_value}%")

        # For Label artifacts with a non-empty filter, also search CSV file content
        # stored in the label_content table (ILIKE substring match on full_text_content).
        # TODO: Re-enable tsvector full-text search once tokenization is optimized
        # label_content_match_subquery = (
        #     select(label_content.c.artifact_id)
        #     .where(
        #         label_content.c.artifact_id == artifact_type_cte.c.artifact_id,
        #         label_content.c.content_tsvector.op('@@')(func.plainto_tsquery('english', filter_value))
        #     )
        #     .exists()
        # )
        if artifact_type == "Label" and filter_value.strip():
            # EXISTS subquery: checks if any label_content row for this artifact
            # contains the filter value in its CSV text.
            label_content_match_subquery = (
                select(label_content.c.artifact_id)
                .where(
                    label_content.c.artifact_id == artifact_type_cte.c.artifact_id,
                    label_content.c.full_text_content.ilike(f"%{filter_value}%")
                )
                .exists()
            )
            # Match if metadata OR CSV file content contains the filter.
            search_predicate = or_(search_predicate, label_content_match_subquery)

    # Step 3: Sort - "name" uses case-insensitive lower(); other columns sort numerically.
    # lower() cannot be applied to BIGINT (create_time_since_epoch), so it is skipped there.
    if sort_column == "name":
        sort_col = artifact_type_cte.c.name
        sort_direction = func.lower(sort_col).asc() if sort_order.upper() == "ASC" else func.lower(sort_col).desc()
    else:
        # create_time_since_epoch is a bigint - lower() cannot be applied to numeric types
        sort_col = artifact_type_cte.c.create_time_since_epoch
        sort_direction = sort_col.asc() if sort_order.upper() == "ASC" else sort_col.desc()

    # Final query: LEFT JOINs keep artifacts even when they have no properties.
    # count().over() is a window function - returns total matching rows without a
    # separate COUNT query. e.g. 42 total matches - every row carries total_records=42.
    final_query = (
        select(
            artifact_type_cte.c.artifact_id,
            artifact_type_cte.c.name,
            artifact_type_cte.c.create_time_since_epoch,
            artifact_properties_agg_cte.c.artifact_properties,
            func.count().over().label("total_records")
        )
        .select_from(artifact_type_cte)
        .outerjoin(
            artifact_properties_agg_cte,
            artifact_type_cte.c.artifact_id == artifact_properties_agg_cte.c.artifact_id
        )
        .outerjoin(
            artifact_property_values_subquery,
            artifact_type_cte.c.artifact_id == artifact_property_values_subquery.c.artifact_id
        )
    )

    # Apply search filter if provided
    if search_predicate is not None:
        final_query = final_query.where(search_predicate)

    # Apply sorting and pagination. e.g. active_page=3, page_size=5 - OFFSET 10
    final_query = (
        final_query
        .order_by(sort_direction)
        .limit(effective_page_size)
        .offset((active_page - 1) * effective_page_size)
    )

    result = await db.execute(final_query)
    rows = result.mappings().all()
    total_records = rows[0]["total_records"] if rows else 0
    items = []
    # Strip total_records from each row - it's already returned at the top level.
    for row in rows:
        row_dict = dict(row)
        row_dict.pop("total_records", None)
        items.append(row_dict)

    #print(f"Artifacts by stage - Pipeline: {pipeline_name}, Stage: {stage_name}, Count: {total_records}")

    return {
        "total_items": total_records,
        "items": items
    }


async def fetch_artifact_types_by_stage(
    db: AsyncSession,
    pipeline_name: str,
    stage_name: str
):
    """
    Fetch unique artifact types available in a specific stage of a pipeline.
    
    Args:
        db: Database session
        pipeline_name: Name of the pipeline
        stage_name: Stage name (Context_Type value) to filter by
        
    Returns:
        List of unique artifact type names
    """
    artifact_ids = await _get_stage_artifact_ids(db, pipeline_name, stage_name)
    if not artifact_ids:
        return []

    # Step 1: Get unique artifact types.
    artifact_types_query = (
        select(distinct(type_table.c.name).label("artifact_type"))
        .join(
            artifact, type_table.c.id == artifact.c.type_id
        )
        .where(
            artifact.c.id.in_(artifact_ids)
        )
        .where(
            type_table.c.name != "Environment"  # Exclude Environment type
        )
        .order_by("artifact_type")
    )

    result = await db.execute(artifact_types_query)
    artifact_types = result.scalars().all()

    #print(f"Artifact types for stage - Pipeline: {pipeline_name}, Stage: {stage_name}, Types: {artifact_types}")
    
    return list(artifact_types)


async def insert_label_content(
    db: AsyncSession, 
    artifact_id: int, 
    file_name: str, 
    full_text_content: str
):
    """
    Insert label content into the label_content table with full-text search support.
    
    Args:
        db (AsyncSession): Database session
        artifact_id (int): The artifact ID from the artifact table
        file_name (str): The CSV filename
        full_text_content (str): The extracted text content from CSV
    
    Returns:
        dict: Success message or error details
    
    Note:
        - Uses ON CONFLICT DO NOTHING for idempotent inserts
        - Automatically generates tsvector using PostgreSQL's to_tsvector()
        - Stores current timestamp in milliseconds since epoch
        - Supports multiple labels per artifact (composite unique key on artifact_id + file_name)
    """
    try:
        # Get current timestamp in milliseconds since epoch
        current_time_ms = int(time.time() * 1000)
        
        # Create insert query with PostgreSQL's to_tsvector for full-text search
        # Using pg_insert for PostgreSQL-specific on_conflict_do_nothing
        query = pg_insert(label_content).values(
            artifact_id=artifact_id,
            file_name=file_name,
            full_text_content=full_text_content,
            content_tsvector=func.to_tsvector('english', full_text_content),
            created_at=current_time_ms
        ).on_conflict_do_nothing(
            index_elements=['artifact_id', 'file_name']  # Composite unique key
        )
        
        # Execute the insert
        await db.execute(query)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Label content inserted for artifact_id: {artifact_id}, file: {file_name}"
        }
    
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "message": f"Failed to insert label content: {str(e)}"
        }


async def get_artifact_id_by_filename(db: AsyncSession, file_name: str):
    """
    Get artifact_id for a Label artifact by matching the filename in the URI.
    
    Args:
        db (AsyncSession): Database session
        file_name (str): The CSV filename to search for
    
    Returns:
        int or None: The artifact_id if found, None otherwise
    
    Note:
        Searches for Label artifacts where URI contains the filename
    """
    try:
        # Query to find Label artifact with matching filename in URI
        query = (
            select(artifact.c.id)
            .join(type_table, artifact.c.type_id == type_table.c.id)
            .where(
                type_table.c.name == "Label",
                artifact.c.uri.ilike(f"%{file_name}%")
            )
        )
        
        result = await db.execute(query)
        artifact_id = result.scalar()
        
        return artifact_id
    
    except Exception as e:
        print(f"Error finding artifact_id for file {file_name}: {str(e)}")
        return None


# -------- Periodic Sync Scheduling Queries --------
async def create_schedule(
    db: AsyncSession, 
    server_id: int, 
    timezone: str, 
    start_time_utc: int, 
    next_run_time_utc: int, 
    created_at: int, 
    one_time: bool = False,
    recurrence_mode: str = None,
    interval_unit: str = None,
    interval_value: int = None,
    daily_time: str = None,
    weekly_day: str = None,
    weekly_time: str = None
):
    """Insert a schedule row and return the created schedule id."""
    query = insert(scheduled_syncs).values(
        server_id=server_id,
        timezone=timezone,
        start_time_utc=start_time_utc,
        next_run_time_utc=next_run_time_utc,
        active=True,
        status='new',
        one_time=one_time,
        created_at=created_at,
        recurrence_mode=recurrence_mode,
        interval_unit=interval_unit,
        interval_value=interval_value,
        daily_time=daily_time,
        weekly_day=weekly_day,
        weekly_time=weekly_time,
    ).returning(scheduled_syncs.c.id)
    result = await db.execute(query)
    await db.commit()
    return {"id": result.scalar()}


async def list_schedules(db: AsyncSession, server_id: int | None = None):
    """Return active schedules, optionally filtered by server id."""
    query = select(scheduled_syncs).where(scheduled_syncs.c.active == True)
    if server_id is not None:
        query = query.where(scheduled_syncs.c.server_id == server_id)
    result = await db.execute(query)
    return result.mappings().all()


async def due_schedules(db: AsyncSession, now_utc_ms: int):
    """Return active schedules whose next run time is at or before now."""
    query = select(scheduled_syncs).where(
        (scheduled_syncs.c.active == True) & (scheduled_syncs.c.next_run_time_utc <= now_utc_ms)
    )
    result = await db.execute(query)
    return result.mappings().all()


async def update_next_run(db: AsyncSession, schedule_id: int, next_run_time_utc: int):
    """Update the next run timestamp for a schedule."""
    query = update(scheduled_syncs).where(scheduled_syncs.c.id == schedule_id).values(next_run_time_utc=next_run_time_utc)
    await db.execute(query)
    await db.commit()


async def log_sync_run(db: AsyncSession, schedule_id: int, run_time_utc: int, status: str, message: str | None, sync_type: str = "periodic"):
    """Insert one sync execution log row."""
    query = insert(sync_logs).values(
        schedule_id=schedule_id,
        run_time_utc=run_time_utc,
        status=status,
        message=message,
        sync_type=sync_type,
    )
    await db.execute(query)
    await db.commit()


async def list_sync_logs(db: AsyncSession, schedule_id: int, limit: int = 50):
    """Return recent sync logs for a schedule, newest first."""
    query = select(sync_logs).where(sync_logs.c.schedule_id == schedule_id).order_by(sync_logs.c.run_time_utc.desc()).limit(limit)
    result = await db.execute(query)
    return result.mappings().all()


async def get_completed_logs_by_server(db: AsyncSession, server_id: int, limit: int = 100):
    """Return joined sync log history for a specific server."""
    query = (
        select(
            sync_logs.c.id,
            sync_logs.c.run_time_utc,
            sync_logs.c.status,
            sync_logs.c.message,
            sync_logs.c.sync_type,
            scheduled_syncs.c.server_id
        )
        .select_from(sync_logs.join(scheduled_syncs, sync_logs.c.schedule_id == scheduled_syncs.c.id))
        .where(scheduled_syncs.c.server_id == server_id)
        .order_by(sync_logs.c.run_time_utc.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.mappings().all()


async def update_schedule_fields(
    db: AsyncSession,
    schedule_id: int,
    timezone: str | None = None,
    start_time_utc: int | None = None,
    next_run_time_utc: int | None = None,
    active: bool | None = None,
    one_time: bool | None = None,
    status: str | None = None,
):
    """Partially update mutable schedule fields and return status message."""
    values = {}
    if timezone is not None:
        values[scheduled_syncs.c.timezone] = timezone
    if start_time_utc is not None:
        values[scheduled_syncs.c.start_time_utc] = start_time_utc
    if next_run_time_utc is not None:
        values[scheduled_syncs.c.next_run_time_utc] = next_run_time_utc
    if active is not None:
        values[scheduled_syncs.c.active] = active
    if one_time is not None:
        values[scheduled_syncs.c.one_time] = one_time
    if status is not None:
        values[scheduled_syncs.c.status] = status

    if not values:
        return {"message": "No fields to update"}

    query = update(scheduled_syncs).where(scheduled_syncs.c.id == schedule_id).values(values)
    await db.execute(query)
    await db.commit()
    return {"message": "Schedule updated"}


async def delete_schedule(db: AsyncSession, schedule_id: int):
    """Soft-cancel a schedule by deactivating it and setting cancelled status."""
    query = (
        update(scheduled_syncs)
        .where(scheduled_syncs.c.id == schedule_id)
        .values(active=False, status="cancelled")
    )
    await db.execute(query)
    await db.commit()
    return {"message": "Schedule deactivated"}


async def get_sync_status(db: AsyncSession, server_name: str, server_url: str):
    """Return last sync timestamp checkpoint for a server."""
    query = select(registered_servers.c.last_sync_time).where(
        (registered_servers.c.server_name == server_name) & 
        (registered_servers.c.host_info == server_url)
    )
    result = await db.execute(query)
    return result.mappings().all()

