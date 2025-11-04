# AV3 — Multiplicação de Matrizes (Linear / Paralelo Local / Distribuído com Pyro5)

**Disciplina:** Computação Paralela e Distribuída

---

## Objetivo
Implementar e analisar um sistema para multiplicação de matrizes quadradas em três modos:
- Linear (um núcleo);
- Paralelo local (múltiplos núcleos na mesma máquina);
- Paralelo distribuído (múltiplos núcleos em 2+ backends usando Pyro5).

A medição deve **excluir** leitura/escrita de arquivos; salvar `matC.txt` no formato exigido; truncar resultados para 4 casas decimais (sem arredondar). 
A validação é por SHA-256.

---

## Estrutura dos arquivos do projeto
- `src/linear.py` — execução sequencial (1 processo).
- `src/parallel_local.py` — execução local com `multiprocessing` (ProcessPoolExecutor).
- `src/distributed_server.py` — servidor backend (Pyro5).
- `src/distributed_client.py` — frontend (Pyro5) que orquestra backends.
- `src/matrix_generator.py` — (opcional) gera `matA.txt` e `matB.txt`.
- `src/utils/hash_check.py` — utilitário SHA-256 e gravação de `hash.txt`.
- `src/utils/timer.py` — utilitários de medição e logging.
- `data/` — colocar `matA.txt` e `matB.txt`.
- `results/` — saídas: `matC.txt`, logs, `hash.txt`.

---

## Requisitos e instalação
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt
