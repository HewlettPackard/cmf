from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import descriptor_pb2 as _descriptor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf.internal import python_message as _python_message
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

BOOLEAN: PropertyType
DESCRIPTOR: _descriptor.FileDescriptor
DOUBLE: PropertyType
INT: PropertyType
PROTO: PropertyType
STRING: PropertyType
STRUCT: PropertyType
SYSTEM_TYPE_EXTENSION_FIELD_NUMBER: _ClassVar[int]  # type: ignore # mypy error: ClassVar can only be used for assignments in class body
UNKNOWN: PropertyType
system_type_extension: _descriptor.FieldDescriptor

class AnyArtifactStructType(_message.Message):
    __slots__: list[str] = []
    def __init__(self) -> None: ...

class Artifact(_message.Message):
    __slots__ = ["create_time_since_epoch", "custom_properties", "external_id", "id", "last_update_time_since_epoch", "name", "properties", "state", "type", "type_id", "uri"]
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    class CustomPropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...
    CREATE_TIME_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    DELETED: Artifact.State
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATE_TIME_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    LIVE: Artifact.State
    MARKED_FOR_DELETION: Artifact.State
    NAME_FIELD_NUMBER: _ClassVar[int]
    PENDING: Artifact.State
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    UNKNOWN: Artifact.State
    URI_FIELD_NUMBER: _ClassVar[int]
    create_time_since_epoch: int
    custom_properties: _containers.MessageMap[str, Value]
    external_id: str
    id: int
    last_update_time_since_epoch: int
    name: str
    properties: _containers.MessageMap[str, Value]
    state: Artifact.State
    type: str
    type_id: int
    uri: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., type_id: _Optional[int] = ..., type: _Optional[str] = ..., uri: _Optional[str] = ..., external_id: _Optional[str] = ..., properties: _Optional[_Mapping[str, Value]] = ..., custom_properties: _Optional[_Mapping[str, Value]] = ..., state: _Optional[_Union[Artifact.State, str]] = ..., create_time_since_epoch: _Optional[int] = ..., last_update_time_since_epoch: _Optional[int] = ...) -> None: ...

class ArtifactStructType(_message.Message):
    __slots__ = ["any", "dict", "intersection", "list", "none", "simple", "tuple", "union_type"]
    ANY_FIELD_NUMBER: _ClassVar[int]
    DICT_FIELD_NUMBER: _ClassVar[int]
    INTERSECTION_FIELD_NUMBER: _ClassVar[int]
    LIST_FIELD_NUMBER: _ClassVar[int]
    NONE_FIELD_NUMBER: _ClassVar[int]
    SIMPLE_FIELD_NUMBER: _ClassVar[int]
    TUPLE_FIELD_NUMBER: _ClassVar[int]
    UNION_TYPE_FIELD_NUMBER: _ClassVar[int]
    any: AnyArtifactStructType
    dict: DictArtifactStructType
    intersection: IntersectionArtifactStructType
    list: ListArtifactStructType
    none: NoneArtifactStructType
    simple: ArtifactType
    tuple: TupleArtifactStructType
    union_type: UnionArtifactStructType
    def __init__(self, simple: _Optional[_Union[ArtifactType, _Mapping]] = ..., union_type: _Optional[_Union[UnionArtifactStructType, _Mapping]] = ..., intersection: _Optional[_Union[IntersectionArtifactStructType, _Mapping]] = ..., list: _Optional[_Union[ListArtifactStructType, _Mapping]] = ..., none: _Optional[_Union[NoneArtifactStructType, _Mapping]] = ..., any: _Optional[_Union[AnyArtifactStructType, _Mapping]] = ..., tuple: _Optional[_Union[TupleArtifactStructType, _Mapping]] = ..., dict: _Optional[_Union[DictArtifactStructType, _Mapping]] = ...) -> None: ...

