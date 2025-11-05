from __future__ import annotations
import os, time, math, csv, socket, platform, random
from pathlib import Path
from datetime import datetime

import numpy as np

OUT_DIR = Path("results")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "benchmarks.csv"


FIX_THREADS = os.environ.get("BENCH_THREADS", "1")
if FIX_THREADS:
    os.environ["OMP_NUM_THREADS"] = FIX_THREADS
    os.environ["OPENBLAS_NUM_THREADS"] = FIX_THREADS
    os.environ["MKL_NUM_THREADS"] = FIX_THREADS
    os.environ["BLIS_NUM_THREADS"] = FIX_THREADS
    os.environ["VECLIB_MAXIMUM_THREADS"] = FIX_THREADS
    os.environ["NUMEXPR_NUM_THREADS"] = FIX_THREADS

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

def median_time(fn, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return sorted(times)[len(times)//2]

def bench_scalar_int(total_ops: int = 50_000_000) -> dict:
    a = 1
    b = 3
    iters = total_ops // 3 
    def run():
        nonlocal a, b
        x = 0
        for i in range(iters):
            x += a + b
            x -= a
            x *= 2
        return x
    run()
    dt = median_time(run, repeats=3)
    ops = iters * 3
    return {"ops": ops, "time_s": dt, "ops_per_s": ops / dt}

def bench_scalar_float(total_ops: int = 50_000_000) -> dict:
    a = 1.0
    b = math.pi
    iters = total_ops // 3
    def run():
        x = 0.0
        for i in range(iters):
            x = (x + a) * b  
            x = x + a       
        return x
    run()
    dt = median_time(run, repeats=3)
    flops = iters * 3
    return {"ops": flops, "time_s": dt, "ops_per_s": flops / dt}


def bench_gemm(n: int, dtype=np.float64, repeats: int = 3) -> dict:
    A = np.random.rand(n, n).astype(dtype)
    B = np.random.rand(n, n).astype(dtype)
    _ = A @ B
    def run():
        t0 = time.perf_counter()
        C = A @ B
        dt = time.perf_counter() - t0
        if C[0,0] < -1e300: 
            print("ignore", C[0,0])
        return dt
    times = [run() for _ in range(repeats)]
    dt = sorted(times)[len(times)//2]
    flops = 2.0 * (n**3)
    gflops = flops / dt / 1e9
    return {"n": n, "dtype": str(dtype), "time_s": dt, "gflops": gflops}

rows = []

res_i = bench_scalar_int(total_ops=30_000_000)
rows.append({
    "timestamp": STAMP, "host": HOST, "cpu": CPU_INFO, "python": PY_INFO,
    "section": "scalar", "metric": "int_ops_per_s","dtype": "int","n": "",
    "iters": res_i["ops"], "time_s": f"{res_i['time_s']:.6f}",
    "value": f"{res_i['ops_per_s']:.3f}", "notes": f"threads={FIX_THREADS or 'auto'}"
})

res_f = bench_scalar_float(total_ops=30_000_000)
rows.append({
    "timestamp": STAMP, "host": HOST, "cpu": CPU_INFO, "python": PY_INFO,
    "section": "scalar", "metric": "float_ops_per_s","dtype": "float","n": "",
    "iters": res_f["ops"], "time_s": f"{res_f['time_s']:.6f}",
    "value": f"{res_f['ops_per_s']:.3f}", "notes": f"threads={FIX_THREADS or 'auto'}"
})

for dtype in (np.float32, np.float64):
    for n in (256, 512, 1024, 1536):
        r = bench_gemm(n=n, dtype=dtype, repeats=3)
        rows.append({
            "timestamp": STAMP, "host": HOST, "cpu": CPU_INFO, "python": PY_INFO,
            "section": "gemm", "metric": "gflops","dtype": "float32" if dtype==np.float32 else "float64",
            "n": n, "iters": "", "time_s": f"{r['time_s']:.6f}",
            "value": f"{r['gflops']:.3f}", "notes": f"threads={FIX_THREADS or 'auto'}"
        })

write_rows(rows)

print(f"[OK] Benchmark salvo em: {OUT_CSV}")
for r in rows:
    print(r)
