"""
TOPIC 5: Code Validators — 30+ practical examples
Covers: ValidPython, ValidSQL, ValidOpenAPISpec, ExcludeSQLPredicates,
        SqlColumnPresence, SecretsPresent, WebSanitization, EndpointIsReachable

Install:
  guardrails hub install hub://guardrails/valid_python
  guardrails hub install hub://guardrails/valid_sql
  guardrails hub install hub://guardrails/valid_openapi_spec
  guardrails hub install hub://guardrails/exclude_sql_predicates
  guardrails hub install hub://guardrails/sql_column_presence
  guardrails hub install hub://guardrails/secrets_present
  guardrails hub install hub://guardrails/web_sanitization
  guardrails hub install hub://guardrails/endpoint_is_reachable
"""

import openai
from guardrails import Guard

# ──────────────────────────────────────────────────────────────────────────────
# VALID PYTHON
# ──────────────────────────────────────────────────────────────────────────────

# ── 1. Basic Python syntax validation ────────────────────────────────────────
from guardrails.hub import ValidPython

guard1 = Guard().use(ValidPython, on_fail="exception")
guard1.parse("def greet(name):\n    return f'Hello, {name}'")

# ── 2. Reject invalid Python ──────────────────────────────────────────────────
try:
    guard1.parse("def broken(\n    return 'oops'")
except Exception as e:
    print(f"Invalid Python: {e}")

# ── 3. LLM code generator with syntax gate ───────────────────────────────────
guard3 = Guard().use(ValidPython, on_fail="reask")
res3 = guard3(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Write a Python function that reverses a string. Return only code, no explanation.",
    }],
    num_reasks=2,
)
print(res3.validated_output)

# ── 4. Python code generation pipeline ───────────────────────────────────────
def generate_python(task_description: str) -> str:
    guard = Guard().use(ValidPython, on_fail="reask")
    res = guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only valid Python code with no markdown."},
            {"role": "user", "content": task_description},
        ],
        num_reasks=3,
    )
    return res.validated_output

code = generate_python("Implement binary search in Python.")
print(code)

# ── 5. Validate and execute LLM-generated Python safely ──────────────────────
import ast

def safe_exec(code: str) -> dict:
    guard = Guard().use(ValidPython, on_fail="exception")
    guard.parse(code)
    tree = ast.parse(code)
    # Only exec if no imports (safety check)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Imports not allowed in sandboxed execution")
    local_ns = {}
    exec(compile(tree, "<string>", "exec"), {}, local_ns)
    return local_ns

ns = safe_exec("def add(a, b):\n    return a + b")
print(ns["add"](2, 3))   # 5

# ── 6. Async Python code generation ──────────────────────────────────────────
import asyncio
from guardrails import AsyncGuard

async def async_generate_python(task: str) -> str:
    aguard = AsyncGuard().use(ValidPython, on_fail="reask")
    res = await aguard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only valid Python code."},
            {"role": "user", "content": task},
        ],
        num_reasks=2,
    )
    return res.validated_output

asyncio.run(async_generate_python("Write a bubble sort function."))

# ──────────────────────────────────────────────────────────────────────────────
# VALID SQL
# ──────────────────────────────────────────────────────────────────────────────

# ── 7. Basic SQL validation ───────────────────────────────────────────────────
from guardrails.hub import ValidSQL

guard7 = Guard().use(ValidSQL, on_fail="exception")
guard7.parse("SELECT id, name FROM users WHERE active = 1;")

# ── 8. Reject invalid SQL ─────────────────────────────────────────────────────
try:
    guard7.parse("SELEKT * FORM users;")
except Exception as e:
    print(f"Invalid SQL: {e}")

# ── 9. Natural-language to SQL with validation ───────────────────────────────
def text_to_sql(natural_language: str) -> str:
    guard = Guard().use(ValidSQL, on_fail="reask")
    res = guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Convert natural language to SQL. Return only the SQL query."},
            {"role": "user", "content": natural_language},
        ],
        num_reasks=3,
    )
    return res.validated_output

sql = text_to_sql("Find all customers who made a purchase in the last 30 days.")
print(sql)

# ── 10. Exclude SQL predicates (prevent dangerous queries) ────────────────────
from guardrails.hub import ExcludeSQLPredicates

guard10 = Guard().use(
    ExcludeSQLPredicates,
    predicates=["DROP", "DELETE", "TRUNCATE", "ALTER"],
    on_fail="exception",
)
guard10.parse("SELECT name, email FROM customers WHERE city = 'NYC';")

try:
    guard10.parse("DROP TABLE customers;")
except Exception as e:
    print(f"Dangerous SQL blocked: {e}")