class ArtifactType(_message.Message):
    __slots__ = ["base_type", "description", "external_id", "id", "name", "properties", "version"]
    class SystemDefinedBaseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: PropertyType
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[PropertyType, str]] = ...) -> None: ...
    BASE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATASET: ArtifactType.SystemDefinedBaseType
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    METRICS: ArtifactType.SystemDefinedBaseType
    MODEL: ArtifactType.SystemDefinedBaseType
    NAME_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    STATISTICS: ArtifactType.SystemDefinedBaseType
    UNSET: ArtifactType.SystemDefinedBaseType
    VERSION_FIELD_NUMBER: _ClassVar[int]
    base_type: ArtifactType.SystemDefinedBaseType
    description: str
    external_id: str
    id: int
    name: str
    properties: _containers.ScalarMap[str, PropertyType]
    version: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ..., external_id: _Optional[str] = ..., properties: _Optional[_Mapping[str, PropertyType]] = ..., base_type: _Optional[_Union[ArtifactType.SystemDefinedBaseType, str]] = ...) -> None: ...

class Association(_message.Message):
    __slots__ = ["context_id", "execution_id"]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    context_id: int
    execution_id: int
    def __init__(self, execution_id: _Optional[int] = ..., context_id: _Optional[int] = ...) -> None: ...

class Attribution(_message.Message):
    __slots__ = ["artifact_id", "context_id"]
    ARTIFACT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    artifact_id: int
    context_id: int
    def __init__(self, artifact_id: _Optional[int] = ..., context_id: _Optional[int] = ...) -> None: ...

class ConnectionConfig(_message.Message):
    __slots__ = ["fake_database", "mysql", "retry_options", "sqlite"]
    FAKE_DATABASE_FIELD_NUMBER: _ClassVar[int]
    MYSQL_FIELD_NUMBER: _ClassVar[int]
    RETRY_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    SQLITE_FIELD_NUMBER: _ClassVar[int]
    fake_database: FakeDatabaseConfig
    mysql: MySQLDatabaseConfig
    retry_options: RetryOptions
    sqlite: SqliteMetadataSourceConfig
    def __init__(self, fake_database: _Optional[_Union[FakeDatabaseConfig, _Mapping]] = ..., mysql: _Optional[_Union[MySQLDatabaseConfig, _Mapping]] = ..., sqlite: _Optional[_Union[SqliteMetadataSourceConfig, _Mapping]] = ..., retry_options: _Optional[_Union[RetryOptions, _Mapping]] = ...) -> None: ...

class Context(_message.Message):
    __slots__ = ["create_time_since_epoch", "custom_properties", "external_id", "id", "last_update_time_since_epoch", "name", "properties", "type", "type_id"]
    class CustomPropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...
    CREATE_TIME_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATE_TIME_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    create_time_since_epoch: int
    custom_properties: _containers.MessageMap[str, Value]
    external_id: str
    id: int
    last_update_time_since_epoch: int
    name: str
    properties: _containers.MessageMap[str, Value]
    type: str
    type_id: int
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., type_id: _Optional[int] = ..., type: _Optional[str] = ..., external_id: _Optional[str] = ..., properties: _Optional[_Mapping[str, Value]] = ..., custom_properties: _Optional[_Mapping[str, Value]] = ..., create_time_since_epoch: _Optional[int] = ..., last_update_time_since_epoch: _Optional[int] = ...) -> None: ...

class ContextType(_message.Message):
    __slots__ = ["base_type", "description", "external_id", "id", "name", "properties", "version"]
    class SystemDefinedBaseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: PropertyType
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[PropertyType, str]] = ...) -> None: ...
    BASE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    UNSET: ContextType.SystemDefinedBaseType
    VERSION_FIELD_NUMBER: _ClassVar[int]
    base_type: ContextType.SystemDefinedBaseType
    description: str
    external_id: str
    id: int
    name: str
    properties: _containers.ScalarMap[str, PropertyType]
    version: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ..., external_id: _Optional[str] = ..., properties: _Optional[_Mapping[str, PropertyType]] = ..., base_type: _Optional[_Union[ContextType.SystemDefinedBaseType, str]] = ...) -> None: ...

