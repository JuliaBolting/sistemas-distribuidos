import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from src.utils.hash_check import sha256_of_file, save_hash
from src.utils.timer import TemporizadorSimples, adicionar_log, agora_ts

def truncar_4digitos(matriz):
    # Trunca valores da matriz para 4 casas decimais
    matriz_truncada = []
    for linha in matriz:
        nova_linha = [int(valor * 10000) / 10000 for valor in linha]
        matriz_truncada.append(nova_linha)
    return matriz_truncada

def multiplicar_linha(args):
    # Calcula produto de uma linha com a matriz B
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
    with open(f"{args.matdir}/matA_linear.txt", "r") as f:
        for linha in f:
            matA.append([float(x) for x in linha.strip().split()])
    with open(f"{args.matdir}/matB_linear.txt", "r") as f:
        for linha in f:
            matB.append([float(x) for x in linha.strip().split()])

    num_workers = args.workers or multiprocessing.cpu_count()

    # Multiplicação paralela e medição de tempo
    temporizador = TemporizadorSimples()
    temporizador.iniciar()
    matC = multiplicacao_paralela_local(matA, matB, num_workers)
    tempo_clock, tempo_cpu = temporizador.parar()

    # Truncar resultados
    matC = truncar_4digitos(matC)

    # Salvar matriz resultante
    path_matC = f"{args.outdir}/matC.txt"
    with open(path_matC, "w") as f:
        for linha in matC:
            f.write(" ".join(f"{valor:.4f}" for valor in linha) + "\n")

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
    print("Hash:", h)

if __name__ == "__main__":
    main()