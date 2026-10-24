import os
import subprocess
import random

# ==========================================================================================
# PASSO 1: Criar o arquivo do modelo (Versão 1 Minimização de Custos) (.mod)
# ==========================================================================================
codigo_mod = """
set T; 
set P; 
set R; 

param alfa;                     
param gama{P, T};               
param AZ{P, T};                    
param Z_barra{P, T};            
param D{T};                        
param TF{T};                       

param PC{P};                     
param GTC{P};                    
param CC;                        
param C_OGR{R};                  
param v_cost{T};                 

var z{P, T} >= 0;               
var gx{P, T} >= 0;              
var ogr_x{R, T} >= 0;              
var w{T} >= 0;                  
var v{T} >= 0;                     

minimize Custo_Total:
    sum{p in P, t in T} (PC[p] * z[p,t]) +      
    sum{p in P, t in T} (GTC[p] * gx[p,t]) +    
    sum{t in T} (CC * w[t]) +                   
    sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) + 
    sum{t in T} (v_cost[t] * v[t]);             

s.t. Atendimento_Demanda{t in T}:
    (alfa * w[t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];

s.t. Limite_Area_Disponivel{p in P, t in T}:
    z[p,t] <= Z_barra[p,t];

s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P} (z[p,t] / AZ[p,t]) >= TF[t];

s.t. Balanco_Massa_Agricola{p in P, t in T}:
    gx[p,t] = gama[p,t] * z[p,t];

s.t. Capacidade_Trituracao{t in T}:
    w[t] = sum{p in P} gx[p,t];

s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t];
"""

with open("pbio_versao1.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod)

print("-> Arquivo pbio_versao1.mod (Versão 1) criado com sucesso.")

# ==========================================================================================
# PASSO 2: Gerar as Instâncias por Porte e Executar o Solver
# ==========================================================================================
random.seed(42)
print("\nGerando instâncias (Pequeno, Médio, Grande) e executando o solver...")
print(f"{'Instância':<15} | {'Porte':<10} | {'Custo Ótimo (R$)':<22} | {'Estado'}")
print("-" * 68)

for i in range(1, 21):
    if i <= 6:
        porte = "Pequeno"
        fator = 0.6  
    elif i <= 14:
        porte = "Médio"
        fator = 1.0  
    else:
        porte = "Grande"
        fator = 1.4  

    demanda_2024 = round(random.uniform(90000, 105000) * fator, 2)
    demanda_2025 = round(random.uniform(105000, 125000) * fator, 2)

    oferta_ogr_1 = 90000.0 * fator
    oferta_ogr_2 = 20000.0 * fator
    oferta_ogr_1_25 = 100000.0 * fator
    oferta_ogr_2_25 = 25000.0 * fator

    conteudo_dat = f"""data;
# Instância {i} - Porte: {porte} (Versão 1)
set T := 2024 2025;
set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;

param alfa := 0.19;

param CC := 45.0;

param C_OGR :=
    rede_catadores_moc 110.0
    rede_urbana        125.0;

param PC :=
    polo_norteMG    145.0
    polo_semiarido  165.0;

param GTC := 
    polo_norteMG    18.0 
    polo_semiarido  25.0;

param gama :=
    [polo_norteMG, *]   := 2024 2.5  2025 2.8
    [polo_semiarido, *] := 2024 1.8  2025 2.0;

param AZ :=
    [polo_norteMG, *]   := 2024 12.0 2025 12.0
    [polo_semiarido, *] := 2024 15.0 2025 15.0;

param Z_barra :=
    [polo_norteMG, *]   := 2024 {45000.0 * fator} 2025 {50000.0 * fator}
    [polo_semiarido, *] := 2024 {35000.0 * fator} 2025 {40000.0 * fator};

param D :=
    2024 {demanda_2024}
    2025 {demanda_2025};

param v_cost :=
    2024 480.0
    2025 510.0;

param TF :=
    2024 1800
    2025 2200;

end;
"""

    dat_file = f"instancia_{i}.dat"
    out_file = f"resultado_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_versao1.mod", "-d", dat_file, "-o", out_file],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        custo_str = "N/D"
        with open(out_file, "r", encoding="utf-8") as f_out:
            for line in f_out:
                if "Objective:" in line:
                    partes = line.split()
                    for p in partes:
                        try:
                            val = float(p.replace(',', ''))
                            if val >= 0:
                                custo_str = f"R$ {val:,.2f}"
                                break
                        except ValueError:
                            continue
        print(f"Instância {i:<2} ({porte:<8}) | {custo_str:<22} | OPTIMAL")
    except Exception:
        print(f"Instância {i:<2} ({porte:<8}) | Falha na execução                  | ERROR")
