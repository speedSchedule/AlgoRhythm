import os
import ssl
from urllib.parse import urlparse
import pg8000.native
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# DB 연결
# ---------------------------------------------------------------------------

def get_conn() -> pg8000.native.Connection:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError("DATABASE_URL or POSTGRES_URL is not set")

    p = urlparse(url)
    ctx = ssl.create_default_context()

    return pg8000.native.Connection(
        user=p.username,
        password=p.password,
        host=p.hostname,
        port=p.port or 5432,
        database=p.path.lstrip("/"),
        ssl_context=ctx,
    )


def ensure_table():
    conn = get_conn()
    conn.run("""
        CREATE TABLE IF NOT EXISTS calc_logs (
            id SERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            a FLOAT NOT NULL,
            b FLOAT NOT NULL,
            op TEXT NOT NULL,
            result FLOAT,
            error TEXT
        )
    """)
    conn.close()


def insert_log(a, b, op, result, error):
    try:
        conn = get_conn()
        conn.run(
            "INSERT INTO calc_logs (a, b, op, result, error) VALUES (:a, :b, :op, :result, :error)",
            a=a, b=b, op=op, result=result, error=error,
        )
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] {e}")


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Calculator</title>
</head>
<body>
<h2>Calculator</h2>

<form id="calcForm">
<input type="number" id="a" placeholder="숫자 1" required>
<select id="op">
<option value="add">+</option>
<option value="sub">-</option>
<option value="mul">×</option>
<option value="div">÷</option>
</select>
<input type="number" id="b" placeholder="숫자 2" required>
<button type="submit">계산</button>
</form>

<p id="result"></p>

<script>
document.getElementById("calcForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const a = document.getElementById("a").value;
    const b = document.getElementById("b").value;
    const op = document.getElementById("op").value;

    const res = await fetch(`/api/calc?a=${a}&b=${b}&op=${op}`);
    const data = await res.json();

    document.getElementById("result").textContent =
        data.error ? `오류: ${data.error}` : `결과: ${data.result}`;
});
</script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.get("/api/calc")
def calc(a: float = Query(...), b: float = Query(...), op: str = Query("add")):
    ops = {
        "add": a + b,
        "sub": a - b,
        "mul": a * b,
        "div": a / b if b != 0 else None,
    }

    if op not in ops:
        insert_log(a, b, op, None, "invalid operator")
        return {"error": "invalid operator"}

    if ops[op] is None:
        insert_log(a, b, op, None, "division by zero")
        return {"error": "division by zero"}

    result = ops[op]
    insert_log(a, b, op, result, None)
    return {"result": result}


@app.get("/api/logs")
def logs(limit: int = Query(20, ge=1, le=100)):
    try:
        ensure_table()
        conn = get_conn()
        rows = conn.run(
            "SELECT id, ts, a, b, op, result, error FROM calc_logs ORDER BY id DESC LIMIT :limit",
            limit=limit,
        )
        conn.close()

        return [
            {
                "id": r[0],
                "ts": r[1].isoformat(),
                "a": r[2],
                "b": r[3],
                "op": r[4],
                "result": r[5],
                "error": r[6],
            }
            for r in rows
        ]

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/init-db")
def init_db():
    try:
        ensure_table()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
