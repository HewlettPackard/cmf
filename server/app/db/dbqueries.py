from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from server.app.db.dbconfig import get_db
from sqlalchemy import select, func, text, String, bindparam, case, distinct
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
)

async def register_server_details(db: AsyncSession, server_name: str, host_info: str):
    """
    Register server details in the database.
    """
    # Step 1: Check if the server is already registered
    query_check = text("""
        SELECT 1 FROM registered_servers WHERE host_info = :host_info
    """)
    result = await db.execute(query_check, {"host_info": host_info})
    # If a matching row exists, scalar() returns 1 (from SELECT 1). If not, it returns None
    exists = result.scalar()

    if exists:
        return {"message": "Server is already registered"}

    # Step 2: Insert new server
    query_insert = text("""
        INSERT INTO registered_servers (server_name, host_info)
        VALUES (:server_name, :host_info)
    """)
    await db.execute(query_insert, {"server_name": server_name, "host_info": host_info})
    await db.commit()

    return {"message": "Server registered successfully"}


async def get_registered_server_details(db: AsyncSession = Depends(get_db())):
    """
    Get all registered server details from the database.
    """
    query = text("""SELECT * FROM registered_servers""")
    result = await db.execute(query)
    return result.mappings().all()


async def get_sync_status(db: AsyncSession, server_name: str, host_info: str):
    """
    Get the sync status from the database.
    """
    query = text("""SELECT last_sync_time FROM registered_servers WHERE server_name = :server_name AND host_info = :host_info""")
    result = await db.execute(query, {"server_name": server_name, "host_info": host_info})
    return result.mappings().all()


async def update_sync_status(db: AsyncSession, current_utc_time: int, server_name: str, host_info: str):
    """
    Update the sync status in the database.
    """
    query = text("""
        UPDATE registered_servers
        SET last_sync_time = :current_utc_time
        WHERE server_name = :server_name AND host_info = :host_info
    """)
    await db.execute(query, {"current_utc_time": current_utc_time, "server_name": server_name, "host_info": host_info})
    await db.commit()  # Commit the transaction


