---
name: software-developer
description: The guidelines to follow in any codebase modification, use it when you are asked to modify something in the codebase.
---

# Software Developer

## Instructions

1.  **Define Strict Data Contracts:** For any data entering your system (from an API, a database, a message queue), define a strict schema using Pydantic models (DTOs). Specify exact data types (`int`, `bool`, `str`, `Decimal`) for all fields. Use `src/utils/decimal_utils.py` for financial precision. Do not use generic types like `Any`.

2.  **Validate Once, at the Entry Point:** Instantiate your Pydantic model immediately when the external data is received. This is the **only** place validation should occur.

3.  **Handle Validation Errors at the Boundary:** Wrap the schema instantiation in a `try...except ValidationError` block to catch validation failures. If validation fails, reject the data immediately using project-specific errors from `src/*/errors.py`.

4.  **Trust Your Internal Objects:** Once an object has been successfully created (e.g., `PortfolioConfig`), trust it. Do not perform `None` checks or type checks on its properties later in the code.

5.  **Use Financial Precision:** Always use `Decimal` for monetary values. Follow the precision rules:
    - Money: 2 decimal places (`quantize_money`)
    - Quantity: 9 decimal places (`quantize_quantity`)
    - Percentage: 4 decimal places (`quantize_percentage`)

6.  **Use Named Boolean Validation:** Avoid using `if` with complex conditions. Use a descriptive boolean variable to explain the condition.

7.  **Avoid Magic Numbers:** Use constants (e.g., from `src/config/config.py`) instead of hardcoded numbers.

8.  **Self-Documenting Code:** Avoid comments. Use descriptive function and variable names to make the code self-explanatory. Only add comments if absolutely necessary for complex algorithms.

9.  **Do Not Write Tests:** Unless explicitly requested by the user.

**To-Do Checklist:**
- [ ] Review your code. Are you validating the same variable in multiple places? Consolidate this logic into a single schema validation at the start.
- [ ] Change all manual type conversions (e.g., `int(variable)`) surrounded by `try...except` to be handled by a data schema's type declarations.
- [ ] Remove any `if data["key"] is not None:` checks if that key is a required field in your schema.

---

### 2. Error Management: Errors Are State, not just logs

**Objective:** Build predictable systems that are transparent about their failures, making them easier to debug and monitor.

**Instructions:**

1.  **Model Errors Explicitly:** Do not just log an error and continue. An error is a critical piece of information. Your function's return value must reflect it.

2.  **Return Structured State:** Functions that can fail should return an object that includes a status field (e.g., `status: "SUCCESS" | "FAILED"`) and a field for error details (e.g., `errors: list`).

3.  **Make Control-Flow Decisions Based on Error State:** The code that calls your function must check the returned `status`. If it is `FAILED`, it must react accordingly (e.g., return an HTTP 500 error, enqueue a retry, or abort the process).

4.  **Eliminate "Log and Forget":** An `except` block that only contains `logging.error(...)` and then allows the program to continue as if nothing happened is a bug. The `except` block must change the state that will be returned.

**To-Do Checklist:**
- [ ] Find `except` blocks that only log an error. Modify them to update a state variable that will be returned if this can be done in a single place.
- [ ] Change functions that return data directly on success and `None` on failure. Instead, make them always return a state object like `{ "status": ..., "data": ..., "errors": ... }`.

---

### 3. Function Scope: Do Not Nest Functions

**Objective:** Ensure functions are testable, reusable, and predictable by avoiding hidden state capture and complex scopes.

**Instructions:**

1.  Define functions only at module scope or as class/static methods. Do not declare functions inside other functions or methods.
2.  Extract inner logic to a top-level helper (use a descriptive name, prefix with `_` if internal) or a `@staticmethod`/`@classmethod` on the relevant class.
3.  Pass all dependencies via explicit parameters. Never rely on closures capturing outer variables.
4.  Keep validators and hooks free of nested defs; place shared utilities at module scope and call them.

**To-Do Checklist:**
- [ ] Refactor any nested `def` into top-level helpers or static/class methods.
- [ ] Replace closures with explicit parameters to remove hidden state.
- [ ] Add/adjust unit tests for extracted helpers to preserve behavior.

### 4. Code Structure: Optimize for Readability

**Objective:** Write code that is easy for other developers (and your future self) to read, understand, and modify safely.

**Instructions:**

1.  **Write Small, Single-Purpose Functions:** A function should do one thing. Its name should accurately describe what it does. If you cannot find a simple, descriptive name, the function is likely doing too much.

2.  **Use Guard Clauses to Reduce Nesting:** Instead of nesting `if` statements, check for invalid conditions at the beginning of your function and exit early (`return`, `continue`, or `raise`).

    -   **Avoid:** `if condition: ... (deeply nested code) ...`
    -   **Prefer:** `if not condition: return`

3.  **Name Variables to Reveal Intent:** A variable's name should clearly state its purpose. Avoid single-letter or overly generic names. Good naming makes code self-documenting. You cannot use letters or non semantical works in your code changes.

