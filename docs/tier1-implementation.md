# Tier 1 Implementation Tracking Document

**Objective**: Active development checklist for Tier 1 - Foundational Data Access & Discovery tools
**Duration**: 4 weeks (Phase 1, Weeks 1-4 from DEVELOPMENT_PLAN.md)
**Target Tools**: 7 tools from roadmap.md Tier 1.1 and 1.2

---

## Foundation (Prerequisites)

### Connection Infrastructure

#### [ ] 1.1 Implement real Snowflake connection logic
- **File**: `src/icebreaker/core/connection.py`
- **Task**: Replace placeholder with actual SnowflakeService integration
- **Dependencies**:
  - Snowflake connector python (`snowflake-connector-python>=4.0.0`)
  - Environment variables loading
- **Acceptance Criteria**:
  - [ ] Connection can be established with valid credentials
  - [ ] Connection context manager properly handles cleanup
  - [ ] Connection errors are properly wrapped in IcebreakerError
  - [ ] Supports all authentication types (private key, password, external browser, OAuth)
- **Tests Required**:
  - [ ] Unit tests with mocked SnowflakeService
  - [ ] Connection failure scenarios
  - [ ] Authentication type detection

#### [ ] 1.2 Add comprehensive unit tests for connection logic
- **File**: `tests/unit/test_connection.py`
- **Coverage**:
  - [ ] Successful connection scenarios
  - [ ] Authentication type detection
  - [ ] Connection error handling
  - [ ] Context manager cleanup
  - [ ] Environment variable loading
- **Mock Strategy**: Use unittest.mock for snowflake.connector

#### [ ] 1.3 Verify .env loading works for standard Snowflake credentials
- **Files**: `.env.example`, `src/icebreaker/core/config.py`
- **Required Variables**:
  - [ ] `SNOWFLAKE_ACCOUNT`
  - [ ] `SNOWFLAKE_USER`
  - [ ] `SNOWFLAKE_PRIVATE_KEY` or `SNOWFLAKE_PASSWORD`
  - [ ] Optional: `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`
- **Validation**:
  - [ ] Environment variables loaded correctly
  - [ ] Missing required variables raise appropriate errors
  - [ ] Default values applied correctly

### Safety & Query Execution Framework

#### [ ] 1.4 Implement SafeQueryExecutor
- **File**: `src/icebreaker/core/query.py`
- **Features**:
  - [ ] Automatic LIMIT enforcement for SELECT queries
  - [ ] Query timeout enforcement
  - [ ] Result size validation against `max_query_results`
  - [ ] Safety validation integration
- **Methods**:
  - [ ] `execute_read_query(sql: str, auto_limit: int = None) -> dict`
  - [ ] `validate_query_safety(sql: str) -> ValidationResult`

#### [ ] 1.5 Implement QueryValidator
- **File**: `src/icebreaker/core/query.py`
- **Features**:
  - [ ] SQL statement type validation using sqlglot
  - [ ] Pattern-based dangerous operation detection
  - [ ] Integration with permission system
- **Methods**:
  - [ ] `validate_read_query(sql: str, user_role: str) -> ValidationResult`
  - [ ] `check_statement_permissions(sql: str, role: str) -> bool`

#### [ ] 1.6 Implement ResultFormatter
- **File**: `src/icebreaker/core/query.py`
- **Features**:
  - [ ] Consistent JSON response format
  - [ ] Column metadata inclusion
  - [ ] Row count and execution metadata
- **Methods**:
  - [ ] `format_query_results(cursor, query: str, execution_time: float) -> dict`

---

## Tool Implementation

### Tool: list_databases

#### [ ] 2.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `ListDatabasesInput`
```python
class ListDatabasesInput(BaseModel):
    pattern: Optional[str] = Field(None, description="Filter pattern for database names (ILIKE)")
    limit: Optional[int] = Field(100, description="Maximum number of databases to return")
```

