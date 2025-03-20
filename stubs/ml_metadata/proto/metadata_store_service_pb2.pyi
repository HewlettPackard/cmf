from ml_metadata.proto import metadata_store_pb2 as _metadata_store_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ArtifactAndType(_message.Message):
    __slots__ = ["artifact", "type"]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    artifact: _metadata_store_pb2.Artifact
    type: _metadata_store_pb2.ArtifactType
    def __init__(self, artifact: _Optional[_Union[_metadata_store_pb2.Artifact, _Mapping]] = ..., type: _Optional[_Union[_metadata_store_pb2.ArtifactType, _Mapping]] = ...) -> None: ...

class ArtifactStruct(_message.Message):
    __slots__ = ["artifact", "list", "map"]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    LIST_FIELD_NUMBER: _ClassVar[int]
    MAP_FIELD_NUMBER: _ClassVar[int]
    artifact: ArtifactAndType
    list: ArtifactStructList
    map: ArtifactStructMap
    def __init__(self, artifact: _Optional[_Union[ArtifactAndType, _Mapping]] = ..., map: _Optional[_Union[ArtifactStructMap, _Mapping]] = ..., list: _Optional[_Union[ArtifactStructList, _Mapping]] = ...) -> None: ...

class ArtifactStructList(_message.Message):
    __slots__ = ["elements"]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    elements: _containers.RepeatedCompositeFieldContainer[ArtifactStruct]
    def __init__(self, elements: _Optional[_Iterable[_Union[ArtifactStruct, _Mapping]]] = ...) -> None: ...

class ArtifactStructMap(_message.Message):
    __slots__ = ["properties"]
    class PropertiesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ArtifactStruct
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ArtifactStruct, _Mapping]] = ...) -> None: ...
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    properties: _containers.MessageMap[str, ArtifactStruct]
    def __init__(self, properties: _Optional[_Mapping[str, ArtifactStruct]] = ...) -> None: ...

class GetArtifactByTypeAndNameRequest(_message.Message):
    __slots__ = ["artifact_name", "transaction_options", "type_name", "type_version"]
    ARTIFACT_NAME_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    artifact_name: str
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., artifact_name: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactByTypeAndNameResponse(_message.Message):
    __slots__ = ["artifact"]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    artifact: _metadata_store_pb2.Artifact
    def __init__(self, artifact: _Optional[_Union[_metadata_store_pb2.Artifact, _Mapping]] = ...) -> None: ...

class GetArtifactTypeRequest(_message.Message):
    __slots__ = ["transaction_options", "type_name", "type_version"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactTypeResponse(_message.Message):
    __slots__ = ["artifact_type"]
    ARTIFACT_TYPE_FIELD_NUMBER: _ClassVar[int]
    artifact_type: _metadata_store_pb2.ArtifactType
    def __init__(self, artifact_type: _Optional[_Union[_metadata_store_pb2.ArtifactType, _Mapping]] = ...) -> None: ...

class GetArtifactTypesByExternalIdsRequest(_message.Message):
    __slots__ = ["external_ids", "transaction_options"]
    EXTERNAL_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    external_ids: _containers.RepeatedScalarFieldContainer[str]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, external_ids: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactTypesByExternalIdsResponse(_message.Message):
    __slots__ = ["artifact_types"]
    ARTIFACT_TYPES_FIELD_NUMBER: _ClassVar[int]
    artifact_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ArtifactType]
    def __init__(self, artifact_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ArtifactType, _Mapping]]] = ...) -> None: ...

class GetArtifactTypesByIDRequest(_message.Message):
    __slots__ = ["transaction_options", "type_ids"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_IDS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, type_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactTypesByIDResponse(_message.Message):
    __slots__ = ["artifact_types"]
    ARTIFACT_TYPES_FIELD_NUMBER: _ClassVar[int]
    artifact_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ArtifactType]
    def __init__(self, artifact_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ArtifactType, _Mapping]]] = ...) -> None: ...

class GetArtifactTypesRequest(_message.Message):
    __slots__ = ["transaction_options"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactTypesResponse(_message.Message):
    __slots__ = ["artifact_types"]
    ARTIFACT_TYPES_FIELD_NUMBER: _ClassVar[int]
    artifact_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ArtifactType]
    def __init__(self, artifact_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ArtifactType, _Mapping]]] = ...) -> None: ...

