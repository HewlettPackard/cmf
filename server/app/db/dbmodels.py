from sqlalchemy import(
    Table,
    Column,
    Integer,
    BigInteger,
    Text,
    String,
    Boolean,
    Double,
    LargeBinary,
    Index,
    UniqueConstraint,
    MetaData,
    SmallInteger
)

metadata = MetaData()

artifact = Table(
    "artifact", metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("type_id", Integer, nullable=False),
    Column("uri", Text),
    Column("state", Integer),
    Column("name", String(255)),
    Column("external_id", String(255), unique=True),
    Column("create_time_since_epoch", BigInteger, nullable=False),
    Column("last_update_time_since_epoch", BigInteger, nullable=False),
    
    # Indexes
    Index("idx_artifact_create_time_since_epoch", "create_time_since_epoch"),
    Index("idx_artifact_external_id", "external_id"),
    Index("idx_artifact_last_update_time_since_epoch", "last_update_time_since_epoch"),
    Index("idx_artifact_uri", "uri"),
    
    # Constraints
    UniqueConstraint("type_id", "name", name="uniqueartifacttypename")
)


artifactproperty = Table(
    "artifactproperty", metadata,
    Column("artifact_id", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("is_custom_property", Boolean, nullable=False),
    Column("int_value", Integer),
    Column("double_value", Double),
    Column("string_value", Text),
    Column("byte_value", LargeBinary),
    Column("proto_value", LargeBinary),
    Column("bool_value", Boolean),
    
    # Primary Key
    UniqueConstraint("artifact_id", "name", "is_custom_property", name="artifactproperty_pkey"),
    
    # Indexes
    Index("idx_artifact_property_double", "name", "is_custom_property", "double_value"),
    Index("idx_artifact_property_int", "name", "is_custom_property", "int_value"),
    Index("idx_artifact_property_string", "name", "is_custom_property", "string_value")
)


context = Table(
    "context", metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("type_id", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("external_id", String(255), unique=True),
    Column("create_time_since_epoch", BigInteger, nullable=False),
    Column("last_update_time_since_epoch", BigInteger, nullable=False),

    # Unique Constraints
    UniqueConstraint("type_id", "name", name="context_type_id_name_key"),

    # Indexes
    Index("idx_context_create_time_since_epoch", "create_time_since_epoch"),
    Index("idx_context_external_id", "external_id"),
    Index("idx_context_last_update_time_since_epoch", "last_update_time_since_epoch")
)

parentcontext = Table(
    "parentcontext", metadata, 
    Column("context_id", Integer, nullable=False),
    Column("parent_context_id", Integer, nullable=False),

    # Primary Key
    UniqueConstraint("context_id", "parent_context_id", name="parentcontext_pkey"),

    # Indexes
    Index("idx_parentcontext_parent_context_id", "parent_context_id")
)

type_table = Table(
    "type", metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("name", String(255), nullable=False),
    Column("version", String(255)),
    Column("type_kind", SmallInteger, nullable=False),
    Column("description", Text),
    Column("input_type", Text),
    Column("output_type", Text),
    Column("external_id", String(255), unique=True),

    # Indexes 
    Index("idx_type_external_id", "external_id"),
    Index("idx_type_name", "name"),

    # Constraints
    UniqueConstraint("external_id", name="type_external_id_key")
)


attribution = Table(
    "attribution", metadata, 
    Column("id", Integer, primary_key=True, nullable=False),
    Column("context_id", Integer, nullable=False),
    Column("artifact_id", Integer, nullable=False),

    # Unique Constraint
    UniqueConstraint("context_id", "artifact_id", name="attribution_context_id_artifact_id_key") 
)


execution = Table(
    "execution", metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("type_id", Integer, nullable=False),
    Column("last_known_state", Integer),
    Column("name", String(255)),
    Column("external_id", String(255), unique=True),
    Column("create_time_since_epoch", BigInteger, nullable=False),
    Column("last_update_time_since_epoch", BigInteger, nullable=False),
    
    # Indexes
    Index("idx_execution_create_time_since_epoch", "create_time_since_epoch"),
    Index("idx_execution_external_id", "external_id"),
    Index("idx_execution_last_update_time_since_epoch", "last_update_time_since_epoch"),
    
    # Constraints
    UniqueConstraint("type_id", "name", name="uniqueexecutiontypename")
    # UniqueConstraint("external_id", name="execution_external_id_key")
)


executionproperty = Table(
    "executionproperty", metadata,
    Column("execution_id", Integer, nullable=False),
    Column("name", String(255), nullable=False),
    Column("is_custom_property", Boolean, nullable=False),
    Column("int_value", Integer),
    Column("double_value", Double),
    Column("string_value", Text),
    Column("byte_value", LargeBinary),
    Column("proto_value", LargeBinary),
    Column("bool_value", Boolean),
    
    # Primary Key
    UniqueConstraint("execution_id", "name", "is_custom_property", name="executionproperty_pkey"),
    
    # Indexes
    Index("idx_execution_property_double", "name", "is_custom_property", "double_value"),
    Index("idx_execution_property_int", "name", "is_custom_property", "int_value"),
    Index("idx_execution_property_string", "name", "is_custom_property", "string_value")
)


association = Table(
    "association", metadata, 
    Column("id", Integer, primary_key=True, nullable=False),
    Column("context_id", Integer, nullable=False),
    Column("execution_id", Integer, nullable=False),

    # Unique Constraint
    UniqueConstraint("context_id", "execution_id", name="association_context_id_execution_id_key") 
)


event = Table(
    "event", metadata, 
    Column("id", Integer, primary_key=True, nullable=False),
    Column("artifact_id", Integer, nullable=False),
    Column("execution_id", Integer, nullable=False),
    Column("type", Integer, nullable=False),
    Column("milliseconds_since_epoch", BigInteger),

    # Unique Constraint
    UniqueConstraint("artifact_id", "execution_id", "type", name="uniqueevent") 
)