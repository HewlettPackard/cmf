from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, String, bindparam, case
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
    event
)

async def fetch_artifacts(
    db: AsyncSession,   # Used to interact with the database
    pipeline_name: str, 
    artifact_type: str, 
    search_query: str, 
    page_number: int = 1, 
    page_size: int = 5,  # Number of records per page
    sort_column: str = "name", 
    sort_order: str = "ASC"
):
    # Step 1: Get relevant contexts
    relevant_contexts = select(
        parentcontext.c.context_id
    ).join(
        context, parentcontext.c.parent_context_id == context.c.id
    ).where(
        context.c.name == bindparam("pipeline_name")
    ).subquery("relevant_contexts")

    # Step 2: Aggregate artifact properties into JSON
    artifact_properties_agg = (
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
        .group_by(artifactproperty.c.artifact_id)
        .subquery()
    )

    # Step 3: Base data query
    base_data = (
        select(
            artifact.c.id.label('artifact_id'),
            artifact.c.name,
            context.c.name.label('execution'),
            artifact.c.uri,
            artifact.c.create_time_since_epoch,
            artifact.c.last_update_time_since_epoch
        )
        .join(
            type_table, artifact.c.type_id == type_table.c.id
        )
        .join(
            attribution, artifact.c.id == attribution.c.artifact_id
        )
        .join(
            context, attribution.c.context_id == context.c.id
        )
        .where(
            type_table.c.name == artifact_type,
            attribution.c.context_id.in_(select(relevant_contexts.c.context_id))  # Using subquery
        )
        .subquery("base_data")
    )

    # Step 4: Initial query setup for fetching paginated data with search filter
    # Inside your SQLAlchemy query
    query = (
        select(
            base_data.c.artifact_id,
            base_data.c.name,
            base_data.c.execution,
            base_data.c.uri,
            base_data.c.create_time_since_epoch,
            base_data.c.last_update_time_since_epoch,
            artifact_properties_agg.c.artifact_properties,
            func.count().over().label("total_records")
        )
        .select_from(base_data)
        .outerjoin(artifact_properties_agg, base_data.c.artifact_id == artifact_properties_agg.c.artifact_id)
        .where(
            # Apply search filter to all columns of base_data
            (base_data.c.artifact_id.cast(String).ilike(f"%{search_query}%")) |
            (base_data.c.name.ilike(f"%{search_query}%")) |
            (base_data.c.execution.ilike(f"%{search_query}%")) |
            (base_data.c.uri.ilike(f"%{search_query}%")) |
            (base_data.c.create_time_since_epoch.cast(String).ilike(f"%{search_query}%")) |
            (base_data.c.last_update_time_since_epoch.cast(String).ilike(f"%{search_query}%")) |
            
            # Apply search filter to artifact properties aggregation
            (artifact_properties_agg.c.artifact_properties.cast(String).ilike(f"%{search_query}%"))
        )
        .limit(page_size)
        .offset((page_number - 1) * page_size)
    )

    # Step 5: Apply sorting (order by the specified column and order)
    if sort_order.lower() == "desc":
        query = query.order_by(getattr(base_data.c, sort_column).desc())
    else:
        query = query.order_by(getattr(base_data.c, sort_column).asc())

    # Step 6: Execute the query
    result = await db.execute(query, {"pipeline_name": pipeline_name})
    rows = result.mappings().all()

    # Extract the total count from the window function (available in all rows)
    total_record = rows[0]['total_records'] if rows else 0  # Get total count from the first row
    
    # Step 7: Return paginated data with total count
    return {
        "total_items": total_record,
        "items": [dict(row) for row in rows]
    }

# acutal code
async def fetch_executions(
    db: AsyncSession, 
    pipeline_name: str, 
    filter_value: str, 
    active_page: int = 1, 
    record_per_page: int = 5,
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


async def fetch_artifact_execution_lineage(
    db: AsyncSession,
    pipeline_name: str,
    page_number: int = 1,
    page_size: int = 5,
    sort_column: str = "id",
    sort_order: str = "ASC"
):
    print("i am inside psql query")
    # Step 1: Get relevant contexts
    relevant_contexts = select(
        parentcontext.c.context_id
    ).join(
        context, parentcontext.c.parent_context_id == context.c.id
    ).where(
        context.c.name == bindparam("pipeline_name")
    ).subquery("relevant_contexts")

    # Step 2: Join event with artifact and execution_property tables
    query = (
        select(
            event.c.id,
            artifact.c.name.label("artifact_name"),
            case(
                (executionproperty.c.name == "Context_Type", func.coalesce(
                    executionproperty.c.string_value,
                    func.cast(executionproperty.c.bool_value, String),
                    func.cast(executionproperty.c.double_value, String),
                    func.cast(executionproperty.c.int_value, String),
                    func.cast(executionproperty.c.byte_value, String),
                    func.cast(executionproperty.c.proto_value, String),
                    text("NULL")
                )),
                else_=text("NULL")
            ).label("execution_context_type"),
            event.c.type
        )
        .join(
            artifact, event.c.artifact_id == artifact.c.id
        )
        .join(
            execution, event.c.execution_id == execution.c.id
        )
        .join(
            executionproperty, execution.c.id == executionproperty.c.execution_id
        )
        .where(
            executionproperty.c.name == "Context_Type",
            association.c.context_id.in_(select(relevant_contexts.c.context_id))
        )
        .order_by(event.c.id.asc())
    )

    # Step 4: Execute the query
    result = await db.execute(query, {"pipeline_name": pipeline_name})
    rows = result.mappings().all()

    # Step 6: Create dictionary of pairs based on type of event
    combined_dict = []
    for row in rows:
        if row['type'] == 4:
            combined_dict.append({'id': row['artifact_name'], 'parents': [row['execution_context_type']]})
        elif row['type'] == 3:
            # Check whether artifact name exists as an id inside combined_dict
            # If not exists then create id as artifact name and parents as empty
            if not any(d['id'] == row['artifact_name'] for d in combined_dict):
                combined_dict.append({'id': row['artifact_name'], 'parents': []})
            combined_dict.append({'id': row['execution_context_type'], 'parents': [row['artifact_name']]})


    # Remove duplicates from combined_dict
    combined_dict = [i for n, i in enumerate(combined_dict) if i not in combined_dict[n + 1:]]
    # print(combined_dict)

    from collections import defaultdict

    # Step 1: Create a mapping of parents to their children
    parent_map = defaultdict(list)
    independent_nodes = []

    for item in combined_dict:
        if not item['parents']:  # If the node has no parents, treat it as an independent group
            independent_nodes.append([item])
        else:
            for parent in item['parents']:
                parent_map[parent].append(item)

    # Step 2: Collect all grouped lists
    grouped_data = independent_nodes + list(parent_map.values())

    # Step 6: Return paginated data
    return grouped_data