#### [ ] 2.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `DatabaseInfo`
```python
class DatabaseInfo(BaseModel):
    name: str = Field(..., description="Database name")
    owner: str = Field(..., description="Database owner")
    created_on: datetime = Field(..., description="Creation timestamp")
    last_altered: datetime = Field(..., description="Last modification timestamp")
    comment: Optional[str] = Field(None, description="Database comment")
```

#### [ ] 2.3 Implement tool logic
- **File**: `src/icebreaker/tools/catalog.py`
- **Function**: `list_databases(input: ListDatabasesInput) -> List[DatabaseInfo]`
- **SQL**: `SHOW DATABASES [LIKE '<pattern>']`
- **Features**:
  - [ ] Pattern matching support
  - [ ] Limit enforcement
  - [ ] Permission validation
  - [ ] Safety checks
  - [ ] Error handling

#### [ ] 2.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`
- **Task**: Add `@server.tool()` decorator and integrate with permission system
- **Integration**:
  - [ ] Permission wrapper using PermissionManager
  - [ ] Input validation
  - [ ] Error handling
  - [ ] Audit logging

#### [ ] 2.5 Add unit tests
- **File**: `tests/unit/test_tools/test_catalog.py`
- **Test Cases**:
  - [ ] Successful database listing
  - [ ] Pattern filtering
  - [ ] Limit enforcement
  - [ ] Permission denied scenarios
  - [ ] Error handling

### Tool: list_schemas

#### [ ] 3.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `ListSchemasInput`
```python
class ListSchemasInput(BaseModel):
    database: str = Field(..., description="Database name")
    pattern: Optional[str] = Field(None, description="Filter pattern for schema names")
    limit: Optional[int] = Field(100, description="Maximum number of schemas to return")
```

#### [ ] 3.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `SchemaInfo`
```python
class SchemaInfo(BaseModel):
    name: str = Field(..., description="Schema name")
    database_name: str = Field(..., description="Database name")
    owner: str = Field(..., description="Schema owner")
    created_on: datetime = Field(..., description="Creation timestamp")
    last_altered: datetime = Field(..., description="Last modification timestamp")
    comment: Optional[str] = Field(None, description="Schema comment")
```

#### [ ] 3.3 Implement tool logic
- **File**: `src/icebreaker/tools/catalog.py`
- **Function**: `list_schemas(input: ListSchemasInput) -> List[SchemaInfo]`
- **SQL**: `SHOW SCHEMAS IN DATABASE <database> [LIKE '<pattern>']`
- **Features**:
  - [ ] Database existence validation
  - [ ] Pattern matching support
  - [ ] Limit enforcement
  - [ ] Permission validation

#### [ ] 3.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`
- **Integration**: Same pattern as list_databases

#### [ ] 3.5 Add unit tests
- **File**: `tests/unit/test_tools/test_catalog.py`
- **Test Cases**:
  - [ ] Successful schema listing
  - [ ] Database not found error
  - [ ] Pattern filtering
  - [ ] Permission validation

### Tool: list_tables

#### [ ] 4.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `ListTablesInput`
```python
class ListTablesInput(BaseModel):
    database: str = Field(..., description="Database name")
    schema: str = Field(..., description="Schema name")
    pattern: Optional[str] = Field(None, description="Filter pattern for table names")
    include_views: bool = Field(True, description="Include views in results")
    limit: Optional[int] = Field(100, description="Maximum number of tables to return")
```

#### [ ] 4.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `TableInfo`
```python
class TableInfo(BaseModel):
    name: str = Field(..., description="Table name")
    schema_name: str = Field(..., description="Schema name")
    database_name: str = Field(..., description="Database name")
    kind: str = Field(..., description="Object kind: TABLE or VIEW")
    owner: str = Field(..., description="Table owner")
    created_on: datetime = Field(..., description="Creation timestamp")
    last_altered: datetime = Field(..., description="Last modification timestamp")
    comment: Optional[str] = Field(None, description="Table comment")
    row_count: Optional[int] = Field(None, description="Estimated row count")
    bytes: Optional[int] = Field(None, description="Table size in bytes")
```

