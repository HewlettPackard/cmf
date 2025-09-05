from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from server.app.db.dbconfig import get_db
from sqlalchemy import select, func, text, String, bindparam, case, distinct, insert, update
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
    label_index,
    registered_servers
)

async def register_server_details(db: AsyncSession, server_name: str, host_info: str):
    """
    Register server details in the database.
    """
    # Step 1: Check if the server is already registered
    query_check = select(registered_servers.c.id).where(
        registered_servers.c.host_info == host_info
    )
    result = await db.execute(query_check)
    # If a matching row exists, scalar() returns 1 (from SELECT 1). If not, it returns None
    exists = result.scalar()

    if exists:
        return {"message": "Server is already registered"}

    # Step 2: Insert new server
    query_insert = insert(registered_servers).values(
        server_name=server_name, 
        host_info=host_info
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


async def get_sync_status(db: AsyncSession, server_name: str, host_info: str):
    """
    Get the sync status from the database.
    """
    query = select(registered_servers.c.last_sync_time).where(
        (registered_servers.c.server_name == server_name) & 
        (registered_servers.c.host_info == host_info)
    )
    result = await db.execute(query)
    return result.mappings().all()


async def update_sync_status(db: AsyncSession, current_utc_time: int, server_name: str, host_info: str):
    """
    Update the sync status in the database.
    """
    query = update(registered_servers).where(
        (registered_servers.c.server_name == server_name) & 
        (registered_servers.c.host_info == host_info)
    ).values(last_sync_time=current_utc_time)
    await db.execute(query)
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

    # Early check: are there any relevant contexts for the given pipeline?
    res = await db.execute(select(relevant_contexts_cte.c.context_id))
    context_ids = res.scalars().all()
    if not context_ids:
        # No relevant contexts found, return empty result
        return {"total_items": 0, "items": []}

    # Step 2: Fetch execution IDs based on pipeline name
    execution_ids_cte = (
        select(
            execution.c.id.label("execution_id")
        )
        .join(
            association, execution.c.id == association.c.execution_id
        )
        .where(
            association.c.context_id.in_(context_ids)
        )
        .cte("execution_ids_cte")
    )

    # Fetch all execution IDs for the relevant pipeline contexts
    res = await db.execute(select(execution_ids_cte.c.execution_id))
    execution_ids = res.scalars().all()
    if not execution_ids:
        # No executions found for the pipeline, return empty result
        return {"total_items": 0, "items": []}

    # Step 3: Based on execution ids list fetching equvalent artifact lists from event_path table
    artifact_ids_cte = (
        select(distinct(event.c.artifact_id).label("artifact_id"))
        .where(event.c.execution_id.in_(execution_ids))
        .cte("artifact_ids_cte")
    )

    # Fetch all artifact IDs for the relevant executions
    res = await db.execute(select(artifact_ids_cte.c.artifact_id))
    artifact_ids = res.scalars().all()
    if not artifact_ids:
        # No artifacts found for the executions, return empty result
        return {"total_items": 0, "items": []}

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
        .where(artifactproperty.c.artifact_id.in_(artifact_ids)) # Filter by artifact IDs
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
        .where(event.c.artifact_id.in_(artifact_ids))
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
            artifact.c.id.in_(artifact_ids),
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


async def search_labels_in_artifacts(db: AsyncSession, filter_value: str, pipeline_name: str = None, limit: int = 50):
    """
    Search for artifacts that have labels matching the filter value using PostgreSQL full-text search.

    This function provides high-performance full-text search across CSV label content stored
    in the label_index table. It uses PostgreSQL's built-in text search capabilities with
    ts_rank scoring for relevance-based result ordering.

    Key Features:
    - Full-text search with relevance scoring
    - Works independently of artifact metadata
    - Optimized for large datasets (1 lakh+ rows)
    - Returns structured results compatible with artifact API

    Performance Characteristics:
    - Uses PostgreSQL's GIN indexes on search_vector for fast text search
    - LIMIT parameter prevents memory exhaustion on large result sets
    - ts_rank scoring provides meaningful result ordering

    Args:
        db: Database session for executing queries
        filter_value: Text to search for within label content
        pipeline_name: Optional pipeline name filter (reserved for future use)
        limit: Maximum number of results to return (default: 50)

    Returns:
        List of dictionaries containing:
        - artifact_id: None (label search doesn't map to specific artifacts)
        - name: Descriptive name indicating label match
        - uri: Label URI in format "label://filename#row_index"
        - label_file: Source CSV filename
        - matching_content: The actual content that matched
        - label_metadata: Raw metadata from the CSV row
        - relevance_score: PostgreSQL ts_rank relevance score (0.0-1.0)

    Examples:
        # Search for "error" in all label content
        results = await search_labels_in_artifacts(db, "error")

        # Limited search for performance
        results = await search_labels_in_artifacts(db, "classification", limit=10)

    Note:
        The pipeline_name parameter is reserved for future pipeline-specific filtering
        but is not currently implemented. It's maintained for API compatibility.
    """
    try:
        # Note: pipeline_name parameter reserved for future pipeline-specific filtering

        # PostgreSQL full-text search with relevance scoring
        # Uses tsvector/tsquery for high-performance text search across large datasets
        base_query = """
            SELECT DISTINCT
                li.file_name as label_file,
                li.content as matching_content,
                li.metadata as label_metadata,
                li.row_index,
                ts_rank(li.search_vector, plainto_tsquery('english', :filter_value)) as relevance_score
            FROM label_index li
            WHERE li.search_vector @@ plainto_tsquery('english', :filter_value)
            ORDER BY relevance_score DESC
            LIMIT :limit  -- CRITICAL: Prevents memory exhaustion with large datasets (1 lakh+ rows)
        """

        # Parameterized query for security and performance
        params = {"filter_value": filter_value, "limit": limit}

        # Execute search query
        result = await db.execute(text(base_query), params)
        label_results = result.mappings().all()

        # Transform database results to API-compatible format
        # This ensures consistency with other artifact search functions
        converted_results = []
        for label_result in label_results:
            converted_results.append({
                'artifact_id': None,  # Label search doesn't map to specific artifacts
                'name': f"Label Match: {label_result['label_file']}",  # Descriptive name
                'uri': f"label://{label_result['label_file']}#{label_result['row_index']}",  # Unique label URI
                'type_id': None,
                'create_time_since_epoch': None,
                'last_update_time_since_epoch': None,
                # Label-specific fields for frontend processing
                'label_file': label_result['label_file'],
                'matching_content': label_result['matching_content'],
                'label_metadata': label_result['label_metadata'],
                'relevance_score': float(label_result['relevance_score'])  # Convert Decimal to float
            })

        return converted_results

    except Exception as e:
        # Log error but return empty list to prevent API failures
        # This allows partial success in combined searches
        print(f"Label search error: {e}")
        return []


async def search_labels_with_advanced_conditions(db: AsyncSession, conditions: list, pipeline_name: str = None, limit: int = 50):
    """
    Search for label artifacts using advanced JSONB queries for structured conditions.

    This function enables sophisticated search queries on CSV label data using PostgreSQL's
    JSONB operators. It supports numeric comparisons, text operations, and complex conditions
    that would be impossible with simple full-text search.

    Advanced Search Capabilities:
    - Numeric comparisons: "lines>240", "score<=0.5", "confidence>=0.8"
    - Text operations: "status~active", "name!~error"
    - Multiple conditions: Combined with AND logic
    - Type-aware queries: Automatic type casting for proper comparisons

    Performance Features:
    - Uses JSONB indexes for fast query execution
    - Deterministic ordering for consistent pagination
    - LIMIT parameter prevents performance degradation
    - Efficient query plan generation

    Args:
        db: Database session for executing queries
        conditions: List of SearchCondition objects from AdvancedSearchParser
        pipeline_name: Optional pipeline name filter (reserved for future use)
        limit: Maximum number of results to return (default: 50)

    Returns:
        List of dictionaries containing:
        - label_file: Source CSV filename
        - matching_content: The actual content that matched
        - label_metadata: Raw metadata from the CSV row
        - parsed_data: Type-converted data used for the search
        - row_index: Row number within the CSV file
        - relevance_score: Static score (1.0) for deterministic ordering

    Examples:
        # Numeric comparison
        conditions = [SearchCondition("lines", ComparisonOperator.GREATER_THAN, 240)]
        results = await search_labels_with_advanced_conditions(db, conditions)

        # Text operation
        conditions = [SearchCondition("status", ComparisonOperator.CONTAINS, "active")]
        results = await search_labels_with_advanced_conditions(db, conditions)

        # Multiple conditions
        conditions = [
            SearchCondition("lines", ComparisonOperator.GREATER_THAN, 240),
            SearchCondition("score", ComparisonOperator.LESS_EQUAL, 0.5)
        ]
        results = await search_labels_with_advanced_conditions(db, conditions)

    Note:
        The pipeline_name parameter is reserved for future pipeline-specific filtering
        but is not currently implemented. It's maintained for API compatibility.
    """
    try:
        # Note: pipeline_name parameter reserved for future pipeline-specific filtering

        # Import query builder for JSONB condition construction
        from server.app.label_management import JsonbQueryBuilder

        # Step 1: Convert SearchCondition objects to PostgreSQL JSONB WHERE clause
        where_clause, params = JsonbQueryBuilder.build_where_clause(conditions)

        # Early return if no valid conditions provided
        if not where_clause:
            return []

        # Step 2: Build advanced search query using JSONB operators
        # This enables type-aware comparisons on parsed CSV data
        base_query = f"""
            SELECT DISTINCT
                li.file_name as label_file,
                li.content as matching_content,
                li.metadata as label_metadata,
                li.parsed_data,
                li.row_index,
                1.0 as relevance_score  -- Static score for advanced search
            FROM label_index li
            WHERE {where_clause}  -- Dynamic JSONB conditions (e.g., parsed_data->>'lines'::numeric > 240)
            ORDER BY li.file_name, li.row_index  -- Consistent ordering for pagination
            LIMIT :limit  -- ESSENTIAL: Prevents performance degradation with large datasets
        """

        # Step 3: Add limit parameter to the existing condition parameters
        params["limit"] = limit

        # Step 4: Execute the parameterized query
        result = await db.execute(text(base_query), params)
        label_results = result.mappings().all()

        # Step 5: Transform results to consistent format
        # Maintains compatibility with other search functions
        converted_results = []
        for row in label_results:
            converted_results.append({
                'label_file': row['label_file'],
                'matching_content': row['matching_content'],
                'label_metadata': row['label_metadata'],
                'parsed_data': row['parsed_data'],  # Include parsed data for debugging
                'row_index': row['row_index'],
                'relevance_score': row['relevance_score']
            })

        return converted_results

    except Exception as e:
        # Log error but return empty list to prevent API failures
        # This allows graceful degradation in combined searches
        print(f"Advanced label search error: {e}")
        return []


async def search_labels_combined(db: AsyncSession, plain_terms: list = None, conditions: list = None, pipeline_name: str = None, limit: int = 50):
    """
    Combined search function that handles both full-text search and advanced JSONB conditions.

    This is the main entry point for label content search, combining multiple search strategies
    to provide comprehensive search capabilities. It intelligently combines full-text search
    with structured condition matching for maximum flexibility.

    Search Strategy:
    1. Execute full-text search on plain terms (if provided)
    2. Execute advanced JSONB search on conditions (if provided)
    3. Combine and deduplicate results from both searches
    4. Sort by relevance score for optimal user experience
    5. Apply final limit for performance protection

    Deduplication Logic:
    - Uses (file_name, row_index) as unique key
    - Prevents duplicate results when same row matches both searches
    - Maintains highest relevance score for duplicates

    Performance Optimizations:
    - Individual search functions have their own limits
    - Final deduplication and sorting on smaller result sets
    - Multiple layers of limit protection
    - Efficient set-based duplicate detection

    Args:
        db: Database session for executing queries
        plain_terms: List of plain text terms for full-text search (e.g., ["error", "classification"])
        conditions: List of SearchCondition objects for advanced search (e.g., lines>240)
        pipeline_name: Optional pipeline name filter (reserved for future use)
        limit: Maximum number of results to return after deduplication (default: 50)

    Returns:
        List of dictionaries containing combined and deduplicated results:
        - Results from full-text search (with relevance scores)
        - Results from advanced search (with static scores)
        - Sorted by relevance score (descending) then by filename
        - Limited to specified maximum count

    Examples:
        # Full-text search only
        results = await search_labels_combined(db, plain_terms=["error", "classification"])

        # Advanced search only
        conditions = [SearchCondition("lines", ComparisonOperator.GREATER_THAN, 240)]
        results = await search_labels_combined(db, conditions=conditions)

        # Combined search (most powerful)
        results = await search_labels_combined(
            db,
            plain_terms=["error"],
            conditions=[SearchCondition("confidence", ComparisonOperator.LESS_THAN, 0.5)]
        )

    Note:
        The pipeline_name parameter is reserved for future pipeline-specific filtering
        but is not currently implemented. It's maintained for API compatibility.
    """
    try:
        # Note: pipeline_name parameter reserved for future pipeline-specific filtering

        # Step 1: Initialize results collection
        results = []

        # Step 2: Execute full-text search if plain text terms are provided
        # This handles searches like "error classification" or "data processing"
        if plain_terms:
            plain_search_term = " ".join(plain_terms)
            if plain_search_term.strip():  # Ensure non-empty search term
                # Full-text search with individual limit for performance protection
                text_results = await search_labels_in_artifacts(db, plain_search_term, pipeline_name, limit)
                results.extend(text_results)

        # Step 3: Execute advanced JSONB search if structured conditions are provided
        # This handles searches like "lines>240 AND score<=0.5"
        if conditions:
            # Advanced search with individual limit for complex query protection
            advanced_results = await search_labels_with_advanced_conditions(db, conditions, pipeline_name, limit)
            results.extend(advanced_results)

        # Step 4: Deduplication - Remove duplicate rows from combined results
        # Critical when same CSV row matches both full-text and advanced criteria
        # Example: Row contains "error" (text match) AND has lines>240 (condition match)
        seen = set()
        unique_results = []
        for result in results:
            # Use (filename, row_index) as unique identifier
            key = (result['label_file'], result.get('row_index', 0))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
                # Note: First occurrence wins (preserves higher relevance scores from text search)

        # Step 5: Sort results for optimal user experience
        # Primary sort: Relevance score (descending) - best matches first
        # Secondary sort: Filename (ascending) - consistent ordering for same scores
        unique_results.sort(key=lambda x: (-x.get('relevance_score', 0), x['label_file']))

        # Step 6: Apply final limit as last line of defense
        # Even with individual limits and deduplication, ensure response size is manageable
        # This protects against edge cases where deduplication is minimal
        return unique_results[:limit]

    except Exception as e:
        # Log error but return empty list to prevent complete API failure
        # This allows other search components to continue functioning
        print(f"Combined label search error: {e}")
        return []
