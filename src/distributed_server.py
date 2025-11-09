import argparse
import Pyro5.api
from pathlib import Path
from benchmark import run_benchmark
import time
from numba import njit
import gzip, pickle
from Pyro5.api import SerializedBlob
import base64
from numba.typed import List

@njit(cache=True, fastmath=True)
def multiplicar_numba(A, B):
    # A e B chegam como numba.typed.List(List(float64))
    num_linhas = len(A)
    num_colunas = len(B[0])
    num_elem = len(B)

    # pré-aloca resultado como lista de listas
    resultado = [[0.0 for _ in range(num_colunas)] for _ in range(num_linhas)]

    for i in range(num_linhas):
        for j in range(num_colunas):
            soma = 0.0
            for k in range(num_elem):
                soma += A[i][k] * B[k][j]
            resultado[i][j] = soma
        print(f"  Linha {i+1}/{num_linhas} processada.")
    return resultado

def to_typed_2d(py2d):
    out = List()
    for row in py2d:
        r = List()
        for v in row:
            r.append(float(v))
        out.append(r)
    return out

@Pyro5.api.expose
class CalculadoraMatriz(object):
    def __init__(self):
            self.matriz_B = None
            self.nome = "Servidor"

    def set_nome(self, nome):
        self.nome = nome

    @Pyro5.api.expose
    def set_matriz_B_compressa(self, dados_zip):
        # Normalmente já será bytes por causa do SERIALIZER="pickle"
        if isinstance(dados_zip, (bytes, bytearray)):
            raw = dados_zip
        elif isinstance(dados_zip, dict):  # fallback se vier do serpent como dict base64
            if "data" in dados_zip:
                raw = base64.b64decode(dados_zip["data"])
            elif "py/b64" in dados_zip:
                raw = base64.b64decode(dados_zip["py/b64"])
            else:
                raise TypeError(f"Dict inesperado: chaves={list(dados_zip.keys())}")
        else:
            raise TypeError(f"Esperado bytes, recebi: {type(dados_zip)}")

        print(f"[{self.nome}] Recebendo matriz B comprimida: {len(raw)/1024/1024:.2f} MB")
        dados = gzip.decompress(raw)
        B_py = pickle.loads(dados)          # lista de listas “normal” (Python)
        self.matriz_B = B_py                # mantém se quiser inspecionar/printar
        self.matriz_B_nb = to_typed_2d(B_py)  # ✅ versão tipada p/ Numba
        print(f"[{self.nome}] B descomprimida! Dim: {len(B_py)} x {len(B_py[0])}")
        return True

    def set_matriz_B(self, matriz_B):
        print(f"[{self.nome}] Matriz B recebida! Dimensões: {len(matriz_B)} x {len(matriz_B[0])}")
        self.matriz_B = matriz_B
        return True

    def multiplicar_linhas(self, linhas_A):
        if getattr(self, "matriz_B_nb", None) is None:
            raise RuntimeError("Matriz B não foi definida ainda.")

        print(f"\n[{self.nome}] Recebido bloco com {len(linhas_A)} linhas de A para multiplicar...")
        inicio = time.time()

        A_nb = to_typed_2d(linhas_A)         # ✅ bloco A tipado
        print(f"[{self.nome}] Bloco A convertido para typed.List para Numba.")
        C_nb = multiplicar_numba(A_nb, self.matriz_B_nb)

        fim = time.time()
        print(f"[{self.nome}] Bloco multiplicado com Numba! Tempo: {fim - inicio:.3f}s ✅\n")

        # Pyro não deve trafegar typed.List; converta pra listas Python:
        C_py = [list(row) for row in C_nb]
        return C_py


def main():
    print("Iniciando servidor de cálculo de matrizes...")

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="host para vincular o daemon Pyro")
    parser.add_argument("--port", type=int, default=0, help="porta do daemon (0=auto)")
    parser.add_argument("--name", required=True, help="nome Pyro para registrar (único por servidor)")
    parser.add_argument("--ns-host", default="192.168.1.7", help="host do nameserver Pyro (se houver)")
    args = parser.parse_args()

    # Criar daemon
    daemon = Pyro5.api.Daemon(host=args.host, port=args.port)

    # Criar objeto remoto
    serv = CalculadoraMatriz()
    serv.set_nome(args.name)

    if args.ns_host:
        print(f"Conectando ao nameserver em {args.ns_host}...")
        ns = Pyro5.api.locate_ns(host=args.ns_host)
        uri = daemon.register(serv)
        ns.register(args.name, uri)
        print(f"[{args.name}] Registrado -> {uri}")
    else:
        uri = daemon.register(serv)
        print(f"[{args.name}] Registrado sem NS -> {uri}")

    print(f"[{args.name}] Servidor pronto! Endereço: {daemon.locationStr}\n")

    try:
        daemon.requestLoop()
    finally:
        daemon.shutdown()


if __name__ == "__main__":
    main()