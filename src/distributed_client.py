import argparse
import time
from pathlib import Path
from weakref import proxy
import Pyro5.api
import numpy as np
import csv
import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(dirname(dirname(__file__))))
from utils.hash_check import sha256_of_file, save_hash

def agora_ts():
    # Retorna timestamp atual formatado como YYYY-MM-DD HH:MM:SS
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def adicionar_log(caminho_csv, linha, cabecalho=None):
    
    # Adiciona uma linha em arquivo CSV.
    # Se o arquivo não existir e cabecalho for fornecido, escreve o cabeçalho primeiro.
    
    p = Path(caminho_csv)
    p.parent.mkdir(parents=True, exist_ok=True)
    escrever_cabecalho = not p.exists()
    with open(p, "a", newline="", encoding="utf8") as f:
        escritor = csv.writer(f)
        if escrever_cabecalho and cabecalho:
            escritor.writerow(cabecalho)
        escritor.writerow(linha)

def truncar4_array(arr):
    # Trunca valores de uma matriz para 4 casas decimais
    return [[int(valor * 10000) / 10000 for valor in linha] for linha in arr]

def dividir_blocos(matA, num_blocos):
    # Divide as linhas da matriz em blocos de forma uniforme
    total_linhas = len(matA)
    blocos = []
    linhas_por_bloco = total_linhas // num_blocos
    resto = total_linhas % num_blocos
    inicio = 0
    for i in range(num_blocos):
        fim = inicio + linhas_por_bloco + (1 if i < resto else 0)
        blocos.append(matA[inicio:fim])
        inicio = fim
    return blocos

def multiplicar_matriz_for(linhas_A, matriz_B):
    # Multiplicação de matrizes usando loops
    num_linhas = len(linhas_A)
    num_colunas = len(matriz_B[0])
    num_elem = len(matriz_B)
    resultado = [[0.0 for _ in range(num_colunas)] for _ in range(num_linhas)]
    for i in range(num_linhas):
        for j in range(num_colunas):
            for k in range(num_elem):
                resultado[i][j] += linhas_A[i][k] * matriz_B[k][j]
    return resultado

def multiplicacao_distribuida(matA, matB, uris_backends):
    
    # uris_backends: lista de URIs Pyro (strings)
    # retorna matC, estatísticas (clock, cpu, comunicação)
    
    num_servidores = len(uris_backends)
    blocos = dividir_blocos(matA, num_servidores)

    # medir tempo de comunicação + computação separadamente
    tempo_total_comunicacao = 0.0
    tempo_total_computacao = 0.0

    resultados_blocos = [None] * len(uris_backends)

    # medimos tempo total da operação
    inicio_clock = time.time()
    inicio_cpu = time.process_time()

    for i, uri in enumerate(uris_backends):
        print(f"\tConectando ao servidor {uri}...")
        proxy = Pyro5.api.Proxy(uri)
        # envia bloco e matB para cálculo remoto
        print(f"\tEnviando bloco {i} para servidor {uri}...")
        inicio_chamada = time.time()
        res = proxy.multiplicar_linhas(blocos[i], matB)
        fim_chamada = time.time()
        tempo_total_comunicacao += (fim_chamada - inicio_chamada)
        resultados_blocos[i] = res  # já é lista de listas

    fim_clock = time.time()
    fim_cpu = time.process_time()
    tempo_clock = fim_clock - inicio_clock
    tempo_cpu = fim_cpu - inicio_cpu

    # juntar resultados
    matC = []
    for bloco in resultados_blocos:
        matC.extend(bloco)

    return matC, tempo_clock, tempo_cpu, tempo_total_comunicacao

def main():
    servers = [
        "PYRONAME:NameServer@192.168.1.2"
        #"PYRONAME:NameServer@10.151.56.46"
        #"PYRONAME:NameServer@192.168.1.10",
    ]
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--matdir", default="data", help="diretório das matrizes")
    parser.add_argument("--outdir", default="results", help="diretório de saída")
    parser.add_argument("--backends", nargs="+", required=True, help="lista de URIs Pyro backend ou PYRONAME:...")
    parser.add_argument("--ns-host", default="192.168.1.2", help="host do nameserver Pyro (opcional)")
    args = parser.parse_args()

    try:
        Pyro5.config.NS_HOST = args.ns_host
    except Exception:
        pass

    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    # Carregar matrizes
    A = []
    B = []
    with open(f"{args.matdir}/matA.txt", "r") as f:
        for linha in f:
            A.append([float(x) for x in linha.strip().split()])
    with open(f"{args.matdir}/matB.txt", "r") as f:
        for linha in f:
            B.append([float(x) for x in linha.strip().split()])
            
    # Resolver URIs backend e multiplicação distribuída
    matC, tempo_clock, tempo_cpu, tempo_comunicacao = multiplicacao_distribuida(A, B, args.backends)

    matC = truncar4_array(matC)
    out_path = f"{args.outdir}/matC.txt"

    # Salvar resultado
    with open(out_path, "w") as f:
        for linha in matC:
            f.write(" ".join(f"{valor:.4f}" for valor in linha) + "\n")

    # Calcular hash e salvar
    h = sha256_of_file(out_path)
    save_hash(h, f"{args.outdir}/hash.txt")

    # Salvar log
    cabecalho = ["modo","num_processos","tempo_clock","tempo_cpu","tempo_comunicacao","tempo_total","timestamp","notas"]
    linha_log = ["distribuido", len(args.backends), f"{tempo_clock:.6f}", f"{tempo_cpu:.6f}", f"{tempo_comunicacao:.6f}", f"{tempo_clock:.6f}", agora_ts(), ""]
    adicionar_log(f"{args.outdir}/run_logs.csv", linha_log, cabecalho)

    print("Multiplicação distribuída concluída.")
    print("Backends:", args.backends)
    print("Tempo clock:", tempo_clock, "Tempo CPU:", tempo_cpu, "Tempo comunicação:", tempo_comunicacao)
    print("SHA256:", h)

if __name__ == "__main__":
    main()
