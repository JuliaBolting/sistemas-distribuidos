import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from src.utils.hash_check import sha256_of_file, save_hash
from src.utils.timer import TemporizadorSimples, adicionar_log, agora_ts
import numpy as np
from numba import njit, prange

# utiliza Numba para acelerar o cálculo da multiplicação matricial usando paralelismo automático
@njit(parallel=True, fastmath=True)
def multiplicacao_numba(matA, matB):
    n = matA.shape[0]
    m = matB.shape[1]
    p = matB.shape[0]

    matC = np.zeros((n, m), dtype=np.float64)

    for i in prange(n):
        for k in range(p):
            for j in range(m):
                matC[i, j] += matA[i, k] * matB[k, j]

    return matC

def multiplicar_linha(args):
    # Calcula produto de uma linha da matriz A com a matriz B
    idx, linha, matrizB = args
    num_colunas = len(matrizB[0])
    num_elem = len(matrizB)
    resultado_linha = [0.0 for _ in range(num_colunas)]
    for j in range(num_colunas):
        for k in range(num_elem):
            resultado_linha[j] += linha[k] * matrizB[k][j]
    return (idx, resultado_linha)

def multiplicacao_paralela_local(matA, matB, num_workers):
    # Multiplicação de matrizes em paralelo usando ProcessPoolExecutor
    # Cada processo calcula uma linha inteira da matriz C
    n = len(matA)
    matC = [[0.0 for _ in range(len(matB[0]))] for _ in range(n)]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        argumentos = [(i, matA[i], matB) for i in range(n)]
        for idx, linha_resultante in executor.map(multiplicar_linha, argumentos):
            matC[idx] = linha_resultante

    return matC


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matdir", default="data", help="Diretório das matrizes")
    parser.add_argument("--outdir", default="results", help="Diretório de saída")
    parser.add_argument("--workers", type=int, default=None, help="Número de processadores (default: cpu_count())")
    args = parser.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    # Carregar matrizes
    matA = []
    matB = []
    with open(f"{args.matdir}/matA.txt", "r") as f:
        for linha in f:
            matA.append([float(x) for x in linha.strip().split()])
    with open(f"{args.matdir}/matB.txt", "r") as f:
        for linha in f:
            matB.append([float(x) for x in linha.strip().split()])

    num_workers = args.workers or multiprocessing.cpu_count()

    # Multiplicação paralela e medição de tempo
    temporizador = TemporizadorSimples()
    temporizador.iniciar()
    # converter para numpy
    matC = multiplicacao_paralela_local(matA, matB, num_workers)

    
    #matA = np.array(matA, dtype=np.float64)
    #matB = np.array(matB, dtype=np.float64)
    #set_num_threads(num_workers)
    #_ = multiplicacao_numba(matA[:2, :2], matB[:2, :2])
    #temporizador.iniciar()
    #matC = multiplicacao_numba(matA, matB)
    
    matC = matC.tolist()
    tempo_clock, tempo_cpu = temporizador.parar()

    # Salvar matriz resultante
    path_matC = f"{args.outdir}/matC.txt"
    with open(path_matC, "w") as f:
        for i, linha in enumerate(matC):
            if i > 0:
                f.write("\n")
            f.write(" ".join(f"{valor:.4f}" for valor in linha))

    # Calcular hash e salvar
    h = sha256_of_file(path_matC)
    save_hash(h, f"{args.outdir}/hash.txt")

    # Salvar log
    cabecalho = ["modo","num_processos","tempo_clock","tempo_cpu","tempo_comunicacao","tempo_total","timestamp","notas"]
    linha_log = ["paralelo_local", num_workers, f"{tempo_clock:.6f}", f"{tempo_cpu:.6f}", 0.0, f"{tempo_clock:.6f}", agora_ts(), ""]
    adicionar_log(f"{args.outdir}/run_logs.csv", linha_log, cabecalho)

    print("Multiplicação local paralela concluída.")
    print("Workers:", num_workers)
    print("Tempo (clock):", tempo_clock, "CPU:", tempo_cpu)
    horas = int(tempo_clock // 3600)
    minutos = int((tempo_clock % 3600) // 60)
    segundos = tempo_clock % 60
    print(f"Tempo real: {horas}h {minutos}min {segundos:.2f}s")
    print("Hash:", h)
    '''
    hash_result = f"{args.outdir}/hash_result.txt"
    with open(hash_result, "r") as f:
        expected_hash = f.read().strip()
    if h == expected_hash:
        print("Hash confere com o esperado.")
    else:
        print("Hash NÃO confere com o esperado.")
    '''

if __name__ == "__main__":
    main()