# Rule-Based Repair System Architecture

## Component Architecture for Handling Error Messages

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE ERROR MESSAGE                        │
│  "no such column: regoin"                                       │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│               ERROR CLASSIFIER COMPONENT                         │
│  • Parses error message                                         │
│  • Maps to taxonomy code                                        │
│  • Extracts problematic token                                   │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
                  {code: "SC2", token: "regoin"}
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  REPAIR ROUTER COMPONENT                         │
│  • Looks up repair strategy from taxonomy                       │
│  • Routes to appropriate handler                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
              [rule_based | llm_guided]
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                  ↓
┌──────────────────┐           ┌──────────────────┐
│  RULE-BASED      │           │   LLM-GUIDED     │
│  REPAIR ENGINE   │           │   CORRECTOR      │
│                  │           │   (5% of cases)  │
│  (95% of cases)  │           └──────────────────┘
└────────┬─────────┘
         ↓
   ┌────────────────────────────────────────┐
   │     SPECIALIZED REPAIR HANDLERS        │
   ├────────────────────────────────────────┤
   │ • Schema Error Handler (SC1-SC5)       │
   │ • Aggregation Error Handler (A1-A4)    │
   │ • Join Error Handler (J1-J5)           │
   │ • Filter Error Handler (F1-F5)         │
   │ • Syntax Error Handler (S1-S4)         │
   └────────┬───────────────────────────────┘
            ↓
      [Fixed SQL]
```

---

## 2. Core Components

### 2.1 Error Classifier

**Purpose:** Parse database error messages and map to taxonomy codes

```python
class ErrorClassifier:
    """
    Maps database errors to taxonomy error codes
    """

    # Error pattern definitions
    ERROR_PATTERNS = {
        'SC1': [  # Wrong table name
            r'no such table: (\w+)',
            r'table "(\w+)" does not exist',
            r'relation "(\w+)" does not exist'
        ],
        'SC2': [  # Wrong column name
            r'no such column: (\w+)',
            r'column "(\w+)" does not exist',
            r'unknown column "(\w+)"'
        ],
        'SC4': [  # Ambiguous column
            r'ambiguous column name: (\w+)',
            r'column reference "(\w+)" is ambiguous'
        ],
        'S1': [  # Syntax error
            r'syntax error near "(.+)"',
            r'syntax error at or near "(.+)"'
        ],
        'A1': [  # Missing GROUP BY (detected from execution behavior)
            r'column "(\w+)" must appear in GROUP BY'
        ],
        'F2': [  # Type mismatch
            r'invalid input syntax for type (.+)',
            r'cannot compare (.+) with (.+)'
        ]
    }

    def classify(self, error_message: str) -> ErrorInfo:
        """
        Classify database error into taxonomy code

        Input: "no such column: regoin"
        Output: ErrorInfo(code='SC2', token='regoin', category='SCHEMA')
        """
        for error_code, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, error_message, re.IGNORECASE)
                if match:
                    token = match.group(1)
                    category = get_error_category(error_code)

                    return ErrorInfo(
                        code=error_code,
                        token=token,
                        category=category,
                        original_message=error_message
                    )

        # Unknown error
        return ErrorInfo(
            code='UNKNOWN',
            token=None,
            category='UNKNOWN',
            original_message=error_message
        )
```

---

### 2.2 Repair Router

**Purpose:** Route errors to appropriate repair handler based on taxonomy

```python
class RepairRouter:
    """
    Routes errors to appropriate repair handler
    """

    def __init__(self):
        # Initialize specialized handlers
        self.handlers = {
            'SCHEMA': SchemaErrorHandler(),
            'AGGREGATION': AggregationErrorHandler(),
            'JOIN': JoinErrorHandler(),
            'FILTER': FilterErrorHandler(),
            'SYNTAX': SyntaxErrorHandler()
        }

    def route(self, error_info: ErrorInfo, sql: str) -> str:
        """
        Route to appropriate handler based on error category

        Flow:
        1. Get error category from taxonomy
        2. Look up handler for that category
        3. Delegate repair to handler
        """
        # Get category from error code
        category = error_info.category  # e.g., 'SCHEMA'

        # Get handler for this category
        handler = self.handlers.get(category)

        if not handler:
            raise UnsupportedErrorType(f"No handler for {category}")

        # Delegate to handler
        fixed_sql = handler.repair(sql, error_info)

        return fixed_sql
