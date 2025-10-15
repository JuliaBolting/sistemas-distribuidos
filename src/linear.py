import argparse
from pathlib import Path
from src.utils.hash_check import sha256_of_file, save_hash
from src.utils.timer import TemporizadorSimples, adicionar_log, agora_ts

def truncar_4digitos(matriz):
    # Trunca valores da matriz para 4 casas decimais
    matriz_truncada = []
    for linha in matriz:
        nova_linha = [int(valor * 10000) / 10000 for valor in linha]
        matriz_truncada.append(nova_linha)
    return matriz_truncada

def multiplicacao_linear_for(matA, matB):
    # Multiplicação de matrizes usando loops for
    num_linhas = len(matA)
    num_colunas = len(matB[0])
    num_elem = len(matB)
    resultado = [[0.0 for _ in range(num_colunas)] for _ in range(num_linhas)]
    for i in range(num_linhas):
        for j in range(num_colunas):
            for k in range(num_elem):
                resultado[i][j] += matA[i][k] * matB[k][j]
    return resultado

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matdir", default="data", help="Diretório das matrizes")
    parser.add_argument("--outdir", default="results", help="Diretório de saída")
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

    # Multiplicação linear e medição de tempo
    temporizador = TemporizadorSimples()
    temporizador.iniciar()
    matC = multiplicacao_linear_for(matA, matB)
    tempo_clock, tempo_cpu = temporizador.parar()

    # Truncar resultados para 4 casas decimais
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
    linha_log = ["linear", 1, f"{tempo_clock:.6f}", f"{tempo_cpu:.6f}", 0.0, f"{tempo_clock:.6f}", agora_ts(), ""]
    adicionar_log(f"{args.outdir}/run_logs.csv", linha_log, cabecalho)

    print("Multiplicação Linear concluída.")
    print("Tempo (clock):", tempo_clock, "CPU:", tempo_cpu)
    print("Hash:", h)

if __name__ == "__main__":
    main()
