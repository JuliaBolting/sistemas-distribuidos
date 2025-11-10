import random
import argparse
from pathlib import Path

#gera duas matrizes do mesmo tamanho
def generate(mat_size, out_a, out_b):
    out_a = Path(out_a)
    out_b = Path(out_b)
    out_a.parent.mkdir(parents=True, exist_ok=True)
    out_b.parent.mkdir(parents=True, exist_ok=True)

#Abre os arquivos contendo as matrizes. 
    with open(out_a, "w", encoding="utf8") as fa, open(out_b, "w", encoding="utf8") as fb:
        for i in range(mat_size):
            row_a = [] #Cria duas listas vazias para armazenar as linhas das matrizes A e B.
            row_b = []
            for j in range(mat_size):
                row_a.append(f"{random.uniform(0.15,1.15):.4f}")
                row_b.append(f"{random.uniform(0.15,1.15):.4f}")
            fa.write(" ".join(row_a))
            fb.write(" ".join(row_b))
            if i != mat_size - 1:
                fa.write("\n")
                fb.write("\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--size", type=int, default=100, help="matrix size")
    p.add_argument("--outdir", default="data")
    args = p.parse_args()
    generate(args.size, f"{args.outdir}/matA.txt", f"{args.outdir}/matB.txt")
    print("Generated matA and matB in", args.outdir)
