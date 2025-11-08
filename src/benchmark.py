from __future__ import annotations
import os, time, math, csv, socket, platform
from pathlib import Path
from datetime import datetime
import numpy as np

OUT_DIR = Path("results")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "benchmarks.csv"

# Fixar número de threads para tornar comparável entre hosts
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["BLIS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

HOST = socket.gethostname()
STAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
CPU_INFO = platform.processor() or platform.machine()
PY_INFO = platform.python_version()

def write_rows(rows):
    header = [
        "timestamp","host","cpu","python","section","metric","dtype","n",
        "iters","time_s","value","notes"
    ]
    file_exists = OUT_CSV.exists()
    with OUT_CSV.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)

def median_time(fn, repeats=3):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return sorted(times)[len(times)//2]

def bench_scalar_int(total_ops: int = 500_000) -> dict:
    a, b = 1, 3
    iters = total_ops // 3
    def run():
        x = 0
        for i in range(iters):
            x += a + b
            x -= a
            x *= 2
            
            if i % (iters // 10) == 0 and i > 0:
                print(f"   [int] progresso: {100 * i/iters:.0f}%")
        return x
    run()
    dt = median_time(run)
    return {"ops": iters*3, "time_s": dt}

def bench_scalar_float(total_ops: int = 5_000_000) -> dict:
    a, b = 1.0, math.pi
    iters = total_ops // 3
    def run():
        x = 0.0
        for _ in range(iters):
            x = (x + a) * b
            x = x + a
        return x
    run()
    dt = median_time(run)
    return {"ops": iters*3, "time_s": dt}

def bench_gemm(n: int, dtype=np.float64) -> dict:
    A = np.random.rand(n, n).astype(dtype)
    B = np.random.rand(n, n).astype(dtype)
    _ = A @ B  # warm-up
    t0 = time.perf_counter()
    C = A @ B
    dt = time.perf_counter() - t0
    flops = 2.0*(n**3)
    gflops = flops/dt/1e9
    return {"n": n, "dtype": str(dtype), "time_s": dt, "gflops": gflops}

def run_benchmark():
    rows = []
    print("\n=== Benchmark iniciado ===")

    # scalar int
    print("-> Teste escalar (inteiro)")
    i = bench_scalar_int()
    rows.append({
        "timestamp": STAMP, "host": HOST, "cpu": CPU_INFO, "python": PY_INFO,
        "section": "scalar", "metric": "int_ops_per_s", "dtype": "", "n": 0,
        "iters": 0, "time_s": i["time_s"], "value": i["ops"]/i["time_s"], "notes": ""
    })
    print("  Ops/s:", i["ops"]/i["time_s"])

    # scalar float
    print("-> Teste escalar (float)")
    f = bench_scalar_float()
    rows.append({
        "timestamp": STAMP, "host": HOST, "cpu": CPU_INFO, "python": PY_INFO,
        "section": "scalar", "metric": "float_ops_per_s", "dtype": "", "n": 0,
        "iters": 0, "time_s": f["time_s"], "value": f["ops"]/f["time_s"], "notes": ""
    })
    print("  Ops/s:", f["ops"]/f["time_s"])

    # GEMM FLOAT64 — tamanhos menores e mais rápidos
    for n in (256, 512):
        print(f"-> GEMM: n={n}, dtype=float64")
        r = bench_gemm(n=n)
        rows.append({
            "timestamp": STAMP, "host": HOST, "cpu": CPU_INFO, "python": PY_INFO,
            "section": "gemm", "metric": "gflops", "dtype": "float64", "n": n,
            "iters": 1, "time_s": r["time_s"], "value": r["gflops"], "notes": ""
        })
        print(f"   {r['gflops']:.2f} GFLOPS, time={r['time_s']:.3f}s")

    write_rows(rows)
    print("[OK] Benchmark salvo em:", OUT_CSV)

if __name__ == "__main__":
    run_benchmark()