4.  **Extract Complex Logic into Functions:** If a loop or conditional block becomes complex, move that logic into a new function. Give the new function a name that explains *what* it does. This hides the complexity (the *how*) and makes the original code easier to read.

**To-Do Checklist:**
- [ ] Identify functions longer than 20-25 lines. Can they be broken down into smaller, helper functions?
- [ ] Find nested `if/else` statements. Can they be flattened by using guard clauses?
- [ ] Look for variables named `data`, `item`, `x`, or `temp`. Rename them to be more descriptive.
- [ ] Don not add comments to the code, use the code to autoexplain the code itself. Just add comments to the code if is ultra really necessary.

### 5. Reliability & Resilience: Fail Fast, Recover Gracefully

**Objective:** Keep systems usable under partial failure.

**Instructions:**

Use retries with exponential backoff for transient errors only.

Make write operations idempotent (keys, dedup tables, version checks).

Apply circuit breakers and bulkheads around fragile dependencies.

Enforce request deadlines end-to-end (pass them downstream).

**To-Do Checklist:**

- [ ] Add idempotency keys to POST/PUT affecting state.
- [ ] Wrap flaky calls with circuit breakers.
- [ ] Define and propagate deadlines via headers/context.


### 6. Optimize Database Interactions

**Objective:** Ensure your application interacts with the database in the most efficient way possible to
minimize latency and resource consumption.

  Instructions:

  1. Use Bulk Operations: For creating or updating multiple records, always use bulk methods
  (bulk_insert_mappings, etc.) to reduce database roundtrips.
  2. Select Only What You Need: When querying data, use load_only or select specific columns to retrieve
  only the data you need.
  3. Master Eager Loading: Use joinedload or selectinload to prevent the "N+1 query problem" by loading
  related objects in a single query.
  4. Push Computation to the Database: Whenever possible, use the database's built-in functions (e.g.,
  ts_rank, aggregations) instead of processing raw data in Python.

**To-Do Checklist:**
- [ ] Review your repository methods. Are there any loops that contain database queries? Can they be replaced
with a single, more efficient query?
- [ ] For every query, ask yourself: "Do I need all the columns from this table?" If not, use load_only.
- [ ] Check for any manual data processing that could be done more efficiently in the database.

### 7. Use named boolean validation in if statements if the condition is complex

Avoid using if with complex to understand condition, use a name boolean variable to validate the condition

python example:

```python
if not user.is_active and not user.is_admin:
    return False
```

should be:

```python
have_enough_balance = (
  user.balance < 100
  and user.is_active
  and user.is_admin
)
if have_enough_balance:
    return False
```

### 8. Avoid magic numbers

Avoid using magic numbers in the code, use constants instead

python example:

```python
if user.age < 18:
    return False
```

should be:

```python
MIN_AGE = 18
is_user_under_age = user.age < MIN_AGE
if is_user_under_age:
    return False
```

### 9. Type Safety Strategy: Pydantic vs Type Hints

- **Roles:** Python type hints (with `mypy`) ensure static safety during development. Pydantic schemas execute at runtime, providing a strict guard at system boundaries (APIs, Broker responses, Configuration).
- **When to use Type Hints:** Describe protocols (like `Broker` in `src/broker/broker_interface.py`) and internal function signatures.
- **When to use Pydantic:** Validate all external inputs and DTOs. Use `ConfigDict(frozen=True)` for immutability where possible.
- **Clean architecture flow:** External Source -> Pydantic Model (Runtime Validation) -> Internal Logic (Static Type Safety).

**To-Do Checklist:**
- [ ] Add Pydantic models to every entry point where data crosses trust boundaries.
- [ ] Use `Decimal` and quantization for all financial calculations.
- [ ] Ensure all models use `ConfigDict(arbitrary_types_allowed=True)` if they include non-Pydantic objects.

### 10. Event-Driven Architecture

- **Objective:** Maintain decoupled communication between system components using the internal `EventBus`.
- **Instructions:**
    1. Define events as Pydantic models in `src/event_bus/event_dtos.py`.
    2. Register handlers in `src/event_bus/event_handlers.py`.
    3. Emit events using the `EventBus` for side effects (e.g., price changes triggering rebalancing) rather than direct calls between domains.

**To-Do Checklist:**
- [ ] Are domains directly calling each other? Refactor to use the `EventBus`.
- [ ] Use `src/*/errors.py` for all custom exceptions.
- [ ] Ensure `Decimal` is used for all money-related logic in events.


### Error Handling Pattern

The project uses a custom error hierarchy for consistent error management:
- Location: `src/*/errors.py` (e.g., `src/portfolio/errors.py`)
- Custom exceptions inheriting from a base error (e.g., `PortfolioError`).
- Meaningful error messages and context (like `failed_operations` or `attempt` count).
- Consistent structure for reporting failures to the event bus.