async def fetch_artifacts(
    db: AsyncSession,   # Used to interact with the database
    pipeline_name: str, 
    artifact_type: str, 
    filter_value: str, 
    active_page: int = 1, 
    page_size: int = 5,  # Number of records per page
    sort_column: str = "name", 
    sort_order: str = "ASC"
):
    # Step 1: Get relevant contexts
    relevant_contexts_cte = select(
        parentcontext.c.context_id
    ).join(
        context, parentcontext.c.parent_context_id == context.c.id
    ).where(
        context.c.name == pipeline_name
    ).cte("relevant_contexts_cte")

    # Step 2: Fetch execution IDs based on pipeline name
    execution_ids_cte = (
        select(
            execution.c.id.label("execution_id")
        )
        .join(
            association, execution.c.id == association.c.execution_id
        )
        .where(
            association.c.context_id.in_(select(relevant_contexts_cte.c.context_id))
        )
        .cte("execution_ids_cte")
    )

    # Step 3: Based on execution ids list fetching equvalent artifact lists from event_path table
    artifact_ids_cte = (
        select(distinct(event.c.artifact_id).label("artifact_id"))
        .where(event.c.execution_id.in_(select(execution_ids_cte.c.execution_id)))
        .cte("artifact_ids_cte")
    )

    # Step 4: Aggregate artifact properties into JSON
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
        .where(artifactproperty.c.artifact_id.in_(select(artifact_ids_cte.c.artifact_id)))  # Filter by artifact IDs
        .group_by(artifactproperty.c.artifact_id)
        .cte("artifact_properties_agg_cte")
    )

    # Step 5: Aggregate execution type names per artifact
    artifact_execution_types_agg_cte = (
        select(
            event.c.artifact_id,
            func.string_agg(func.distinct(context.c.name), ', ').label("execution")
        )
        .join(execution, event.c.execution_id == execution.c.id)
        .join(association, execution.c.id == association.c.execution_id)
        .join(context, association.c.context_id == context.c.id)
        .where(event.c.artifact_id.in_(select(artifact_ids_cte.c.artifact_id)))
        .group_by(event.c.artifact_id)
        .cte("artifact_execution_types_agg_cte")
    )

    # Step 6: Base artifact metadata
    artifact_metadata_cte = (
        select(
            artifact.c.id.label('artifact_id'),
            artifact.c.name,
            artifact.c.uri,
            func.to_char(
                func.timezone('GMT', func.to_timestamp(artifact.c.create_time_since_epoch / 1000)),
                'Dy, DD Mon YYYY HH24:MI:SS GMT'
            ).label('create_time_since_epoch'),
            artifact.c.last_update_time_since_epoch
        )
        .join(type_table, artifact.c.type_id == type_table.c.id)
        .join(attribution, artifact.c.id == attribution.c.artifact_id)
        .join(context, attribution.c.context_id == context.c.id)
        .where(
            artifact.c.id.in_(select(artifact_ids_cte.c.artifact_id)),
            type_table.c.name == artifact_type
        )
        .cte("artifact_metadata_cte")
    )

    # Step 7: Query for fetching paginated data
    query = (
        select(
            artifact_metadata_cte.c.artifact_id,
            artifact_metadata_cte.c.name,
            artifact_execution_types_agg_cte.c.execution,
            artifact_metadata_cte.c.uri,
            artifact_metadata_cte.c.create_time_since_epoch,
            artifact_metadata_cte.c.last_update_time_since_epoch,
            artifact_properties_agg_cte.c.artifact_properties,
            func.count().over().label("total_records")  # Total records for pagination
        )
        .select_from(artifact_metadata_cte)
        .outerjoin(artifact_properties_agg_cte, artifact_metadata_cte.c.artifact_id == artifact_properties_agg_cte.c.artifact_id)
        .outerjoin(artifact_execution_types_agg_cte, artifact_metadata_cte.c.artifact_id == artifact_execution_types_agg_cte.c.artifact_id)
        .where(
            # Apply search filter to all columns of artifact_metadata_cte
            (artifact_metadata_cte.c.artifact_id.cast(String).ilike(f"%{filter_value}%")) |
            (artifact_metadata_cte.c.name.ilike(f"%{filter_value}%")) |
            (artifact_execution_types_agg_cte.c.execution.ilike(f"%{filter_value}%")) |
            (artifact_metadata_cte.c.uri.ilike(f"%{filter_value}%")) |
            (artifact_metadata_cte.c.create_time_since_epoch.cast(String).ilike(f"%{filter_value}%")) |
            (artifact_metadata_cte.c.last_update_time_since_epoch.cast(String).ilike(f"%{filter_value}%")) |
            # Apply search filter to artifact properties aggregation
            (artifact_properties_agg_cte.c.artifact_properties.cast(String).ilike(f"%{filter_value}%"))
        )
        .limit(page_size)  # Limit the number of records per page
        .offset((active_page - 1) * page_size)  # Offset for pagination
    )

    # Step 8: Apply sorting (order by the specified column and order)
    if sort_order.lower() == "desc":
        query = query.order_by(getattr(artifact_metadata_cte.c, sort_column).desc())
    else:
        query = query.order_by(getattr(artifact_metadata_cte.c, sort_column).asc())

    # Step 9: Execute the query
    result = await db.execute(query)
    rows = result.mappings().all()

    # Step 10: Extract total records and format results
    total_records = rows[0]["total_records"] if rows else 0
    return {
        "total_items": total_records,
        "items": [dict(row) for row in rows]
    }    


# acutal code
async def fetch_executions(
    db: AsyncSession, 
    pipeline_name: str, 
    filter_value: str, 
    active_page: int = 1, 
    record_per_page: int = 5,
    sort_column: str = "Context_Type", 
    sort_order: str = "ASC"
):
    # Step 1: Get relevant contexts
    relevant_contexts = select(
        parentcontext.c.context_id
    ).join(
        context, parentcontext.c.parent_context_id == context.c.id
    ).where(
        context.c.name == pipeline_name
    ).subquery("relevant_contexts")

    # Step 2: Aggregate execution properties into JSON
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

    # Step 3: Base data query (executions and associations)
    base_data = (
        select(
            execution.c.id.label("execution_id")
        )
        .join(
            type_table, execution.c.type_id == type_table.c.id
        )
        .join(
            association, execution.c.id == association.c.execution_id
        )
        .join(
            context, association.c.context_id == context.c.id
        )
        .where(
            association.c.context_id.in_(select(relevant_contexts.c.context_id))
        )
        .subquery("base_data")
    )

    # Step 4: Final query with execution properties aggregation
    query = (
        select(
            base_data.c.execution_id,
            execution_properties_agg.c.execution_properties,
            func.count().over().label("total_records")
        )
        .select_from(base_data)
        .outerjoin(
            execution_properties_agg, base_data.c.execution_id == execution_properties_agg.c.execution_id
        )
        .where(
            func.lower(execution_properties_agg.c.execution_properties.cast(String)).ilike(f"%{filter_value}%")  # Filter based on execution_properties using ILIKE
        )
        .limit(record_per_page)
        .offset((active_page - 1) * record_per_page)
    )

    # Step 5: Execute the query for paginated results
    result = await db.execute(query)
    rows = result.mappings().all()

    # Step 6: Extract total records from the first row (since it's constant across all rows)
    total_record = rows[0]["total_records"] if rows else 0

    # Return the results in the specified format
    return {
        "total_items": total_record,
        "items": [dict(row) for row in rows]
    }