class DictArtifactStructType(_message.Message):
    __slots__ = ["extra_properties_type", "none_type_not_required", "properties"]
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ArtifactStructType
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ArtifactStructType, _Mapping]] = ...) -> None: ...
    EXTRA_PROPERTIES_TYPE_FIELD_NUMBER: _ClassVar[int]
    NONE_TYPE_NOT_REQUIRED_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    extra_properties_type: ArtifactStructType
    none_type_not_required: bool
    properties: _containers.MessageMap[str, ArtifactStructType]
    def __init__(self, properties: _Optional[_Mapping[str, ArtifactStructType]] = ..., none_type_not_required: bool = ..., extra_properties_type: _Optional[_Union[ArtifactStructType, _Mapping]] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ["artifact_id", "execution_id", "milliseconds_since_epoch", "path", "type"]
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    class Path(_message.Message):
        __slots__ = ["steps"]
        class Step(_message.Message):
            __slots__ = ["index", "key"]
            INDEX_FIELD_NUMBER: _ClassVar[int]
            KEY_FIELD_NUMBER: _ClassVar[int]
            index: int
            key: str
            def __init__(self, index: _Optional[int] = ..., key: _Optional[str] = ...) -> None: ...
        STEPS_FIELD_NUMBER: _ClassVar[int]
        steps: _containers.RepeatedCompositeFieldContainer[Event.Path.Step]
        def __init__(self, steps: _Optional[_Iterable[_Union[Event.Path.Step, _Mapping]]] = ...) -> None: ...
    ARTIFACT_ID_FIELD_NUMBER: _ClassVar[int]
    DECLARED_INPUT: Event.Type
    DECLARED_OUTPUT: Event.Type
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT: Event.Type
    INTERNAL_INPUT: Event.Type
    INTERNAL_OUTPUT: Event.Type
    MILLISECONDS_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    OUTPUT: Event.Type
    PATH_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    UNKNOWN: Event.Type
    artifact_id: int
    execution_id: int
    milliseconds_since_epoch: int
    path: Event.Path
    type: Event.Type
    def __init__(self, artifact_id: _Optional[int] = ..., execution_id: _Optional[int] = ..., path: _Optional[_Union[Event.Path, _Mapping]] = ..., type: _Optional[_Union[Event.Type, str]] = ..., milliseconds_since_epoch: _Optional[int] = ...) -> None: ...

class Execution(_message.Message):
    __slots__ = ["create_time_since_epoch", "custom_properties", "external_id", "id", "last_known_state", "last_update_time_since_epoch", "name", "properties", "type", "type_id"]
    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    class CustomPropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...
    CACHED: Execution.State
    CANCELED: Execution.State
    COMPLETE: Execution.State
    CREATE_TIME_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    FAILED: Execution.State
    ID_FIELD_NUMBER: _ClassVar[int]
    LAST_KNOWN_STATE_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATE_TIME_SINCE_EPOCH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NEW: Execution.State
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    RUNNING: Execution.State
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    UNKNOWN: Execution.State
    create_time_since_epoch: int
    custom_properties: _containers.MessageMap[str, Value]
    external_id: str
    id: int
    last_known_state: Execution.State
    last_update_time_since_epoch: int
    name: str
    properties: _containers.MessageMap[str, Value]
    type: str
    type_id: int
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., type_id: _Optional[int] = ..., type: _Optional[str] = ..., external_id: _Optional[str] = ..., last_known_state: _Optional[_Union[Execution.State, str]] = ..., properties: _Optional[_Mapping[str, Value]] = ..., custom_properties: _Optional[_Mapping[str, Value]] = ..., create_time_since_epoch: _Optional[int] = ..., last_update_time_since_epoch: _Optional[int] = ...) -> None: ...