class GetArtifactsByContextRequest(_message.Message):
    __slots__ = ["context_id", "options", "transaction_options"]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    context_id: int
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, context_id: _Optional[int] = ..., options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactsByContextResponse(_message.Message):
    __slots__ = ["artifacts", "next_page_token"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    next_page_token: str
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetArtifactsByExternalIdsRequest(_message.Message):
    __slots__ = ["external_ids", "transaction_options"]
    EXTERNAL_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    external_ids: _containers.RepeatedScalarFieldContainer[str]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, external_ids: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactsByExternalIdsResponse(_message.Message):
    __slots__ = ["artifacts"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ...) -> None: ...

class GetArtifactsByIDRequest(_message.Message):
    __slots__ = ["artifact_ids", "transaction_options"]
    ARTIFACT_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    artifact_ids: _containers.RepeatedScalarFieldContainer[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, artifact_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactsByIDResponse(_message.Message):
    __slots__ = ["artifacts"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ...) -> None: ...

class GetArtifactsByTypeRequest(_message.Message):
    __slots__ = ["options", "transaction_options", "type_name", "type_version"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactsByTypeResponse(_message.Message):
    __slots__ = ["artifacts", "next_page_token"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    next_page_token: str
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetArtifactsByURIRequest(_message.Message):
    __slots__ = ["transaction_options", "uris"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    URIS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    uris: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, uris: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactsByURIResponse(_message.Message):
    __slots__ = ["artifacts"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ...) -> None: ...

class GetArtifactsRequest(_message.Message):
    __slots__ = ["options", "transaction_options"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetArtifactsResponse(_message.Message):
    __slots__ = ["artifacts", "next_page_token"]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    next_page_token: str
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetChildrenContextsByContextRequest(_message.Message):
    __slots__ = ["context_id", "transaction_options"]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    context_id: int
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, context_id: _Optional[int] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetChildrenContextsByContextResponse(_message.Message):
    __slots__ = ["contexts"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ...) -> None: ...

class GetContextByTypeAndNameRequest(_message.Message):
    __slots__ = ["context_name", "transaction_options", "type_name", "type_version"]
    CONTEXT_NAME_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    context_name: str
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., context_name: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextByTypeAndNameResponse(_message.Message):
    __slots__ = ["context"]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    context: _metadata_store_pb2.Context
    def __init__(self, context: _Optional[_Union[_metadata_store_pb2.Context, _Mapping]] = ...) -> None: ...

class GetContextTypeRequest(_message.Message):
    __slots__ = ["transaction_options", "type_name", "type_version"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextTypeResponse(_message.Message):
    __slots__ = ["context_type"]
    CONTEXT_TYPE_FIELD_NUMBER: _ClassVar[int]
    context_type: _metadata_store_pb2.ContextType
    def __init__(self, context_type: _Optional[_Union[_metadata_store_pb2.ContextType, _Mapping]] = ...) -> None: ...

class GetContextTypesByExternalIdsRequest(_message.Message):
    __slots__ = ["external_ids", "transaction_options"]
    EXTERNAL_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    external_ids: _containers.RepeatedScalarFieldContainer[str]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, external_ids: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextTypesByExternalIdsResponse(_message.Message):
    __slots__ = ["context_types"]
    CONTEXT_TYPES_FIELD_NUMBER: _ClassVar[int]
    context_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ContextType]
    def __init__(self, context_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ContextType, _Mapping]]] = ...) -> None: ...

class GetContextTypesByIDRequest(_message.Message):
    __slots__ = ["transaction_options", "type_ids"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_IDS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, type_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextTypesByIDResponse(_message.Message):
    __slots__ = ["context_types"]
    CONTEXT_TYPES_FIELD_NUMBER: _ClassVar[int]
    context_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ContextType]
    def __init__(self, context_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ContextType, _Mapping]]] = ...) -> None: ...