#### [ ] 4.3 Implement tool logic
- **File**: `src/icebreaker/tools/catalog.py`
- **Function**: `list_tables(input: ListTablesInput) -> List[TableInfo]`
- **SQL**: `SHOW TABLES IN SCHEMA <database>.<schema> [LIKE '<pattern>']`
- **Features**:
  - [ ] Schema existence validation
  - [ ] Table/View filtering
  - [ ] Enhanced metadata from INFORMATION_SCHEMA
  - [ ] Row count and size information

#### [ ] 4.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`

#### [ ] 4.5 Add unit tests
- **File**: `tests/unit/test_tools/test_catalog.py`

### Tool: describe_table

#### [ ] 5.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `DescribeTableInput`
```python
class DescribeTableInput(BaseModel):
    database: str = Field(..., description="Database name")
    schema: str = Field(..., description="Schema name")
    table: str = Field(..., description="Table name")
```

#### [ ] 5.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `TableDescription`, `ColumnInfo`
```python
class ColumnInfo(BaseModel):
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Snowflake data type")
    is_nullable: bool = Field(..., description="Whether column allows NULL values")
    default_value: Optional[str] = Field(None, description="Default value expression")
    comment: Optional[str] = Field(None, description="Column comment")
    ordinal_position: int = Field(..., description="Column position")

class TableDescription(BaseModel):
    name: str = Field(..., description="Table name")
    schema_name: str = Field(..., description="Schema name")
    database_name: str = Field(..., description="Database name")
    owner: str = Field(..., description="Table owner")
    created_on: datetime = Field(..., description="Creation timestamp")
    last_altered: datetime = Field(..., description="Last modification timestamp")
    comment: Optional[str] = Field(None, description="Table comment")
    columns: List[ColumnInfo] = Field(..., description="Column definitions")
    row_count: Optional[int] = Field(None, description="Row count")
    bytes: Optional[int] = Field(None, description="Table size in bytes")
```

#### [ ] 5.3 Implement tool logic
- **File**: `src/icebreaker/tools/catalog.py`
- **Function**: `describe_table(input: DescribeTableInput) -> TableDescription`
- **SQL**: `DESCRIBE TABLE <database>.<schema>.<table>`
- **Features**:
  - [ ] Table existence validation
  - [ ] Comprehensive column information
  - [ ] Table statistics integration
  - [ ] Enhanced metadata from INFORMATION_SCHEMA.COLUMNS

#### [ ] 5.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`

#### [ ] 5.5 Add unit tests
- **File**: `tests/unit/test_tools/test_catalog.py`

### Tool: get_object_ddl

#### [ ] 6.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `GetObjectDDLInput`
```python
class GetObjectDDLInput(BaseModel):
    object_type: str = Field(..., description="Object type: TABLE, VIEW, FUNCTION, PROCEDURE, etc.")
    object_name: str = Field(..., description="Fully qualified object name")
    database: Optional[str] = Field(None, description="Database name (if not in object_name)")
    schema: Optional[str] = Field(None, description="Schema name (if not in object_name)")
```

#### [ ] 6.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `ObjectDDL`
```python
class ObjectDDL(BaseModel):
    object_type: str = Field(..., description="Object type")
    object_name: str = Field(..., description="Object name")
    ddl: str = Field(..., description="DDL statement")
    created_on: Optional[datetime] = Field(None, description="Creation timestamp")
    last_altered: Optional[datetime] = Field(None, description="Last modification timestamp")
```

#### [ ] 6.3 Implement tool logic
- **File**: `src/icebreaker/tools/catalog.py`
- **Function**: `get_object_ddl(input: GetObjectDDLInput) -> ObjectDDL`
- **SQL**: `SELECT GET_DDL('<object_type>', '<fully_qualified_name>')`
- **Features**:
  - [ ] Object name resolution and validation
  - [ ] DDL formatting and cleaning
  - [ ] Support for all major object types
  - [ ] Permission validation

#### [ ] 6.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`

#### [ ] 6.5 Add unit tests
- **File**: `tests/unit/test_tools/test_catalog.py`

### Tool: search_objects

