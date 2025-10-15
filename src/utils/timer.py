import time
import csv
from pathlib import Path

def agora_ts():
    # Retorna timestamp atual formatado como YYYY-MM-DD HH:MM:SS
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class TemporizadorSimples:
    # Timer simples para medir tempo de relógio e CPU
    def __init__(self):
        self.tempo_inicial = None
        self.cpu_inicial = None

    def iniciar(self):
        # Inicia o temporizador
        self.tempo_inicial = time.time()
        self.cpu_inicial = time.process_time()

    def parar(self):
        # Para o temporizador e retorna (tempo_relogio, tempo_cpu)
        tempo_final = time.time()
        cpu_final = time.process_time()
        return (tempo_final - self.tempo_inicial, cpu_final - self.cpu_inicial)

def adicionar_log(caminho_csv, linha, cabecalho=None):
    """
    Adiciona uma linha em arquivo CSV.
    Se o arquivo não existir e cabecalho for fornecido, escreve o cabeçalho primeiro.
    """
    p = Path(caminho_csv)
    p.parent.mkdir(parents=True, exist_ok=True)
    escrever_cabecalho = not p.exists()
    with open(p, "a", newline="", encoding="utf8") as f:
        escritor = csv.writer(f)
        if escrever_cabecalho and cabecalho:
            escritor.writerow(cabecalho)
        escritor.writerow(linha)