class GetContextTypesRequest(_message.Message):
    __slots__ = ["transaction_options"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextTypesResponse(_message.Message):
    __slots__ = ["context_types"]
    CONTEXT_TYPES_FIELD_NUMBER: _ClassVar[int]
    context_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ContextType]
    def __init__(self, context_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ContextType, _Mapping]]] = ...) -> None: ...

class GetContextsByArtifactRequest(_message.Message):
    __slots__ = ["artifact_id", "transaction_options"]
    ARTIFACT_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    artifact_id: int
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, artifact_id: _Optional[int] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextsByArtifactResponse(_message.Message):
    __slots__ = ["contexts"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ...) -> None: ...

class GetContextsByExecutionRequest(_message.Message):
    __slots__ = ["execution_id", "transaction_options"]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    execution_id: int
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, execution_id: _Optional[int] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextsByExecutionResponse(_message.Message):
    __slots__ = ["contexts"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ...) -> None: ...

class GetContextsByExternalIdsRequest(_message.Message):
    __slots__ = ["external_ids", "transaction_options"]
    EXTERNAL_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    external_ids: _containers.RepeatedScalarFieldContainer[str]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, external_ids: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextsByExternalIdsResponse(_message.Message):
    __slots__ = ["contexts"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ...) -> None: ...

class GetContextsByIDRequest(_message.Message):
    __slots__ = ["context_ids", "transaction_options"]
    CONTEXT_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    context_ids: _containers.RepeatedScalarFieldContainer[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, context_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextsByIDResponse(_message.Message):
    __slots__ = ["contexts"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ...) -> None: ...

class GetContextsByTypeRequest(_message.Message):
    __slots__ = ["options", "transaction_options", "type_name", "type_version"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., type_version: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextsByTypeResponse(_message.Message):
    __slots__ = ["contexts", "next_page_token"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    next_page_token: str
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetContextsRequest(_message.Message):
    __slots__ = ["options", "transaction_options"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetContextsResponse(_message.Message):
    __slots__ = ["contexts", "next_page_token"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    next_page_token: str
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetEventsByArtifactIDsRequest(_message.Message):
    __slots__ = ["artifact_ids", "transaction_options"]
    ARTIFACT_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    artifact_ids: _containers.RepeatedScalarFieldContainer[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, artifact_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetEventsByArtifactIDsResponse(_message.Message):
    __slots__ = ["events"]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Event]
    def __init__(self, events: _Optional[_Iterable[_Union[_metadata_store_pb2.Event, _Mapping]]] = ...) -> None: ...

class GetEventsByExecutionIDsRequest(_message.Message):
    __slots__ = ["execution_ids", "transaction_options"]
    EXECUTION_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    execution_ids: _containers.RepeatedScalarFieldContainer[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, execution_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetEventsByExecutionIDsResponse(_message.Message):
    __slots__ = ["events"]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Event]
    def __init__(self, events: _Optional[_Iterable[_Union[_metadata_store_pb2.Event, _Mapping]]] = ...) -> None: ...

class GetExecutionByTypeAndNameRequest(_message.Message):
    __slots__ = ["execution_name", "transaction_options", "type_name", "type_version"]
    EXECUTION_NAME_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    execution_name: str
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., execution_name: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionByTypeAndNameResponse(_message.Message):
    __slots__ = ["execution"]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    execution: _metadata_store_pb2.Execution
    def __init__(self, execution: _Optional[_Union[_metadata_store_pb2.Execution, _Mapping]] = ...) -> None: ...

class GetExecutionTypeRequest(_message.Message):
    __slots__ = ["transaction_options", "type_name", "type_version"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionTypeResponse(_message.Message):
    __slots__ = ["execution_type"]
    EXECUTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    execution_type: _metadata_store_pb2.ExecutionType
    def __init__(self, execution_type: _Optional[_Union[_metadata_store_pb2.ExecutionType, _Mapping]] = ...) -> None: ...

class GetExecutionTypesByExternalIdsRequest(_message.Message):
    __slots__ = ["external_ids", "transaction_options"]
    EXTERNAL_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    external_ids: _containers.RepeatedScalarFieldContainer[str]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, external_ids: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionTypesByExternalIdsResponse(_message.Message):
    __slots__ = ["execution_types"]
    EXECUTION_TYPES_FIELD_NUMBER: _ClassVar[int]
    execution_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ExecutionType]
    def __init__(self, execution_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ExecutionType, _Mapping]]] = ...) -> None: ...

class GetExecutionTypesByIDRequest(_message.Message):
    __slots__ = ["transaction_options", "type_ids"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_IDS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, type_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionTypesByIDResponse(_message.Message):
    __slots__ = ["execution_types"]
    EXECUTION_TYPES_FIELD_NUMBER: _ClassVar[int]
    execution_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ExecutionType]
    def __init__(self, execution_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ExecutionType, _Mapping]]] = ...) -> None: ...