class ExecutionType(_message.Message):
    __slots__ = ["base_type", "description", "external_id", "id", "input_type", "name", "output_type", "properties", "version"]
    class SystemDefinedBaseType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: PropertyType
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[PropertyType, str]] = ...) -> None: ...
    BASE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEPLOY: ExecutionType.SystemDefinedBaseType
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EVALUATE: ExecutionType.SystemDefinedBaseType
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROCESS: ExecutionType.SystemDefinedBaseType
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    TRAIN: ExecutionType.SystemDefinedBaseType
    TRANSFORM: ExecutionType.SystemDefinedBaseType
    UNSET: ExecutionType.SystemDefinedBaseType
    VERSION_FIELD_NUMBER: _ClassVar[int]
    base_type: ExecutionType.SystemDefinedBaseType
    description: str
    external_id: str
    id: int
    input_type: ArtifactStructType
    name: str
    output_type: ArtifactStructType
    properties: _containers.ScalarMap[str, PropertyType]
    version: str
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., version: _Optional[str] = ..., description: _Optional[str] = ..., external_id: _Optional[str] = ..., properties: _Optional[_Mapping[str, PropertyType]] = ..., input_type: _Optional[_Union[ArtifactStructType, _Mapping]] = ..., output_type: _Optional[_Union[ArtifactStructType, _Mapping]] = ..., base_type: _Optional[_Union[ExecutionType.SystemDefinedBaseType, str]] = ...) -> None: ...

class FakeDatabaseConfig(_message.Message):
    __slots__: list[str] = []
    def __init__(self) -> None: ...

class GrpcChannelArguments(_message.Message):
    __slots__ = ["http2_max_ping_strikes", "max_receive_message_length"]
    HTTP2_MAX_PING_STRIKES_FIELD_NUMBER: _ClassVar[int]
    MAX_RECEIVE_MESSAGE_LENGTH_FIELD_NUMBER: _ClassVar[int]
    http2_max_ping_strikes: int
    max_receive_message_length: int
    def __init__(self, max_receive_message_length: _Optional[int] = ..., http2_max_ping_strikes: _Optional[int] = ...) -> None: ...

class IntersectionArtifactStructType(_message.Message):
    __slots__ = ["constraints"]
    CONSTRAINTS_FIELD_NUMBER: _ClassVar[int]
    constraints: _containers.RepeatedCompositeFieldContainer[ArtifactStructType]
    def __init__(self, constraints: _Optional[_Iterable[_Union[ArtifactStructType, _Mapping]]] = ...) -> None: ...

