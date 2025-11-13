# Execution-Based Self-Healing Workflow

## The REAL Problem: Queries That FAIL or Return Empty Results

---

## 1. The Actual Workflow

### 1.1 Problem Statement

**Current Misunderstanding:**
- ❌ Detect errors BEFORE execution using static analysis
- ❌ Fix errors before running query

**Actual Reality:**
- ✅ Generate SQL that looks syntactically correct
- ✅ Execute SQL on database
- ✅ SQL **FAILS** with database error OR returns **no data**
- ✅ **THEN** self-heal based on failure feedback

---

## 2. Execution-Based Self-Healing Architecture

### 2.1 Complete Flow

```
User Query (NL)
      ↓
[Generate SQL via LLM] ──────────→ 2-3s
      ↓
   Generated SQL
      ↓
[Execute on Database] ←─────────── THIS IS THE KEY STEP
      ↓
   ┌──────────┐
   │ Success? │
   └────┬─────┘
        │
   ┌────┴────┐
   NO       YES
   │         │
   ↓         ↓
[FAILURE] [Return Results]
   ↓
   ├─→ Database Error (syntax, constraint violation)
   ├─→ Empty Results (0 rows)
   └─→ Timeout / Performance issue
   ↓
[Analyze Failure]
   ↓
[Self-Healing Repair]
   ↓
[Re-Execute]
   ↓
Success? → YES → Return Results
         → NO → Return Error to User
```

### 2.2 Types of Failures That Trigger Self-Healing

| Failure Type | Example | Trigger |
|--------------|---------|---------|
| **Syntax Error** | `no such column: regoin` | Database error |
| **Constraint Violation** | `no such table: lead` | Database error |
| **Empty Results** | Query runs but 0 rows | Result validation |
| **Logical Error** | Wrong data (detectable) | Result validation |
| **Timeout** | Query too slow | Execution timeout |

---

## 3. Detailed Self-Healing Flow

### 3.1 Pseudo Code

```python
class ExecutionBasedSelfHealing:
    def __init__(self, llm_client, database, schema):
        self.llm = llm_client
        self.db = database
        self.schema = schema
        self.max_retries = 2

    def query(self, user_query: str) -> QueryResult:
        """
        Main workflow: Execute-based self-healing

        Flow:
        1. Generate SQL
        2. Execute on database
        3. If fails → Analyze error → Fix → Retry
        4. If empty → Analyze reason → Fix → Retry
        """
        # Step 1: Generate SQL
        sql = self.generate_sql(user_query)

        # Step 2-5: Execute with self-healing
        for attempt in range(self.max_retries):
            # Execute on database
            result = self.execute_sql(sql)

            if result.success and result.has_data:
                # Success! Return results
                return result

            elif result.error:
                # Database error - parse and fix
                sql = self.heal_from_error(sql, result.error, user_query)

            elif result.empty:
                # No results - analyze why
                sql = self.heal_from_empty(sql, user_query)

            else:
                # Unknown failure
                break

        # Failed after retries
        return ErrorResult("Unable to generate correct SQL")

    def execute_sql(self, sql: str) -> ExecutionResult:
        """
        Execute SQL on database and capture result/error

        Returns:
        - success: True/False
        - error: Database error message (if any)
        - rows: Result rows
        - has_data: Whether results are non-empty
        """
        try:
            cursor = self.db.execute(sql)
            rows = cursor.fetchall()

            return ExecutionResult(
                success=True,
                error=None,
                rows=rows,
                has_data=len(rows) > 0
            )

        except DatabaseError as e:
            # Capture database error
            return ExecutionResult(
                success=False,
                error=str(e),  # "no such column: regoin"
                rows=None,
                has_data=False
            )

    def heal_from_error(self, sql: str, error: str, user_query: str) -> str:
        """
        Fix SQL based on database error message

        Error Types:
        1. "no such table: X" → Schema error (wrong table name)
        2. "no such column: X" → Schema error (wrong column name)
        3. "ambiguous column name: X" → Missing table qualifier
        4. "syntax error near X" → SQL syntax error
        5. "UNIQUE constraint failed" → Logic error
        """
        # Parse error type
        error_type = self.classify_error(error)

        if error_type == 'NO_SUCH_TABLE':
            # Extract wrong table name from error
            wrong_table = extract_token(error, "no such table: ")

            # Find correct table using fuzzy match
            correct_table = fuzzy_match(wrong_table, self.schema.tables)

            # Replace in SQL
            fixed_sql = sql.replace(wrong_table, correct_table)

            return fixed_sql

        elif error_type == 'NO_SUCH_COLUMN':
            # Extract wrong column name
            wrong_column = extract_token(error, "no such column: ")

            # Find correct column
            correct_column = fuzzy_match(wrong_column, self.schema.all_columns)

            # Replace in SQL
            fixed_sql = sql.replace(wrong_column, correct_column)

            return fixed_sql

        elif error_type == 'AMBIGUOUS_COLUMN':
            # Need to add table qualifier
            column = extract_token(error, "ambiguous column name: ")

            # Use LLM to add qualifier (needs context)
            fixed_sql = self.llm_add_qualifier(sql, column, user_query)

            return fixed_sql

        elif error_type == 'SYNTAX_ERROR':
            # Complex - use LLM to fix syntax
            fixed_sql = self.llm_fix_syntax(sql, error, user_query)

            return fixed_sql

        else:
            # Unknown error - use LLM
            fixed_sql = self.llm_generic_fix(sql, error, user_query)

            return fixed_sql

    def heal_from_empty(self, sql: str, user_query: str) -> str:
        """
        Fix SQL that returns no results

        Possible causes:
        1. Wrong filter conditions (too restrictive)
        2. Wrong JOIN conditions (no matches)
        3. Missing data (not a SQL error)
        4. Logic error (wrong table/column)
        """
        # Analyze why empty
        analysis = self.analyze_empty_result(sql, user_query)

        if analysis.reason == 'FILTER_TOO_RESTRICTIVE':
            # Try relaxing filters
            fixed_sql = self.relax_filters(sql, analysis)

        elif analysis.reason == 'WRONG_JOIN':
            # Check JOIN conditions
            fixed_sql = self.fix_join_conditions(sql)

        elif analysis.reason == 'NO_DATA':
            # Data doesn't exist - not a SQL error
            return sql  # Can't fix

        else:
            # Use LLM to diagnose and fix
            fixed_sql = self.llm_fix_empty(sql, user_query)

        return fixed_sql
```