class GetExecutionTypesRequest(_message.Message):
    __slots__ = ["transaction_options"]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionTypesResponse(_message.Message):
    __slots__ = ["execution_types"]
    EXECUTION_TYPES_FIELD_NUMBER: _ClassVar[int]
    execution_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ExecutionType]
    def __init__(self, execution_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ExecutionType, _Mapping]]] = ...) -> None: ...

class GetExecutionsByContextRequest(_message.Message):
    __slots__ = ["context_id", "options", "transaction_options"]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    context_id: int
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, context_id: _Optional[int] = ..., options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionsByContextResponse(_message.Message):
    __slots__ = ["executions", "next_page_token", "transaction_options"]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    next_page_token: str
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionsByExternalIdsRequest(_message.Message):
    __slots__ = ["external_ids", "transaction_options"]
    EXTERNAL_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    external_ids: _containers.RepeatedScalarFieldContainer[str]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, external_ids: _Optional[_Iterable[str]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionsByExternalIdsResponse(_message.Message):
    __slots__ = ["executions"]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ...) -> None: ...

class GetExecutionsByIDRequest(_message.Message):
    __slots__ = ["execution_ids", "transaction_options"]
    EXECUTION_IDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    execution_ids: _containers.RepeatedScalarFieldContainer[int]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, execution_ids: _Optional[_Iterable[int]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionsByIDResponse(_message.Message):
    __slots__ = ["executions"]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ...) -> None: ...