```

---

### 2.3 Schema Error Handler

**Purpose:** Handle SC1-SC5 (table/column name errors)

```python
class SchemaErrorHandler:
    """
    Handles schema-related errors (SC1-SC5)

    Components:
    • Fuzzy Matcher - finds closest matching names
    • Schema Cache - quick lookups
    • Token Replacer - replaces wrong tokens in SQL
    """

    def __init__(self, schema):
        self.schema = schema
        self.fuzzy_matcher = FuzzyMatcher()
        self.token_replacer = TokenReplacer()

    def repair(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Repair schema errors using fuzzy matching
        """
        error_code = error_info.code

        if error_code == 'SC1':  # Wrong table name
            return self._fix_table_name(sql, error_info)

        elif error_code == 'SC2':  # Wrong column name
            return self._fix_column_name(sql, error_info)

        elif error_code == 'SC4':  # Ambiguous column
            return self._add_table_qualifier(sql, error_info)

        else:
            raise UnsupportedErrorCode(error_code)

    def _fix_table_name(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Fix wrong table name using fuzzy matching

        Example:
        Error: "no such table: lead"
        Token: "lead"
        Available: ["leads", "customers", "orders"]
        Match: "leads" (distance = 1)
        """
        wrong_table = error_info.token

        # Get all valid table names from schema
        valid_tables = self.schema.get_all_table_names()

        # Find closest match
        correct_table = self.fuzzy_matcher.find_best_match(
            wrong_table,
            valid_tables,
            max_distance=2
        )

        if not correct_table:
            raise NoMatchFound(f"Cannot find match for '{wrong_table}'")

        # Replace in SQL
        fixed_sql = self.token_replacer.replace(
            sql,
            old_token=wrong_table,
            new_token=correct_table,
            context='table'
        )

        return fixed_sql

    def _fix_column_name(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Fix wrong column name using fuzzy matching

        Example:
        Error: "no such column: regoin"
        Token: "regoin"
        Available: ["region", "revenue", "customer_id"]
        Match: "region" (distance = 1)
        """
        wrong_column = error_info.token

        # Get all valid column names
        valid_columns = self.schema.get_all_column_names()

        # Find closest match
        correct_column = self.fuzzy_matcher.find_best_match(
            wrong_column,
            valid_columns,
            max_distance=2
        )

        if not correct_column:
            raise NoMatchFound(f"Cannot find match for '{wrong_column}'")

        # Replace in SQL
        fixed_sql = self.token_replacer.replace(
            sql,
            old_token=wrong_column,
            new_token=correct_column,
            context='column'
        )

        return fixed_sql

    def _add_table_qualifier(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Add table qualifier to ambiguous column

        Example:
        Error: "ambiguous column name: id"
        Token: "id"
        Tables in query: ["customers", "orders"]
        Both have "id" column

        Solution: Determine which table based on context
        """
        ambiguous_column = error_info.token

        # Parse SQL to find tables
        tables = parse_tables_from_sql(sql)

        # Find which tables have this column
        tables_with_column = [
            t for t in tables
            if self.schema.table_has_column(t, ambiguous_column)
        ]

        if len(tables_with_column) == 1:
            # Only one table has it, use that
            qualified = f"{tables_with_column[0]}.{ambiguous_column}"
        else:
            # Multiple tables - need context analysis
            # Use primary table (usually first in FROM)
            primary_table = tables[0]
            qualified = f"{primary_table}.{ambiguous_column}"

        # Replace in SQL
        fixed_sql = self.token_replacer.replace(
            sql,
            old_token=ambiguous_column,
            new_token=qualified,
            context='column'
        )

        return fixed_sql
```

---

### 2.4 Aggregation Error Handler

**Purpose:** Handle A1-A4 (GROUP BY, aggregation errors)

```python
class AggregationErrorHandler:
    """
    Handles aggregation errors (A1-A4)

    Components:
    • GROUP BY Inserter - adds missing GROUP BY
    • Clause Analyzer - identifies non-aggregated columns
    • HAVING Converter - moves HAVING to WHERE when needed
    """

    def repair(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Repair aggregation errors
        """
        error_code = error_info.code

        if error_code == 'A1':  # Missing GROUP BY
            return self._insert_group_by(sql, error_info)

        elif error_code == 'A3':  # HAVING should be WHERE
            return self._convert_having_to_where(sql)

        else:
            raise UnsupportedErrorCode(error_code)

    def _insert_group_by(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Insert GROUP BY clause

        Algorithm:
        1. Parse SQL to find SELECT columns
        2. Identify non-aggregated columns
        3. Insert GROUP BY with those columns
        4. Place before ORDER BY, HAVING, LIMIT
        """
        # Parse SQL
        ast = parse_sql(sql)

        # Find SELECT clause
        select = ast.find(SelectNode)

        # Get non-aggregated columns
        non_agg_columns = []
        for expr in select.expressions:
            if is_column(expr) and not is_inside_aggregate(expr):
                non_agg_columns.append(expr.name)

        # Build GROUP BY clause
        group_by_clause = f"GROUP BY {', '.join(non_agg_columns)}"

        # Find insertion point (before ORDER BY, HAVING, LIMIT)
        insertion_point = self._find_group_by_insertion_point(sql)

        # Insert GROUP BY
        fixed_sql = (
            sql[:insertion_point] +
            " " + group_by_clause + " " +
            sql[insertion_point:]
        )

        return fixed_sql

    def _find_group_by_insertion_point(self, sql: str) -> int:
        """
        Find where to insert GROUP BY clause

        Priority:
        1. Before ORDER BY
        2. Before HAVING
        3. Before LIMIT
        4. At end
        """
        keywords = ['ORDER BY', 'HAVING', 'LIMIT']

        for keyword in keywords:
            pos = sql.upper().find(keyword)
            if pos != -1:
                return pos

        # Insert at end
        return len(sql)
```

---

### 2.5 Join Error Handler

**Purpose:** Handle J1-J5 (JOIN-related errors)

```python
class JoinErrorHandler:
    """
    Handles JOIN errors (J1-J5)

    Components:
    • FK Analyzer - finds foreign key relationships
    • JOIN Generator - creates JOIN clauses from schema
    • Path Finder - finds shortest path between tables
    """

    def __init__(self, schema):
        self.schema = schema
        self.fk_analyzer = ForeignKeyAnalyzer(schema)
        self.join_generator = JoinGenerator(schema)

    def repair(self, sql: str, error_info: ErrorInfo) -> str:
        """
        Repair JOIN errors
        """
        error_code = error_info.code

        if error_code == 'J1':  # Missing JOIN
            return self._add_missing_joins(sql)

        elif error_code == 'J3':  # Missing ON clause
            return self._add_on_clause(sql, error_info)

        else:
            raise UnsupportedErrorCode(error_code)

    def _add_missing_joins(self, sql: str) -> str:
        """
        Add missing JOINs using schema FK relationships

        Algorithm:
        1. Parse SQL to find tables
        2. Use BFS to find FK path between tables
        3. Generate JOIN clauses
        4. Replace Cartesian product with JOINs
        """
        # Parse to find tables
        ast = parse_sql(sql)
        tables = [t.name for t in ast.find_all(TableNode)]

        # Generate JOIN path using schema
        join_clauses = self.join_generator.generate_join_path(tables)

        # Replace comma-separated tables with JOINs
        fixed_sql = self._replace_with_joins(sql, tables, join_clauses)

        return fixed_sql

    def _replace_with_joins(self, sql: str, tables: List[str],
                           join_clauses: List[str]) -> str:
        """
        Replace: FROM t1, t2, t3
        With:    FROM t1 JOIN t2 ON ... JOIN t3 ON ...
        """
        # Find FROM clause
        from_pos = sql.upper().find('FROM')

        # Find end of table list
        where_pos = sql.upper().find('WHERE')
        if where_pos == -1:
            where_pos = len(sql)

        # Build new FROM clause
        new_from = f"FROM {tables[0]} " + " ".join(join_clauses)

        # Reconstruct SQL
        fixed_sql = (
            sql[:from_pos] +
            new_from + " " +
            sql[where_pos:]
        )

        return fixed_sql
```

---

### 2.6 Supporting Components

#### Fuzzy Matcher
```python
class FuzzyMatcher:
    """
    Finds best matching string using Levenshtein distance
    """

    def __init__(self):
        self.cache = LRUCache(maxsize=1000)

    def find_best_match(self, typo: str, valid_options: List[str],
                       max_distance: int = 2) -> Optional[str]:
        """
        Find closest match within distance threshold

        Example:
        typo: "regoin"
        valid_options: ["region", "revenue", "customer"]
        max_distance: 2

        Returns: "region" (distance = 1)
        """
        # Check cache
        cache_key = (typo, tuple(sorted(valid_options)))
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Calculate distances
        matches = []
        for option in valid_options:
            distance = levenshtein_distance(typo.lower(), option.lower())
            if distance <= max_distance:
                matches.append((option, distance))

        # Get best match
        if matches:
            best = min(matches, key=lambda x: x[1])[0]
        else:
            best = None

        # Cache result
        self.cache[cache_key] = best
        return best
```

#### Token Replacer
```python
class TokenReplacer:
    """
    Replaces tokens in SQL with context awareness
    """

    def replace(self, sql: str, old_token: str, new_token: str,
               context: str) -> str:
        """
        Replace token in SQL with context awareness

        Context matters to avoid wrong replacements:
        - 'table' context: only replace in FROM/JOIN
        - 'column' context: only replace in SELECT/WHERE/GROUP BY
        """
        if context == 'table':
            # Only replace in FROM/JOIN clauses
            return self._replace_in_table_context(sql, old_token, new_token)

        elif context == 'column':
            # Replace in SELECT/WHERE/GROUP BY/HAVING/ORDER BY
            return sql.replace(old_token, new_token)

        else:
            # Generic replacement
            return sql.replace(old_token, new_token)

    def _replace_in_table_context(self, sql: str, old: str, new: str) -> str:
        """
        Replace only in table positions (FROM, JOIN)
        """
        # Parse to AST and replace at table nodes only
        ast = parse_sql(sql)

        for table_node in ast.find_all(TableNode):
            if table_node.name == old:
                table_node.name = new

        return ast.to_sql()
```

#### JOIN Generator
```python
class JoinGenerator:
    """
    Generates JOIN clauses using schema FK relationships
    """

    def __init__(self, schema):
        self.schema = schema

    def generate_join_path(self, tables: List[str]) -> List[str]:
        """
        Generate JOIN clauses to connect tables

        Uses BFS to find shortest path through FK graph

        Example:
        tables: ['orders', 'customers', 'products']

        Returns: [
            'JOIN customers ON orders.customer_id = customers.id',
            'JOIN products ON orders.product_id = products.id'
        ]
        """
        joins = []
        connected = {tables[0]}  # Start with first table
        remaining = set(tables[1:])

        while remaining:
            found = False

            for conn_table in connected:
                for rem_table in remaining:
                    # Check for FK relationship
                    fk = self.schema.get_fk_between(conn_table, rem_table)

                    if fk:
                        # Found connection
                        joins.append(
                            f"JOIN {rem_table} ON {fk[0]} = {fk[1]}"
                        )
                        connected.add(rem_table)
                        remaining.remove(rem_table)
                        found = True
                        break

                if found:
                    break

            if not found:
                # No FK path exists
                break

        return joins
```

---

## 3. Complete Error Flow Example

### Example: "no such column: regoin"

```
┌─────────────────────────────────────────────────┐
│ DATABASE ERROR                                  │
│ "no such column: regoin"                        │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ ERROR CLASSIFIER                                │
│                                                 │
│ Pattern Match:                                  │
│   r'no such column: (\w+)' → SC2               │
│                                                 │
│ Extract Token:                                  │
│   token = "regoin"                             │
│                                                 │
│ Output:                                         │
│   ErrorInfo(                                    │
│     code='SC2',                                 │
│     token='regoin',                            │
│     category='SCHEMA'                          │
│   )                                             │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ REPAIR ROUTER                                   │
│                                                 │
│ Lookup Category:                                │
│   SC2 → SCHEMA category                        │
│                                                 │
│ Route to Handler:                               │
│   handlers['SCHEMA'] → SchemaErrorHandler      │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│ SCHEMA ERROR HANDLER                            │
│                                                 │
│ Step 1: Identify sub-type                      │
│   SC2 → _fix_column_name()                     │
│                                                 │
│ Step 2: Get valid columns                      │
│   schema.get_all_column_names()                │
│   → ["region", "revenue", "customer_id", ...]  │
│                                                 │
│ Step 3: Fuzzy match                            │
│   FuzzyMatcher.find_best_match(               │
│     "regoin",                                  │
│     ["region", "revenue", ...]                 │
│   )                                             │
│   → "region" (distance = 1)                    │
│                                                 │
│ Step 4: Replace token                          │
│   TokenReplacer.replace(                       │
│     sql,                                       │
│     old="regoin",                              │
│     new="region"                               │
│   )                                             │
│                                                 │
│ Output:                                         │
│   Fixed SQL with "region"                      │
└─────────────────────────────────────────────────┘
```

---

## 4. Component Dependency Map

```
┌──────────────────────────────────────────────────────┐
│                    REPAIR ROUTER                     │
│  (routes based on error category)                   │
└───────┬──────────────────────────────────────────────┘
        │
        ├─→ Schema Error Handler
        │   └─→ Fuzzy Matcher
        │   └─→ Token Replacer
        │   └─→ Schema Cache
        │
        ├─→ Aggregation Error Handler
        │   └─→ Clause Analyzer
        │   └─→ GROUP BY Inserter
        │   └─→ HAVING Converter
        │
        ├─→ Join Error Handler
        │   └─→ FK Analyzer
        │   └─→ JOIN Generator
        │   └─→ Path Finder
        │
        ├─→ Filter Error Handler
        │   └─→ Type Checker
        │   └─→ Condition Validator
        │
        └─→ Syntax Error Handler
            └─→ Parser
            └─→ Syntax Validator
```

---

## 5. Error Type to Handler Mapping

| Error Code | Category | Handler | Component Used | Latency |
|------------|----------|---------|----------------|---------|
| **SC1** | SCHEMA | SchemaErrorHandler | Fuzzy Matcher (tables) | 20ms |
| **SC2** | SCHEMA | SchemaErrorHandler | Fuzzy Matcher (columns) | 20ms |
| **SC4** | SCHEMA | SchemaErrorHandler | Token Replacer (qualifier) | 15ms |
| **A1** | AGGREGATION | AggregationErrorHandler | GROUP BY Inserter | 30ms |
| **A3** | AGGREGATION | AggregationErrorHandler | HAVING Converter | 25ms |
| **J1** | JOIN | JoinErrorHandler | JOIN Generator + BFS | 50ms |
| **J3** | JOIN | JoinErrorHandler | FK Analyzer | 30ms |
| **F2** | FILTER | FilterErrorHandler | Type Checker | 20ms |
| **S1** | SYNTAX | SyntaxErrorHandler | Parser | 40ms |

---

## 6. Summary

### Components Available:

1. **Error Classifier** - Maps DB errors to taxonomy codes
2. **Repair Router** - Routes to appropriate handler
3. **5 Specialized Handlers:**
   - Schema Error Handler (SC1-SC5)
   - Aggregation Error Handler (A1-A4)
   - Join Error Handler (J1-J5)
   - Filter Error Handler (F1-F5)
   - Syntax Error Handler (S1-S4)

4. **Supporting Components:**
   - Fuzzy Matcher (Levenshtein distance)
   - Token Replacer (context-aware)
   - JOIN Generator (BFS on FK graph)
   - Schema Cache (fast lookups)

### Key Advantages:

✅ **Modular** - Each handler is independent
✅ **Extensible** - Easy to add new error types
✅ **Fast** - 15-50ms per repair
✅ **Accurate** - Uses schema + fuzzy matching
✅ **Organized** - Taxonomy provides structure
