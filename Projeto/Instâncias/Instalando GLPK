import subprocess
import shutil

# Verifica se o glpsol está instalado, caso contrário instala-o automaticamente no Colab
if not shutil.which("glpsol"):
    print("GLPK não encontrado. Instalando glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Roda apenas a primeira instância para testar capturando erros
resultado = subprocess.run("glpsol -m pbio.mod -d instancia_1.dat -o saida_1.txt", shell=True, capture_output=True, text=True)

if resultado.returncode != 0:
    print("Erro ao executar o GLPK:")
    print(resultado.stderr)
else:
    # Lê e imprime as primeiras 35 linhas do ficheiro gerado pelo GLPK
    try:
        with open("saida_1.txt", "r", encoding="utf-8", errors="ignore") as f:
            linhas = f.readlines()
            for l in linhas[:35]:
                print(l, end="")
    except FileNotFoundError:
        print("Erro: O arquivo 'saida_1.txt' não foi gerado mesmo com a execução do GLPK.")