class GetExecutionsByTypeRequest(_message.Message):
    __slots__ = ["options", "transaction_options", "type_name", "type_version"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_VERSION_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    type_name: str
    type_version: str
    def __init__(self, type_name: _Optional[str] = ..., type_version: _Optional[str] = ..., options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionsByTypeResponse(_message.Message):
    __slots__ = ["executions", "next_page_token"]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    next_page_token: str
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetExecutionsRequest(_message.Message):
    __slots__ = ["options", "transaction_options"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.ListOperationOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, options: _Optional[_Union[_metadata_store_pb2.ListOperationOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetExecutionsResponse(_message.Message):
    __slots__ = ["executions", "next_page_token"]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    next_page_token: str
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ..., next_page_token: _Optional[str] = ...) -> None: ...

class GetLineageGraphRequest(_message.Message):
    __slots__ = ["options", "transaction_options"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _metadata_store_pb2.LineageGraphQueryOptions
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, options: _Optional[_Union[_metadata_store_pb2.LineageGraphQueryOptions, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetLineageGraphResponse(_message.Message):
    __slots__ = ["subgraph"]
    SUBGRAPH_FIELD_NUMBER: _ClassVar[int]
    subgraph: _metadata_store_pb2.LineageGraph
    def __init__(self, subgraph: _Optional[_Union[_metadata_store_pb2.LineageGraph, _Mapping]] = ...) -> None: ...

class GetParentContextsByContextRequest(_message.Message):
    __slots__ = ["context_id", "transaction_options"]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    context_id: int
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, context_id: _Optional[int] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class GetParentContextsByContextResponse(_message.Message):
    __slots__ = ["contexts"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ...) -> None: ...

class PutArtifactTypeRequest(_message.Message):
    __slots__ = ["all_fields_match", "artifact_type", "can_add_fields", "can_delete_fields", "can_omit_fields", "transaction_options"]
    ALL_FIELDS_MATCH_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_TYPE_FIELD_NUMBER: _ClassVar[int]
    CAN_ADD_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_DELETE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_OMIT_FIELDS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    all_fields_match: bool
    artifact_type: _metadata_store_pb2.ArtifactType
    can_add_fields: bool
    can_delete_fields: bool
    can_omit_fields: bool
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, artifact_type: _Optional[_Union[_metadata_store_pb2.ArtifactType, _Mapping]] = ..., can_add_fields: bool = ..., can_omit_fields: bool = ..., can_delete_fields: bool = ..., all_fields_match: bool = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutArtifactTypeResponse(_message.Message):
    __slots__ = ["type_id"]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    type_id: int
    def __init__(self, type_id: _Optional[int] = ...) -> None: ...

class PutArtifactsRequest(_message.Message):
    __slots__ = ["artifacts", "options", "transaction_options"]
    class Options(_message.Message):
        __slots__ = ["abort_if_latest_updated_time_changed"]
        ABORT_IF_LATEST_UPDATED_TIME_CHANGED_FIELD_NUMBER: _ClassVar[int]
        abort_if_latest_updated_time_changed: bool
        def __init__(self, abort_if_latest_updated_time_changed: bool = ...) -> None: ...
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    options: PutArtifactsRequest.Options
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ..., options: _Optional[_Union[PutArtifactsRequest.Options, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutArtifactsResponse(_message.Message):
    __slots__ = ["artifact_ids"]
    ARTIFACT_IDS_FIELD_NUMBER: _ClassVar[int]
    artifact_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, artifact_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class PutAttributionsAndAssociationsRequest(_message.Message):
    __slots__ = ["associations", "attributions", "transaction_options"]
    ASSOCIATIONS_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    associations: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Association]
    attributions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Attribution]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, attributions: _Optional[_Iterable[_Union[_metadata_store_pb2.Attribution, _Mapping]]] = ..., associations: _Optional[_Iterable[_Union[_metadata_store_pb2.Association, _Mapping]]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutAttributionsAndAssociationsResponse(_message.Message):
    __slots__: list[str] = []
    def __init__(self) -> None: ...

class PutContextTypeRequest(_message.Message):
    __slots__ = ["all_fields_match", "can_add_fields", "can_delete_fields", "can_omit_fields", "context_type", "transaction_options"]
    ALL_FIELDS_MATCH_FIELD_NUMBER: _ClassVar[int]
    CAN_ADD_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_DELETE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_OMIT_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    all_fields_match: bool
    can_add_fields: bool
    can_delete_fields: bool
    can_omit_fields: bool
    context_type: _metadata_store_pb2.ContextType
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, context_type: _Optional[_Union[_metadata_store_pb2.ContextType, _Mapping]] = ..., can_add_fields: bool = ..., can_omit_fields: bool = ..., can_delete_fields: bool = ..., all_fields_match: bool = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutContextTypeResponse(_message.Message):
    __slots__ = ["type_id"]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    type_id: int
    def __init__(self, type_id: _Optional[int] = ...) -> None: ...

class PutContextsRequest(_message.Message):
    __slots__ = ["contexts", "transaction_options"]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutContextsResponse(_message.Message):
    __slots__ = ["context_ids"]
    CONTEXT_IDS_FIELD_NUMBER: _ClassVar[int]
    context_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, context_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class PutEventsRequest(_message.Message):
    __slots__ = ["events", "transaction_options"]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Event]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, events: _Optional[_Iterable[_Union[_metadata_store_pb2.Event, _Mapping]]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutEventsResponse(_message.Message):
    __slots__: list[str] = []
    def __init__(self) -> None: ...

class PutExecutionRequest(_message.Message):
    __slots__ = ["artifact_event_pairs", "contexts", "execution", "options", "transaction_options"]
    class ArtifactAndEvent(_message.Message):
        __slots__ = ["artifact", "event"]
        ARTIFACT_FIELD_NUMBER: _ClassVar[int]
        EVENT_FIELD_NUMBER: _ClassVar[int]
        artifact: _metadata_store_pb2.Artifact
        event: _metadata_store_pb2.Event
        def __init__(self, artifact: _Optional[_Union[_metadata_store_pb2.Artifact, _Mapping]] = ..., event: _Optional[_Union[_metadata_store_pb2.Event, _Mapping]] = ...) -> None: ...
    class Options(_message.Message):
        __slots__ = ["reuse_artifact_if_already_exist_by_external_id", "reuse_context_if_already_exist"]
        REUSE_ARTIFACT_IF_ALREADY_EXIST_BY_EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
        REUSE_CONTEXT_IF_ALREADY_EXIST_FIELD_NUMBER: _ClassVar[int]
        reuse_artifact_if_already_exist_by_external_id: bool
        reuse_context_if_already_exist: bool
        def __init__(self, reuse_context_if_already_exist: bool = ..., reuse_artifact_if_already_exist_by_external_id: bool = ...) -> None: ...
    ARTIFACT_EVENT_PAIRS_FIELD_NUMBER: _ClassVar[int]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    artifact_event_pairs: _containers.RepeatedCompositeFieldContainer[PutExecutionRequest.ArtifactAndEvent]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    execution: _metadata_store_pb2.Execution
    options: PutExecutionRequest.Options
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, execution: _Optional[_Union[_metadata_store_pb2.Execution, _Mapping]] = ..., artifact_event_pairs: _Optional[_Iterable[_Union[PutExecutionRequest.ArtifactAndEvent, _Mapping]]] = ..., contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ..., options: _Optional[_Union[PutExecutionRequest.Options, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutExecutionResponse(_message.Message):
    __slots__ = ["artifact_ids", "context_ids", "execution_id"]
    ARTIFACT_IDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_IDS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_ID_FIELD_NUMBER: _ClassVar[int]
    artifact_ids: _containers.RepeatedScalarFieldContainer[int]
    context_ids: _containers.RepeatedScalarFieldContainer[int]
    execution_id: int
    def __init__(self, execution_id: _Optional[int] = ..., artifact_ids: _Optional[_Iterable[int]] = ..., context_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class PutExecutionTypeRequest(_message.Message):
    __slots__ = ["all_fields_match", "can_add_fields", "can_delete_fields", "can_omit_fields", "execution_type", "transaction_options"]
    ALL_FIELDS_MATCH_FIELD_NUMBER: _ClassVar[int]
    CAN_ADD_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_DELETE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_OMIT_FIELDS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    all_fields_match: bool
    can_add_fields: bool
    can_delete_fields: bool
    can_omit_fields: bool
    execution_type: _metadata_store_pb2.ExecutionType
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, execution_type: _Optional[_Union[_metadata_store_pb2.ExecutionType, _Mapping]] = ..., can_add_fields: bool = ..., can_omit_fields: bool = ..., can_delete_fields: bool = ..., all_fields_match: bool = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutExecutionTypeResponse(_message.Message):
    __slots__ = ["type_id"]
    TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    type_id: int
    def __init__(self, type_id: _Optional[int] = ...) -> None: ...

class PutExecutionsRequest(_message.Message):
    __slots__ = ["executions", "transaction_options"]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutExecutionsResponse(_message.Message):
    __slots__ = ["execution_ids"]
    EXECUTION_IDS_FIELD_NUMBER: _ClassVar[int]
    execution_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, execution_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class PutLineageSubgraphRequest(_message.Message):
    __slots__ = ["artifacts", "contexts", "event_edges", "executions", "options", "transaction_options"]
    class EventEdge(_message.Message):
        __slots__ = ["artifact_index", "event", "execution_index"]
        ARTIFACT_INDEX_FIELD_NUMBER: _ClassVar[int]
        EVENT_FIELD_NUMBER: _ClassVar[int]
        EXECUTION_INDEX_FIELD_NUMBER: _ClassVar[int]
        artifact_index: int
        event: _metadata_store_pb2.Event
        execution_index: int
        def __init__(self, execution_index: _Optional[int] = ..., artifact_index: _Optional[int] = ..., event: _Optional[_Union[_metadata_store_pb2.Event, _Mapping]] = ...) -> None: ...
    class Options(_message.Message):
        __slots__ = ["reuse_artifact_if_already_exist_by_external_id", "reuse_context_if_already_exist"]
        REUSE_ARTIFACT_IF_ALREADY_EXIST_BY_EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
        REUSE_CONTEXT_IF_ALREADY_EXIST_FIELD_NUMBER: _ClassVar[int]
        reuse_artifact_if_already_exist_by_external_id: bool
        reuse_context_if_already_exist: bool
        def __init__(self, reuse_context_if_already_exist: bool = ..., reuse_artifact_if_already_exist_by_external_id: bool = ...) -> None: ...
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    EVENT_EDGES_FIELD_NUMBER: _ClassVar[int]
    EXECUTIONS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    artifacts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Artifact]
    contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Context]
    event_edges: _containers.RepeatedCompositeFieldContainer[PutLineageSubgraphRequest.EventEdge]
    executions: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.Execution]
    options: PutLineageSubgraphRequest.Options
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, executions: _Optional[_Iterable[_Union[_metadata_store_pb2.Execution, _Mapping]]] = ..., artifacts: _Optional[_Iterable[_Union[_metadata_store_pb2.Artifact, _Mapping]]] = ..., contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.Context, _Mapping]]] = ..., event_edges: _Optional[_Iterable[_Union[PutLineageSubgraphRequest.EventEdge, _Mapping]]] = ..., options: _Optional[_Union[PutLineageSubgraphRequest.Options, _Mapping]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutLineageSubgraphResponse(_message.Message):
    __slots__ = ["artifact_ids", "context_ids", "execution_ids"]
    ARTIFACT_IDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_IDS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_IDS_FIELD_NUMBER: _ClassVar[int]
    artifact_ids: _containers.RepeatedScalarFieldContainer[int]
    context_ids: _containers.RepeatedScalarFieldContainer[int]
    execution_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, execution_ids: _Optional[_Iterable[int]] = ..., artifact_ids: _Optional[_Iterable[int]] = ..., context_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class PutParentContextsRequest(_message.Message):
    __slots__ = ["parent_contexts", "transaction_options"]
    PARENT_CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    parent_contexts: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ParentContext]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, parent_contexts: _Optional[_Iterable[_Union[_metadata_store_pb2.ParentContext, _Mapping]]] = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutParentContextsResponse(_message.Message):
    __slots__: list[str] = []
    def __init__(self) -> None: ...

class PutTypesRequest(_message.Message):
    __slots__ = ["all_fields_match", "artifact_types", "can_add_fields", "can_delete_fields", "can_omit_fields", "context_types", "execution_types", "transaction_options"]
    ALL_FIELDS_MATCH_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_TYPES_FIELD_NUMBER: _ClassVar[int]
    CAN_ADD_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_DELETE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CAN_OMIT_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_TYPES_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TYPES_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    all_fields_match: bool
    artifact_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ArtifactType]
    can_add_fields: bool
    can_delete_fields: bool
    can_omit_fields: bool
    context_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ContextType]
    execution_types: _containers.RepeatedCompositeFieldContainer[_metadata_store_pb2.ExecutionType]
    transaction_options: _metadata_store_pb2.TransactionOptions
    def __init__(self, artifact_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ArtifactType, _Mapping]]] = ..., execution_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ExecutionType, _Mapping]]] = ..., context_types: _Optional[_Iterable[_Union[_metadata_store_pb2.ContextType, _Mapping]]] = ..., can_add_fields: bool = ..., can_omit_fields: bool = ..., can_delete_fields: bool = ..., all_fields_match: bool = ..., transaction_options: _Optional[_Union[_metadata_store_pb2.TransactionOptions, _Mapping]] = ...) -> None: ...

class PutTypesResponse(_message.Message):
    __slots__ = ["artifact_type_ids", "context_type_ids", "execution_type_ids"]
    ARTIFACT_TYPE_IDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_TYPE_IDS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TYPE_IDS_FIELD_NUMBER: _ClassVar[int]
    artifact_type_ids: _containers.RepeatedScalarFieldContainer[int]
    context_type_ids: _containers.RepeatedScalarFieldContainer[int]
    execution_type_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, artifact_type_ids: _Optional[_Iterable[int]] = ..., execution_type_ids: _Optional[_Iterable[int]] = ..., context_type_ids: _Optional[_Iterable[int]] = ...) -> None: ...
