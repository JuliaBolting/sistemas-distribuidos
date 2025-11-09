import argparse
import time
from pathlib import Path
import Pyro5.api
import numpy as np
import csv
import sys
from os.path import dirname, abspath
sys.path.insert(0, abspath(dirname(dirname(__file__))))
from utils.hash_check import sha256_of_file, save_hash
import argparse
import gzip
import gzip
import pickle

# Envia B inteira comprimida para o servidor para a multiplicação
def enviar_B_compressa(proxy, matB):
    dados = pickle.dumps(matB, protocol=4)
    dados_zip = gzip.compress(dados)

    print(f"Enviando matriz B comprimida ({len(dados_zip)/1024/1024:.2f} MB)")
    proxy.set_matriz_B_compressa(dados_zip)

# Define onde o nameserver está rodando e quais backends usar
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backends", nargs="+", required=True)
    parser.add_argument("--ns-host", required=True)
    return parser.parse_args()

# Retorna timestamp atual formatado como YYYY-MM-DD HH:MM:SS
def agora_ts():
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

# Realiza a multiplicação distribuída de matrizes
def multiplicacao_distribuida(matA, matB, uris_backends):

    num_servidores = len(uris_backends)
    blocos = dividir_blocos(matA, num_servidores)

    tempo_total_comunicacao = 0.0
    resultados_blocos = [None] * num_servidores

    inicio_clock = time.time()
    inicio_cpu = time.process_time()

    proxies = []
    for uri in uris_backends:
        print(f"\tConectando ao servidor {uri}...")
        p = Pyro5.api.Proxy(uri)
        enviar_B_compressa(p, matB)
        print(f"\tEnviando matriz B para servidor {uri}...")
        proxies.append(p)

    for i, p in enumerate(proxies):
        print(f"\tEnviando bloco {i} para servidor...")
        inicio_chamada = time.time()
        res = p.multiplicar_linhas(blocos[i])
        fim_chamada = time.time()
        tempo_total_comunicacao += (fim_chamada - inicio_chamada)
        resultados_blocos[i] = res

    fim_clock = time.time()
    fim_cpu = time.process_time()

    tempo_clock = fim_clock - inicio_clock
    tempo_cpu = fim_cpu - inicio_cpu

    # Juntar resultados
    matC = []
    for bloco in resultados_blocos:
        matC.extend(bloco)

    return matC, tempo_clock, tempo_cpu, tempo_total_comunicacao

def main():
    args = parse_args()
    ns_host = args.ns_host
    backends = args.backends

    print("\n========== Cliente Distribuído ==========")
    print("NS Host:", ns_host)
    print("Backends:", backends)

    # Resolve backend URIs via NameServer
    Pyro5.api.locate_ns(host=ns_host)
    
    uris = [f"{be}@{ns_host}" if not be.startswith("PYRONAME:") else be for be in backends]

    print("\nCarregando matrizes A e B...")
    matrix_dir = "data"
    matA = np.loadtxt(f"{matrix_dir}/matA.txt").tolist()
    matB = np.loadtxt(f"{matrix_dir}/matB.txt").tolist()
    print("Matrizes carregadas com sucesso!")

    print("\nIniciando multiplicação distribuída...")
    matC, tempo_clock, tempo_cpu, tempo_com = multiplicacao_distribuida(matA, matB, uris)
    
    path_matC = "data/matC.txt"
    with open(path_matC, "w") as f:
        for i, linha in enumerate(matC):
            if i > 0:
                f.write("\n")
            f.write(" ".join(f"{valor:.4f}" for valor in linha))

    print("\nMultiplicação finalizada!")
    print(f"Tempo Clock: {tempo_clock:.2f}s")
    print(f"Tempo CPU: {tempo_cpu:.2f}s")
    print(f"Tempo Comunicação: {tempo_com:.2f}s")
    
    h = sha256_of_file(path_matC)
    save_hash(h, f"{args.outdir}/hash.txt")
    
    # Salvar log
    cabecalho = ["modo","num_processos","tempo_clock","tempo_cpu","tempo_comunicacao","tempo_total","timestamp","notas"]
    linha_log = ["paralelo_local", 2, f"{tempo_clock:.6f}", f"{tempo_cpu:.6f}", 0.0, f"{tempo_clock:.6f}", agora_ts(), ""]
    adicionar_log(f"{args.outdir}/run_logs.csv", linha_log, cabecalho)

    print("\nResultado salvo em matC.txt")

if __name__ == "__main__":
    main()