#### [ ] 7.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `SearchObjectsInput`
```python
class SearchObjectsInput(BaseModel):
    search_pattern: str = Field(..., description="Search pattern (ILIKE)")
    object_types: List[str] = Field(
        default=["TABLE", "VIEW"],
        description="Object types to search: TABLE, VIEW, FUNCTION, PROCEDURE, etc."
    )
    database: Optional[str] = Field(None, description="Limit search to specific database")
    schema: Optional[str] = Field(None, description="Limit search to specific schema")
    limit: Optional[int] = Field(100, description="Maximum number of results")
```

#### [ ] 7.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/catalog.py`
- **Model**: `ObjectInfo`
```python
class ObjectInfo(BaseModel):
    name: str = Field(..., description="Object name")
    object_type: str = Field(..., description="Object type")
    schema_name: str = Field(..., description="Schema name")
    database_name: str = Field(..., description="Database name")
    owner: str = Field(..., description="Object owner")
    created_on: datetime = Field(..., description="Creation timestamp")
    last_altered: datetime = Field(..., description="Last modification timestamp")
    comment: Optional[str] = Field(None, description="Object comment")
```

#### [ ] 7.3 Implement tool logic
- **File**: `src/icebreaker/tools/catalog.py`
- **Function**: `search_objects(input: SearchObjectsInput) -> List[ObjectInfo]`
- **SQL**: Query `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.VIEWS`, etc.
- **Features**:
  - [ ] Cross-database search capability
  - [ ] Pattern matching with ILIKE
  - [ ] Multiple object type support
  - [ ] Search result ranking and relevance

#### [ ] 7.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`

#### [ ] 7.5 Add unit tests
- **File**: `tests/unit/test_tools/test_catalog.py`

### Tool: execute_read_query

#### [ ] 8.1 Define Pydantic model for tool input
- **File**: `src/icebreaker/models/query.py`
- **Model**: `ExecuteReadQueryInput`
```python
class ExecuteReadQueryInput(BaseModel):
    sql: str = Field(..., description="SQL SELECT statement to execute")
    limit: Optional[int] = Field(
        None,
        description="Override default query limit (must be <= max_query_results)"
    )
    timeout_seconds: Optional[int] = Field(
        None,
        description="Query timeout in seconds (overrides default)"
    )
```

#### [ ] 8.2 Define Pydantic model for tool output
- **File**: `src/icebreaker/models/query.py`
- **Model**: `QueryResult`
```python
class QueryResult(BaseModel):
    sql: str = Field(..., description="SQL that was executed")
    rows: List[Dict[str, Any]] = Field(..., description="Query result rows")
    columns: List[str] = Field(..., description="Column names")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_seconds: float = Field(..., description="Query execution time")
    bytes_scanned: Optional[int] = Field(None, description="Bytes scanned by query")
    rows_produced: Optional[int] = Field(None, description="Total rows produced")
```

#### [ ] 8.3 Implement tool logic
- **File**: `src/icebreaker/tools/query.py`
- **Function**: `execute_read_query(input: ExecuteReadQueryInput) -> QueryResult`
- **Features**:
  - [ ] SQL statement validation (SELECT only)
  - [ ] Automatic LIMIT enforcement
  - [ ] Query timeout enforcement
  - [ ] Permission validation
  - [ ] Result size validation
  - [ ] Query metadata collection

#### [ ] 8.4 Register tool with MCP server
- **File**: `src/icebreaker/server.py`

#### [ ] 8.5 Add unit tests
- **File**: `tests/unit/test_tools/test_query.py`
- **Test Cases**:
  - [ ] Successful SELECT execution
  - [ ] Automatic LIMIT addition
  - [ ] Non-SELECT statement rejection
  - [ ] Timeout handling
  - [ ] Permission validation
  - [ ] Large result set handling

---

## Tier 1 Verification

### Integration Testing

#### [ ] 9.1 Create integration test suite
- **File**: `tests/integration/test_tier1_integration.py`
- **Features**:
  - [ ] End-to-end workflow testing
  - [ ] Cross-tool functionality
  - [ ] Permission system integration
  - [ ] Configuration validation
- **Environment**: Requires test Snowflake account with sample data

