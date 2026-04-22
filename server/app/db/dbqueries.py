from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from server.app.db.dbconfig import get_db
from sqlalchemy import select, func, text, String, Double, bindparam, case, distinct, insert, update
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
    registered_servers
)


async def register_server_details(db: AsyncSession, server_name: str, server_url: str):
    """
    Register server details in the database.
    """
    # Step 1: Check if the server is already registered
    query_check = select(registered_servers.c.id).where(
        registered_servers.c.host_info == server_url
    )
    result = await db.execute(query_check)
    exists = result.scalar()

    if exists:
        return {"message": "Server is already registered"}

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
    """
    Update the sync status in the database.
    """
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

    # Apply search filter across execution_id and aggregated properties if filter_value is provided
    search_predicate = None
    if filter_value:
        search_predicate = func.concat(
            func.cast(execution_ids_with_stage.c.execution_id, String),
            func.coalesce(
                func.cast(execution_properties_agg.c.execution_properties, String),
                ""
            )
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

    # Step 1: Aggregate artifact properties into JSON based on artifact id.
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

    # Step 2: Filter by artifact type and prepare the base artifact set.
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

    # Apply search filter across all relevant columns (artifact_id, name, and aggregated properties).
    search_predicate = None
    if filter_value:
        search_predicate = func.concat(
            func.cast(artifact_type_cte.c.artifact_id, String),
            func.cast(artifact_type_cte.c.name, String),
            func.coalesce(
                func.cast(artifact_properties_agg_cte.c.artifact_properties, String),
                ""
            )
        ).ilike(f"%{filter_value}%")

    # Step 3: Build final query with pagination, sorting, and total count.
    if sort_column == "name":
        sort_col = artifact_type_cte.c.name
        sort_direction = func.lower(sort_col).asc() if sort_order.upper() == "ASC" else func.lower(sort_col).desc()
    else:
        # create_time_since_epoch is a bigint — lower() cannot be applied to numeric types
        sort_col = artifact_type_cte.c.create_time_since_epoch
        sort_direction = sort_col.asc() if sort_order.upper() == "ASC" else sort_col.desc()

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
    )

    # Apply search filter if provided
    if search_predicate is not None:
        final_query = final_query.where(search_predicate)

    # Apply sorting, pagination, and execute the query
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
    # Remove total_records from each row before returning results, as it's redundant to include it in every item.
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