# ── 11. Exclude SQL predicates — prevent data modification ───────────────────
readonly_guard = Guard().use(
    ExcludeSQLPredicates,
    predicates=["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"],
    on_fail="exception",
)
readonly_guard.parse("SELECT COUNT(*) FROM orders WHERE status = 'pending';")

# ── 12. SQL column presence — ensure query uses expected columns ──────────────
from guardrails.hub import SqlColumnPresence

guard12 = Guard().use(
    SqlColumnPresence,
    cols_present=["user_id", "created_at"],
    on_fail="exception",
)
guard12.parse("SELECT user_id, name, created_at FROM accounts;")

# ── 13. SQL validation + column presence combo ───────────────────────────────
reporting_guard = Guard().use_many(
    ValidSQL(on_fail="reask"),
    ExcludeSQLPredicates(predicates=["DROP", "DELETE", "INSERT", "UPDATE"], on_fail="exception"),
    SqlColumnPresence(cols_present=["report_date"], on_fail="exception"),
)
reporting_guard.parse("SELECT report_date, total_sales FROM sales_summary;")

# ── 14. Text-to-SQL for analytics dashboards ─────────────────────────────────
analytics_guard = Guard(name="analytics-sql").use_many(
    ValidSQL(on_fail="reask"),
    ExcludeSQLPredicates(
        predicates=["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER"],
        on_fail="exception",
    ),
)

def safe_analytics_query(question: str) -> str:
    res = analytics_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate read-only SQL. Return SQL only."},
            {"role": "user", "content": question},
        ],
        num_reasks=2,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# VALID OPENAPI SPEC
# ──────────────────────────────────────────────────────────────────────────────

# ── 15. Validate an OpenAPI spec ─────────────────────────────────────────────
from guardrails.hub import ValidOpenAPISpec

openapi_spec = """
openapi: "3.0.0"
info:
  title: "Sample API"
  version: "1.0.0"
paths:
  /users:
    get:
      summary: "Get all users"
      responses:
        "200":
          description: "A list of users"
"""

guard15 = Guard().use(ValidOpenAPISpec, on_fail="exception")
guard15.parse(openapi_spec)

# ── 16. LLM generates OpenAPI spec with validation ───────────────────────────
guard16 = Guard().use(ValidOpenAPISpec, on_fail="reask")
res16 = guard16(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "Generate a valid OpenAPI 3.0 YAML spec for a simple Task management API with create and list endpoints.",
    }],
    num_reasks=3,
)
print(res16.validated_output)

# ──────────────────────────────────────────────────────────────────────────────
# SECRETS PRESENT
# ──────────────────────────────────────────────────────────────────────────────

# ── 17. Detect secrets in LLM output ─────────────────────────────────────────
from guardrails.hub import SecretsPresent

guard17 = Guard().use(SecretsPresent, on_fail="exception")
try:
    guard17.parse(
        "Here is the config: AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
    )
except Exception as e:
    print(f"Secret detected: {e}")

# ── 18. Prevent API keys leaking in generated code ───────────────────────────
guard18 = Guard().use(SecretsPresent, on_fail="exception")
try:
    guard18.parse(
        "client = openai.OpenAI(api_key='sk-proj-abc123xyz789secretkeyvalue')"
    )
except Exception as e:
    print(f"API key leaked: {e}")

# ── 19. Code generation with secrets check ───────────────────────────────────
safe_code_guard = Guard().use_many(
    ValidPython(on_fail="reask"),
    SecretsPresent(on_fail="exception"),
)

def generate_safe_code(prompt: str) -> str:
    res = safe_code_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only Python code. Never include real credentials."},
            {"role": "user", "content": prompt},
        ],
        num_reasks=2,
    )
    return res.validated_output

# ──────────────────────────────────────────────────────────────────────────────
# WEB SANITIZATION
# ──────────────────────────────────────────────────────────────────────────────

# ── 20. Sanitize HTML/JS from LLM output ─────────────────────────────────────
from guardrails.hub import WebSanitization

guard20 = Guard().use(WebSanitization, on_fail="fix")
res20 = guard20.parse(
    '<p>Hello</p><script>alert("xss")</script>'
)
print(res20.validated_output)   # script tag removed

# ── 21. Sanitize user-facing HTML ─────────────────────────────────────────────
guard21 = Guard().use(WebSanitization, on_fail="fix")
res21 = guard21.parse(
    '<a href="javascript:void(0)" onclick="steal()">Click me</a>'
)
print(res21.validated_output)

# ── 22. Full web content pipeline: sanitize + valid HTML ─────────────────────
from guardrails.hub import ValidHtml, WebSanitization

web_guard = Guard().use_many(
    WebSanitization(on_fail="fix"),
    ValidHtml(on_fail="exception"),
)
res22 = web_guard.parse("<h1>Welcome</h1><p>Safe content here.</p>")
print(res22.validated_output)

# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT IS REACHABLE
# ──────────────────────────────────────────────────────────────────────────────

# ── 23. Validate URL is reachable ────────────────────────────────────────────
from guardrails.hub import EndpointIsReachable

guard23 = Guard().use(EndpointIsReachable, on_fail="exception")
guard23.parse("https://api.github.com")

# ── 24. URL + reachability combo ─────────────────────────────────────────────
from guardrails.hub import ValidUrl, EndpointIsReachable

url_guard = Guard().use_many(
    ValidUrl(on_fail="exception"),
    EndpointIsReachable(on_fail="exception"),
)
url_guard.parse("https://httpbin.org/get")

# ──────────────────────────────────────────────────────────────────────────────
# COMPOSITE CODE PIPELINES
# ──────────────────────────────────────────────────────────────────────────────

# ── 25. Full code review guard ────────────────────────────────────────────────
code_review_guard = Guard(name="code-review").use_many(
    ValidPython(on_fail="reask"),
    SecretsPresent(on_fail="exception"),
)

def ai_code_review(task: str) -> str:
    res = code_review_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only Python code. No credentials."},
            {"role": "user", "content": task},
        ],
        num_reasks=2,
    )
    return res.validated_output

# ── 26. DB query builder with safety rails ────────────────────────────────────
db_query_guard = Guard(name="db-query").use_many(
    ValidSQL(on_fail="reask"),
    ExcludeSQLPredicates(
        predicates=["DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE", "ALTER"],
        on_fail="exception",
    ),
)

def nl_to_safe_sql(question: str) -> str:
    res = db_query_guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Convert to read-only SQL. Return only the SQL."},
            {"role": "user", "content": question},
        ],
        num_reasks=3,
    )
    return res.validated_output

print(nl_to_safe_sql("Show me the top 10 customers by revenue."))

# ── 27. Code + secrets + XSS for full-stack generation ───────────────────────
fullstack_guard = Guard(name="fullstack").use_many(
    ValidPython(on_fail="reask"),
    SecretsPresent(on_fail="exception"),
    WebSanitization(on_fail="fix"),
)

# ── 28. API spec generator with validation ────────────────────────────────────
def generate_api_spec(service_description: str) -> str:
    guard = Guard().use(ValidOpenAPISpec, on_fail="reask")
    res = guard(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate a valid OpenAPI 3.0 YAML spec. Return only YAML."},
            {"role": "user", "content": service_description},
        ],
        num_reasks=3,
    )
    return res.validated_output

spec = generate_api_spec("A REST API for managing library books with CRUD operations.")
print(spec)

# ── 29. SQL injection prevention for chatbots ────────────────────────────────
injection_guard = Guard().use(
    ExcludeSQLPredicates,
    predicates=["DROP", "DELETE", "UPDATE", "INSERT", "EXEC", "EXECUTE", "xp_", "--"],
    on_fail="exception",
)
try:
    injection_guard.parse("SELECT * FROM users; DROP TABLE users; --")
except Exception as e:
    print(f"SQL injection blocked: {e}")

# ── 30. Python function signature validator ───────────────────────────────────
import ast

def validate_python_function(code: str, expected_func_name: str) -> bool:
    guard = Guard().use(ValidPython, on_fail="exception")
    guard.parse(code)
    tree = ast.parse(code)
    func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    return expected_func_name in func_names

raw_code = "def calculate_bmi(weight, height):\n    return weight / (height ** 2)"
print(validate_python_function(raw_code, "calculate_bmi"))   # True

# ── 31. Batch SQL validation ──────────────────────────────────────────────────
queries = [
    "SELECT * FROM users;",
    "SELECT name FROM products WHERE price > 10;",
    "SELEKT FROM broken;",                    # invalid
    "DROP TABLE users;",                       # dangerous
]

sql_guard = Guard().use(ValidSQL, on_fail="noop")
readonly = Guard().use(ExcludeSQLPredicates, predicates=["DROP", "DELETE"], on_fail="noop")

for q in queries:
    syntax_ok = sql_guard.parse(q).validation_passed
    safe = readonly.parse(q).validation_passed
    print(f"Query: {q[:40]:<40} | Syntax: {syntax_ok} | Safe: {safe}")

# ── 32. Auto-fix XSS in LLM-generated HTML ───────────────────────────────────
def render_llm_html(prompt: str) -> str:
    raw = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Generate HTML for: {prompt}"}],
    ).choices[0].message.content

    guard = Guard().use_many(
        WebSanitization(on_fail="fix"),
        ValidHtml(on_fail="exception"),
    )
    res = guard.parse(raw)
    return res.validated_output