---

## 4. Real Examples

### 4.1 Example 1: Database Error - Wrong Column Name

```
User Query: "Show total sales by region"

┌──────────────────────────────────────────────────┐
│ STEP 1: Generate SQL                             │
└────────────────┬─────────────────────────────────┘
                 ↓
Generated SQL:
SELECT regoin, SUM(sales) as total    ← Typo: "regoin"
FROM orders
GROUP BY regoin

┌──────────────────────────────────────────────────┐
│ STEP 2: Execute on Database                      │
└────────────────┬─────────────────────────────────┘
                 ↓
Database Error:
❌ "no such column: regoin"

┌──────────────────────────────────────────────────┐
│ STEP 3: Analyze Error                            │
└────────────────┬─────────────────────────────────┘
                 ↓
Error Classification:
- Type: NO_SUCH_COLUMN
- Wrong token: "regoin"
- Available columns: ["region", "sales", "product", "date"]

┌──────────────────────────────────────────────────┐
│ STEP 4: Self-Healing Repair                      │
└────────────────┬─────────────────────────────────┘
                 ↓
Fuzzy Match:
"regoin" → "region" (distance = 1, swap i↔o)

Fix:
sql.replace("regoin", "region")

┌──────────────────────────────────────────────────┐
│ STEP 5: Re-Execute                               │
└────────────────┬─────────────────────────────────┘
                 ↓
Fixed SQL:
SELECT region, SUM(sales) as total
FROM orders
GROUP BY region

Execute Result:
✅ Success!
[('North', 125000), ('South', 98000), ('East', 142000)]

Return to User: SUCCESS
```

**Key Point:** Error detected ONLY when database rejected the query.

---

### 4.2 Example 2: Empty Results - Wrong Filter

