from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, case, String, and_
from server.app.db.dbmodels import artifact, artifactproperty, context, parentcontext, attribution, type_table

async def fetch_artifacts(
    db: AsyncSession,
    pipeline_name: str, 
    artifact_type: str, 
    search_query: str, 
    page: int = 1, 
    page_size: int = 10, 
    sort_column: str = "name", 
    sort_order: str = "ASC"
):
    # fetch_artifacts(db, pipeline_name, artifact_type, filter_value, page, 5, sort_column, sort_order)
    """Fetch artifacts with refined subqueries, pagination, and full-text search."""

    offset = (page - 1) * page_size

    
    # Step 1: Get relevant contexts

    #relevant_contexts = select(parentcontext.c.context_id).join(context).where(context.c.name == pipeline_name)
    from sqlalchemy import bindparam, String, text

    offset = (page - 1) * page_size

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

-

    # Step 4: Full-text search
    search_condition = text(
        "to_tsvector('simple', bd.name || ' ' || bd.uri || ' ' || COALESCE(ap_agg.artifact_properties::TEXT, '')) @@ to_tsquery('simple', :search_query)"
    ).bindparams(search_query=search_query)  

    # Step 5: Sorting & Pagination
    order_by_clause = getattr(base_data.c, sort_column)
    if sort_order.lower() == "desc":
        order_by_clause = order_by_clause.desc()

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
        .join(artifact_properties_agg, base_data.c.artifact_id == artifact_properties_agg.c.artifact_id, isouter=True)
        .where(search_condition)
        .order_by(order_by_clause)  # ✅ Fixed ordering
        .limit(page_size)
        .offset(offset)
    )

    # Execute query
    result = await db.execute(query, {"pipeline_name": pipeline_name, "search_query": search_query})
    return result.mappings().all()


    '''
    relevant_contexts = select(
        parentcontext.c.context_id
    ).join(
        context, parentcontext.c.parent_context_id == context.c.id
    ).where(
        context.c.name == text(':pipeline_name')  # Bind parameter for parent context name
    ).subquery('relevant_contexts')


    # Step 2: Aggregate artifact properties into JSON
    artifact_properties_agg = (
        select(
            artifactproperty.c.artifact_id,
            func.json_agg(
                func.json_build_object(
                    "name", artifactproperty.c.name,
                    "value", func.coalesce(
                        artifactproperty.c.string_value,
                        func.cast(artifactproperty.c.bool_value, text),
                        func.cast(artifactproperty.c.double_value, text),
                        func.cast(artifactproperty.c.int_value, text),
                        func.cast(artifactproperty.c.byte_value, text),
                        func.cast(artifactproperty.c.proto_value, text),
                        text("NULL")
                    )
                )
            ).label("artifact_properties")
        )
        .group_by(artifactproperty.c.artifact_id)
        .subquery()
    )

    # Step 3: Fetch base data
    base_data = (
        select(
            artifact.c.id.label("artifact_id"),
            artifact.c.name,
            context.c.name.label("execution"),
            artifact.c.uri,
            func.to_timestamp(artifact.c.create_time_since_epoch / 1000).label("create_time_since_epoch"),
            artifact.c.last_update_time_since_epoch
        )
        .join(type_table, artifact.c.type_id == type_table.c.id)
        .join(attribution, artifact.c.id == attribution.c.artifact_id)
        .join(context, attribution.c.context_id == context.c.id)
        .where(type_table.c.name == artifact_type)
        .where(attribution.c.context_id.in_(relevant_contexts))
        .subquery()
    )

    # Step 4: Full-text search
    search_condition = text(
        f"to_tsvector('simple', bd.name || ' ' || bd.uri || ' ' || COALESCE(ap_agg.artifact_properties::TEXT, '')) @@ to_tsquery('simple', :search_query)"
    )

    # Step 5: Final Query with Pagination, Sorting, and Filtering
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
        .join(artifact_properties_agg, base_data.c.artifact_id == artifact_properties_agg.c.artifact_id, isouter=True)
        .where(search_condition)
        .order_by(text(f"bd.{sort_column} {sort_order}"))
        .limit(page_size)
        .offset(offset)
    )

    # Execute query
    result = await db.execute(query, {"search_query": search_query})
    return result.mappings().all()
    '''