#### [ ] 9.2 Performance validation
- **Requirements**:
  - [ ] Metadata queries < 2 seconds response time
  - [ ] Simple SELECT queries < 5 seconds response time
  - [ ] Concurrent request handling
  - [ ] Memory usage validation

#### [ ] 9.3 Security validation
- **Requirements**:
  - [ ] SQL injection prevention
  - [ ] Permission enforcement
  - [ ] Query result size limits
  - [ ] Dangerous operation blocking

### Manual End-to-End Testing

#### [ ] 10.1 Set up test environment
- **Prerequisites**:
  - [ ] Test Snowflake account with appropriate privileges
  - [ ] Sample data and objects created
  - [ ] MCP client (Claude Desktop) configured
  - [ ] Environment variables configured

#### [ ] 10.2 Test all Tier 1 tools with real MCP client
- **Test Matrix**:
  - [ ] `list_databases()` - Basic functionality
  - [ ] `list_databases(pattern="TEST%")` - Pattern matching
  - [ ] `list_schemas()` - Database and schema combinations
  - [ ] `list_tables()` - Table and view listing
  - [ ] `describe_table()` - Comprehensive table description
  - [ ] `get_object_ddl()` - DDL extraction for various object types
  - [ ] `search_objects()` - Pattern-based search across object types
  - [ ] `execute_read_query()` - SELECT query execution with limits

#### [ ] 10.3 Validate error handling and user experience
- **Scenarios**:
  - [ ] Invalid SQL statements
  - [ ] Permission denied scenarios
  - [ ] Object not found errors
  - [ ] Timeout scenarios
  - [ ] Large result set handling
  - [ ] Malformed input validation

#### [ ] 10.4 Document test results
- **Deliverable**: `docs/tier1-test-results.md`
- **Contents**:
  - [ ] Test execution summary
  - [ ] Performance metrics
  - [ ] Issue identification and resolution
  - [ ] User experience validation
  - [ ] Production readiness assessment

---

## Success Criteria

### Functional Requirements
- [ ] All 7 Tier 1 tools implemented and tested
- [ ] Configuration system integration complete
- [ ] Permission system properly enforced
- [ ] Safety checks prevent unauthorized operations
- [ ] Error handling comprehensive and user-friendly

### Non-Functional Requirements
- [ ] Response time < 2s for metadata operations
- [ ] Response time < 5s for query operations
- [ ] Zero security vulnerabilities
- [ ] 100% test coverage for new code
- [ ] Documentation complete and accurate

### Integration Requirements
- [ ] Seamless integration with existing configuration system
- [ ] Compatible with FastMCP framework
- [ ] Works with Claude Desktop MCP client
- [ ] Proper audit logging for all operations

---

## Progress Tracking

### Completed Tasks
- [ ] Configuration system integration ✅
- [ ] Permission system implementation ✅
- [ ] Dynamic tool registration framework ✅

### Current Sprint
- [ ] Foundation implementation (connection, safety, query execution)
- [ ] Tool implementation (catalog and query tools)
- [ ] Unit test development

### Next Sprint
- [ ] Integration testing
- [ ] Performance validation
- [ ] End-to-end testing with real MCP client

---

## Notes & Considerations

### Atomic Commit Strategy
Each tool implementation should follow this commit pattern:
1. `feat: implement {tool_name} Pydantic models`
2. `feat: implement {tool_name} business logic`
3. `feat: register {tool_name} with MCP server`
4. `test: add unit tests for {tool_name}`

### Risk Mitigation
- **Risk**: Connection issues with Snowflake
- **Mitigation**: Comprehensive error handling and retry logic
- **Risk**: SQL injection vulnerabilities
- **Mitigation**: Parameter validation and sqlglot parsing
- **Risk**: Performance issues with large queries
- **Mitigation**: Automatic limits and timeout enforcement

### Dependencies
- FastMCP framework compatibility
- Snowflake connector python version compatibility
- Test environment setup and maintenance
- Documentation maintenance

---

*Last Updated: $(date)*
*Next Review: After each tool implementation completion*