```
User Query: "Show leads from California"

┌──────────────────────────────────────────────────┐
│ STEP 1: Generate SQL                             │
└────────────────┬─────────────────────────────────┘
                 ↓
Generated SQL:
SELECT * FROM leads
WHERE state = 'California'    ← Should be 'CA' (abbreviation)

┌──────────────────────────────────────────────────┐
│ STEP 2: Execute on Database                      │
└────────────────┬─────────────────────────────────┘
                 ↓
Result:
✅ Query succeeded (no database error)
📊 0 rows returned

┌──────────────────────────────────────────────────┐
│ STEP 3: Analyze Empty Result                     │
└────────────────┬─────────────────────────────────┘
                 ↓
Analysis:
- Query syntax: Valid
- Execution: Successful
- Results: Empty (suspicious for common state)

Check Data:
SELECT DISTINCT state FROM leads
→ ['CA', 'NY', 'TX', 'FL', ...]  ← Uses abbreviations!

┌──────────────────────────────────────────────────┐
│ STEP 4: Self-Healing Repair (LLM)                │
└────────────────┬─────────────────────────────────┘
                 ↓
LLM Prompt:
```
User asked: "Show leads from California"
Generated SQL: SELECT * FROM leads WHERE state = 'California'
Result: 0 rows

Schema info: state column contains: ['CA', 'NY', 'TX', ...]
Diagnosis: State column uses abbreviations, not full names

Fix the SQL to use 'CA' instead of 'California'
```

LLM Response:
SELECT * FROM leads WHERE state = 'CA'

┌──────────────────────────────────────────────────┐
│ STEP 5: Re-Execute                               │
└────────────────┬─────────────────────────────────┘
                 ↓
Fixed SQL:
SELECT * FROM leads WHERE state = 'CA'

Execute Result:
✅ Success!
📊 47 rows returned

Return to User: SUCCESS with 47 leads
```

---

### 4.3 Example 3: Database Error - Missing JOIN

```
User Query: "Show customer names with their orders"

┌──────────────────────────────────────────────────┐
│ STEP 1: Generate SQL                             │
└────────────────┬─────────────────────────────────┘
                 ↓
Generated SQL:
SELECT customers.name, orders.order_id
FROM customers, orders           ← Cartesian product
WHERE customers.state = 'CA'

┌──────────────────────────────────────────────────┐
│ STEP 2: Execute on Database                      │
└────────────────┬─────────────────────────────────┘
                 ↓
Result:
✅ Query succeeded
📊 500,000 rows (Cartesian product: 1000 customers × 500 orders)
⚠️  Timeout after 30 seconds

┌──────────────────────────────────────────────────┐
│ STEP 3: Analyze Failure                          │
└────────────────┬─────────────────────────────────┘
                 ↓
Analysis:
- Multiple tables without JOIN
- Result count excessive
- Query timeout

┌──────────────────────────────────────────────────┐
│ STEP 4: Self-Healing Repair                      │
└────────────────┬─────────────────────────────────┘
                 ↓
Schema Analysis:
- customers table has: customer_id (PK)
- orders table has: customer_id (FK → customers.customer_id)

Generate JOIN:
FROM customers
JOIN orders ON customers.customer_id = orders.customer_id

┌──────────────────────────────────────────────────┐
│ STEP 5: Re-Execute                               │
└────────────────┬─────────────────────────────────┘
                 ↓
Fixed SQL:
SELECT customers.name, orders.order_id
FROM customers
JOIN orders ON customers.customer_id = orders.customer_id
WHERE customers.state = 'CA'

Execute Result:
✅ Success in 0.3 seconds
📊 1,247 rows (correct!)

Return to User: SUCCESS
```

---

## 5. Implementation: Execution-Based Detection

```python
def execution_based_detection(sql: str, database) -> ErrorInfo:
    """
    Detect errors by actually executing SQL

    This is DIFFERENT from static analysis
    """
    # Try to execute
    result = execute_sql(sql, database)

    if result.error:
        # Database rejected it - we have error message
        return ErrorInfo(
            type='DATABASE_ERROR',
            message=result.error,
            detected_by='execution',
            fixable=True
        )

    elif result.empty:
        # Query succeeded but no results
        return ErrorInfo(
            type='EMPTY_RESULT',
            message='Query returned 0 rows',
            detected_by='execution',
            fixable=True  # Maybe fixable
        )

    elif result.timeout:
        # Query too slow
        return ErrorInfo(
            type='PERFORMANCE',
            message='Query timeout',
            detected_by='execution',
            fixable=True
        )

    else:
        # Query succeeded with data
        return ErrorInfo(
            type='SUCCESS',
            message='Query executed successfully',
            detected_by='execution',
            fixable=False  # No fix needed
        )
```

---

## 6. Error Classification from Database Messages