class LineageGraph(_message.Message):
    __slots__ = ["artifact_types", "artifacts", "associations", "attributions", "context_types", "contexts", "events", "execution_types", "executions"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_TYPES_FIELD_NUMBER: _ClassVar[int]
    ASSOCIATIONS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTIONS_FIELD_NUMBER: _ClassVar[int]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_TYPES_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TYPES_FIELD_NUMBER: _ClassVar[int]
    artifact_types: _containers.RepeatedCompositeFieldContainer[ArtifactType]
    artifacts: _containers.RepeatedCompositeFieldContainer[Artifact]
    associations: _containers.RepeatedCompositeFieldContainer[Association]
    attributions: _containers.RepeatedCompositeFieldContainer[Attribution]
    context_types: _containers.RepeatedCompositeFieldContainer[ContextType]
    contexts: _containers.RepeatedCompositeFieldContainer[Context]
    events: _containers.RepeatedCompositeFieldContainer[Event]
    execution_types: _containers.RepeatedCompositeFieldContainer[ExecutionType]
    executions: _containers.RepeatedCompositeFieldContainer[Execution]
    def __init__(self, artifact_types: _Optional[_Iterable[_Union[ArtifactType, _Mapping]]] = ..., execution_types: _Optional[_Iterable[_Union[ExecutionType, _Mapping]]] = ..., context_types: _Optional[_Iterable[_Union[ContextType, _Mapping]]] = ..., artifacts: _Optional[_Iterable[_Union[Artifact, _Mapping]]] = ..., executions: _Optional[_Iterable[_Union[Execution, _Mapping]]] = ..., contexts: _Optional[_Iterable[_Union[Context, _Mapping]]] = ..., events: _Optional[_Iterable[_Union[Event, _Mapping]]] = ..., attributions: _Optional[_Iterable[_Union[Attribution, _Mapping]]] = ..., associations: _Optional[_Iterable[_Union[Association, _Mapping]]] = ...) -> None: ...

class LineageGraphQueryOptions(_message.Message):
    __slots__ = ["artifacts_options", "max_node_size", "stop_conditions"]
    class BoundaryConstraint(_message.Message):
        __slots__ = ["boundary_artifacts", "boundary_executions", "max_num_hops"]
        BOUNDARY_ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
        BOUNDARY_EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
        MAX_NUM_HOPS_FIELD_NUMBER: _ClassVar[int]
        boundary_artifacts: str
        boundary_executions: str
        max_num_hops: int
        def __init__(self, max_num_hops: _Optional[int] = ..., boundary_artifacts: _Optional[str] = ..., boundary_executions: _Optional[str] = ...) -> None: ...
    ARTIFACTS_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    MAX_NODE_SIZE_FIELD_NUMBER: _ClassVar[int]
    STOP_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    artifacts_options: ListOperationOptions
    max_node_size: int
    stop_conditions: LineageGraphQueryOptions.BoundaryConstraint
    def __init__(self, artifacts_options: _Optional[_Union[ListOperationOptions, _Mapping]] = ..., stop_conditions: _Optional[_Union[LineageGraphQueryOptions.BoundaryConstraint, _Mapping]] = ..., max_node_size: _Optional[int] = ...) -> None: ...

class ListArtifactStructType(_message.Message):
    __slots__ = ["element"]
    ELEMENT_FIELD_NUMBER: _ClassVar[int]
    element: ArtifactStructType
    def __init__(self, element: _Optional[_Union[ArtifactStructType, _Mapping]] = ...) -> None: ...

class ListOperationNextPageToken(_message.Message):
    __slots__ = ["field_offset", "id_offset", "listed_ids", "set_options"]
    FIELD_OFFSET_FIELD_NUMBER: _ClassVar[int]
    ID_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LISTED_IDS_FIELD_NUMBER: _ClassVar[int]
    SET_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    field_offset: int
    id_offset: int
    listed_ids: _containers.RepeatedScalarFieldContainer[int]
    set_options: ListOperationOptions
    def __init__(self, id_offset: _Optional[int] = ..., field_offset: _Optional[int] = ..., set_options: _Optional[_Union[ListOperationOptions, _Mapping]] = ..., listed_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class ListOperationOptions(_message.Message):
    __slots__ = ["filter_query", "max_result_size", "next_page_token", "order_by_field"]
    class OrderByField(_message.Message):
        __slots__ = ["field", "is_asc"]
        class Field(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__: list[str] = []
        CREATE_TIME: ListOperationOptions.OrderByField.Field
        FIELD_FIELD_NUMBER: _ClassVar[int]
        FIELD_UNSPECIFIED: ListOperationOptions.OrderByField.Field
        ID: ListOperationOptions.OrderByField.Field
        IS_ASC_FIELD_NUMBER: _ClassVar[int]
        LAST_UPDATE_TIME: ListOperationOptions.OrderByField.Field
        field: ListOperationOptions.OrderByField.Field
        is_asc: bool
        def __init__(self, field: _Optional[_Union[ListOperationOptions.OrderByField.Field, str]] = ..., is_asc: bool = ...) -> None: ...
    FILTER_QUERY_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULT_SIZE_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ORDER_BY_FIELD_FIELD_NUMBER: _ClassVar[int]
    filter_query: str
    max_result_size: int
    next_page_token: str
    order_by_field: ListOperationOptions.OrderByField
    def __init__(self, max_result_size: _Optional[int] = ..., order_by_field: _Optional[_Union[ListOperationOptions.OrderByField, _Mapping]] = ..., next_page_token: _Optional[str] = ..., filter_query: _Optional[str] = ...) -> None: ...

class MetadataStoreClientConfig(_message.Message):
    __slots__ = ["channel_arguments", "client_timeout_sec", "host", "port", "ssl_config"]
    class SSLConfig(_message.Message):
        __slots__ = ["client_key", "custom_ca", "server_cert"]
        CLIENT_KEY_FIELD_NUMBER: _ClassVar[int]
        CUSTOM_CA_FIELD_NUMBER: _ClassVar[int]
        SERVER_CERT_FIELD_NUMBER: _ClassVar[int]
        client_key: str
        custom_ca: str
        server_cert: str
        def __init__(self, client_key: _Optional[str] = ..., server_cert: _Optional[str] = ..., custom_ca: _Optional[str] = ...) -> None: ...
    CHANNEL_ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    CLIENT_TIMEOUT_SEC_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SSL_CONFIG_FIELD_NUMBER: _ClassVar[int]
    channel_arguments: GrpcChannelArguments
    client_timeout_sec: float
    host: str
    port: int
    ssl_config: MetadataStoreClientConfig.SSLConfig
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., ssl_config: _Optional[_Union[MetadataStoreClientConfig.SSLConfig, _Mapping]] = ..., channel_arguments: _Optional[_Union[GrpcChannelArguments, _Mapping]] = ..., client_timeout_sec: _Optional[float] = ...) -> None: ...

class MetadataStoreServerConfig(_message.Message):
    __slots__ = ["connection_config", "migration_options", "ssl_config"]
    class SSLConfig(_message.Message):
        __slots__ = ["client_verify", "custom_ca", "server_cert", "server_key"]
        CLIENT_VERIFY_FIELD_NUMBER: _ClassVar[int]
        CUSTOM_CA_FIELD_NUMBER: _ClassVar[int]
        SERVER_CERT_FIELD_NUMBER: _ClassVar[int]
        SERVER_KEY_FIELD_NUMBER: _ClassVar[int]
        client_verify: bool
        custom_ca: str
        server_cert: str
        server_key: str
        def __init__(self, server_key: _Optional[str] = ..., server_cert: _Optional[str] = ..., custom_ca: _Optional[str] = ..., client_verify: bool = ...) -> None: ...
    CONNECTION_CONFIG_FIELD_NUMBER: _ClassVar[int]
    MIGRATION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    SSL_CONFIG_FIELD_NUMBER: _ClassVar[int]
    connection_config: ConnectionConfig
    migration_options: MigrationOptions
    ssl_config: MetadataStoreServerConfig.SSLConfig
    def __init__(self, connection_config: _Optional[_Union[ConnectionConfig, _Mapping]] = ..., migration_options: _Optional[_Union[MigrationOptions, _Mapping]] = ..., ssl_config: _Optional[_Union[MetadataStoreServerConfig.SSLConfig, _Mapping]] = ...) -> None: ...

class MigrationOptions(_message.Message):
    __slots__ = ["downgrade_to_schema_version", "enable_upgrade_migration"]
    DOWNGRADE_TO_SCHEMA_VERSION_FIELD_NUMBER: _ClassVar[int]
    ENABLE_UPGRADE_MIGRATION_FIELD_NUMBER: _ClassVar[int]
    downgrade_to_schema_version: int
    enable_upgrade_migration: bool
    def __init__(self, enable_upgrade_migration: bool = ..., downgrade_to_schema_version: _Optional[int] = ...) -> None: ...

class MySQLDatabaseConfig(_message.Message):
    __slots__ = ["database", "host", "password", "port", "skip_db_creation", "socket", "ssl_options", "user"]
    class SSLOptions(_message.Message):
        __slots__ = ["ca", "capath", "cert", "cipher", "key", "verify_server_cert"]
        CAPATH_FIELD_NUMBER: _ClassVar[int]
        CA_FIELD_NUMBER: _ClassVar[int]
        CERT_FIELD_NUMBER: _ClassVar[int]
        CIPHER_FIELD_NUMBER: _ClassVar[int]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VERIFY_SERVER_CERT_FIELD_NUMBER: _ClassVar[int]
        ca: str
        capath: str
        cert: str
        cipher: str
        key: str
        verify_server_cert: bool
        def __init__(self, key: _Optional[str] = ..., cert: _Optional[str] = ..., ca: _Optional[str] = ..., capath: _Optional[str] = ..., cipher: _Optional[str] = ..., verify_server_cert: bool = ...) -> None: ...
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    SKIP_DB_CREATION_FIELD_NUMBER: _ClassVar[int]
    SOCKET_FIELD_NUMBER: _ClassVar[int]
    SSL_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    database: str
    host: str
    password: str
    port: int
    skip_db_creation: bool
    socket: str
    ssl_options: MySQLDatabaseConfig.SSLOptions
    user: str
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., database: _Optional[str] = ..., user: _Optional[str] = ..., password: _Optional[str] = ..., socket: _Optional[str] = ..., ssl_options: _Optional[_Union[MySQLDatabaseConfig.SSLOptions, _Mapping]] = ..., skip_db_creation: bool = ...) -> None: ...

class NoneArtifactStructType(_message.Message):
    __slots__: list[str] = []
    def __init__(self) -> None: ...

class ParentContext(_message.Message):
    __slots__ = ["child_id", "parent_id"]
    CHILD_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    child_id: int
    parent_id: int
    def __init__(self, child_id: _Optional[int] = ..., parent_id: _Optional[int] = ...) -> None: ...

class RetryOptions(_message.Message):
    __slots__ = ["max_num_retries"]
    MAX_NUM_RETRIES_FIELD_NUMBER: _ClassVar[int]
    max_num_retries: int
    def __init__(self, max_num_retries: _Optional[int] = ...) -> None: ...

class SqliteMetadataSourceConfig(_message.Message):
    __slots__ = ["connection_mode", "filename_uri"]
    class ConnectionMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__: list[str] = []
    CONNECTION_MODE_FIELD_NUMBER: _ClassVar[int]
    FILENAME_URI_FIELD_NUMBER: _ClassVar[int]
    READONLY: SqliteMetadataSourceConfig.ConnectionMode
    READWRITE: SqliteMetadataSourceConfig.ConnectionMode
    READWRITE_OPENCREATE: SqliteMetadataSourceConfig.ConnectionMode
    UNKNOWN: SqliteMetadataSourceConfig.ConnectionMode
    connection_mode: SqliteMetadataSourceConfig.ConnectionMode
    filename_uri: str
    def __init__(self, filename_uri: _Optional[str] = ..., connection_mode: _Optional[_Union[SqliteMetadataSourceConfig.ConnectionMode, str]] = ...) -> None: ...

class SystemTypeExtension(_message.Message):
    __slots__ = ["type_name"]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    type_name: str
    def __init__(self, type_name: _Optional[str] = ...) -> None: ...

class TransactionOptions(_message.Message):
    __slots__ = ["tag"]
    Extensions: _python_message._ExtensionDict  # type: ignore
    TAG_FIELD_NUMBER: _ClassVar[int]
    tag: str
    def __init__(self, tag: _Optional[str] = ...) -> None: ...

class TupleArtifactStructType(_message.Message):
    __slots__ = ["elements"]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    elements: _containers.RepeatedCompositeFieldContainer[ArtifactStructType]
    def __init__(self, elements: _Optional[_Iterable[_Union[ArtifactStructType, _Mapping]]] = ...) -> None: ...

class UnionArtifactStructType(_message.Message):
    __slots__ = ["candidates"]
    CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    candidates: _containers.RepeatedCompositeFieldContainer[ArtifactStructType]
    def __init__(self, candidates: _Optional[_Iterable[_Union[ArtifactStructType, _Mapping]]] = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ["bool_value", "double_value", "int_value", "proto_value", "string_value", "struct_value"]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    PROTO_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRUCT_VALUE_FIELD_NUMBER: _ClassVar[int]
    bool_value: bool
    double_value: float
    int_value: int
    proto_value: _any_pb2.Any
    string_value: str
    struct_value: _struct_pb2.Struct
    def __init__(self, int_value: _Optional[int] = ..., double_value: _Optional[float] = ..., string_value: _Optional[str] = ..., struct_value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., proto_value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., bool_value: bool = ...) -> None: ...

class PropertyType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__: list[str] = []
