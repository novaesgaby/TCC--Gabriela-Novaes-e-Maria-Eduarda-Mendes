import shutil
import subprocess

if not shutil.which("glpsol"):
    print("⚙️ GLPK não encontrado. Instalando glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ GLPK instalado com sucesso!")
else:
    print("✅ GLPK já está instalado e pronto para uso.")