```python
ERROR_PATTERNS = {
    'NO_SUCH_TABLE': [
        r'no such table: (\w+)',
        r'table "(\w+)" does not exist',
        r'relation "(\w+)" does not exist'
    ],
    'NO_SUCH_COLUMN': [
        r'no such column: (\w+)',
        r'column "(\w+)" does not exist',
        r'unknown column "(\w+)"'
    ],
    'AMBIGUOUS_COLUMN': [
        r'ambiguous column name: (\w+)',
        r'column reference "(\w+)" is ambiguous'
    ],
    'SYNTAX_ERROR': [
        r'syntax error near "(.+)"',
        r'syntax error at or near "(.+)"'
    ],
    'CONSTRAINT_VIOLATION': [
        r'UNIQUE constraint failed: (.+)',
        r'foreign key constraint failed'
    ]
}

def classify_error(error_message: str) -> Tuple[str, str]:
    """
    Parse database error to determine type and extract info

    Example:
    Input: "no such column: regoin"
    Output: ('NO_SUCH_COLUMN', 'regoin')
    """
    for error_type, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                token = match.group(1)
                return (error_type, token)

    return ('UNKNOWN', error_message)
```

---

## 7. Complete Self-Healing Algorithm

```python
def self_healing_query_system(user_query: str) -> QueryResult:
    """
    Complete execution-based self-healing workflow
    """
    # Generate SQL
    sql = llm_generate_sql(user_query)

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        attempts += 1

        # Execute on database
        result = execute_on_database(sql)

        # Check result
        if result.success and result.has_data:
            # Success!
            return QueryResult(
                success=True,
                sql=sql,
                data=result.rows,
                attempts=attempts
            )

        elif result.database_error:
            # Database error - parse and fix
            error_type, token = classify_error(result.error)

            if error_type == 'NO_SUCH_COLUMN':
                # Quick fix: fuzzy match
                correct = fuzzy_match(token, schema.columns)
                sql = sql.replace(token, correct)

            elif error_type == 'NO_SUCH_TABLE':
                # Quick fix: fuzzy match
                correct = fuzzy_match(token, schema.tables)
                sql = sql.replace(token, correct)

            else:
                # Complex error: use LLM
                sql = llm_fix_error(sql, result.error, user_query)

        elif result.empty:
            # No results - analyze and fix
            if attempts == 1:
                # First try: analyze why empty
                sql = analyze_and_fix_empty(sql, user_query)
            else:
                # Second try: use LLM
                sql = llm_fix_empty(sql, user_query)

        elif result.timeout:
            # Performance issue - simplify query
            sql = optimize_query(sql)

        else:
            # Unknown issue
            break

    # Failed after retries
    return QueryResult(
        success=False,
        error="Unable to generate correct SQL after {} attempts".format(attempts),
        sql=sql
    )
```

---

## 8. Key Differences: Execution-Based vs Static Analysis

| Aspect | Static Analysis (Wrong) | Execution-Based (Correct) |
|--------|------------------------|---------------------------|
| **Detection** | Before execution | After execution fails |
| **Error Source** | AST parsing, schema lookup | Database error messages |
| **Coverage** | Limited (85%) | Complete (100% of executable errors) |
| **False Positives** | High (query looks wrong but runs) | None (database is truth) |
| **Latency** | Low (50ms) | Higher (includes execution) |
| **Reliability** | Heuristic-based | Definitive (from database) |

**Example:**
```sql
-- This query might LOOK wrong to static analysis:
SELECT * FROM (SELECT id FROM users) WHERE name = 'John'
-- Error: 'name' not in subquery

-- But if we execute it, database tells us the REAL error
-- Static analysis might miss other issues that database catches
```

---

## 9. Summary

### The CORRECT Workflow:

1. ✅ **Generate SQL** (LLM)
2. ✅ **Execute on Database** (try to run it)
3. ✅ **Check Result:**
   - Success + Data → Return to user
   - Database Error → Parse error, fix, retry
   - Empty Results → Analyze why, fix, retry
   - Timeout → Optimize, retry
4. ✅ **Self-Heal and Retry** (up to 3 times)
5. ✅ **Return Result or Error**

### Why This Works Better:

- ✅ Database is the source of truth
- ✅ Real errors, not guesses
- ✅ No false positives
- ✅ Covers 100% of execution errors
- ✅ Simpler logic (parse error message vs complex static analysis)

### Error Detection is NOT needed beforehand because:
- Database will tell us what's wrong
- We fix based on actual execution feedback
- More reliable than guessing errors statically
