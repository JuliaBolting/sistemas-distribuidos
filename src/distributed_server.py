import argparse
import Pyro5.api
from pathlib import Path

@Pyro5.api.expose
class CalculadoraMatriz(object):
    def multiplicar_linhas(self, linhas_A, matriz_B):
        """
        linhas_A: lista de linhas (bloco da submatriz A)
        matriz_B: matriz completa B
        retorna: lista de listas (linhas do resultado para essas linhas)
        """
        # Obter dimensões das matrizes
        num_linhas = len(linhas_A)
        num_colunas = len(matriz_B[0])
        num_elem = len(matriz_B)

        # Inicializa a matriz de resultado com zeros
        resultado = [[0.0 for _ in range(num_colunas)] for _ in range(num_linhas)]

        # Multiplicação de matrizes usando loops
        for i in range(num_linhas):
            for j in range(num_colunas):
                for k in range(num_elem):
                    resultado[i][j] += linhas_A[i][k] * matriz_B[k][j]

        return resultado

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="host para vincular o daemon Pyro")
    parser.add_argument("--port", type=int, default=0, help="porta do daemon (0=auto)")
    parser.add_argument("--name", required=True, help="nome Pyro para registrar (único por servidor)")
    parser.add_argument("--ns-host", default=None, help="host do nameserver Pyro (se houver)")
    args = parser.parse_args()

    # Criar daemon
    daemon = Pyro5.server.Daemon(host=args.host, port=args.port)
    uri = daemon.register(CalculadoraMatriz)

    if args.ns_host:
        ns = Pyro5.api.locate_ns(host=args.ns_host)
        ns.register(args.name, uri)
        print(f"Nome registrado {args.name} -> {uri} no nameserver {args.ns_host}")
    else:
        # Registrar usando URI direta
        print(f"Nenhum nameserver fornecido. Use este URI para criar proxy: {uri}")

    print("Servidor pronto. Escutando em", daemon.locationStr)

    try:
        daemon.requestLoop()
    finally:
        daemon.shutdown()

if __name__ == "__main__":
    main()
