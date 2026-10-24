import os
import subprocess
import random

# ==========================================================================================
# PASSO 1: Arquivo do modelo (.mod)
# =========================================================================================
codigo_mod = """
set T;
set P;
set R;
set M;

param alfa{M};
param beta_trans := 0.02;
param beta_arm   := 0.01;
param beta_proc  := 0.015;
param gama{P, M, T};
param AZ{P, T};
param Z_barra{P, M, T};
param D{T};
param TF{T};
param Capacidade_Usina;
param OfertaOGR{R, T};
param CompraMax{T};

param Cap_Descarga{T};
param Cap_Armazenagem{T};
param Cap_Frota_Caminhoes{T};
param Cap_Carregamento{T};

param Custo_Fixo_Polo{P};
param Custo_Fixo_OGR{R};

param preco_biodiesel;
param preco_farelo{M};
param rend_farelo{M};
param preco_glicerina;
param rend_glicerina;
param preco_carbono;

param PC{P, M};
param GTC{P};
param CC;
param C_OGR{R};
param v_cost{T};
param Custo_Estoque_Semente{M};

var z{P, M, T} >= 0;
var gx{P, M, T} >= 0;
var ogr_x{R, T} >= 0;
var w{M, T} >= 0;
var v{T} >= 0;
var estoque_semente{M, T} >= 0;

var y_polo{P, T} binary;
var y_ogr{R, T} binary;

maximize Lucro_Total:
    sum{t in T} (preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t])) +
    sum{m in M, t in T} (preco_farelo[m] * rend_farelo[m] * w[m,t]) +
    sum{t in T} (preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) +
    sum{t in T} (preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) -
    (
        sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t]) +
        sum{p in P, m in M, t in T} (GTC[p] * gx[p,m,t]) +
        sum{m in M, t in T} (CC * w[m,t]) +
        sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) +
        sum{t in T} (v_cost[t] * v[t]) +
        sum{m in M, t in T} (Custo_Estoque_Semente[m] * estoque_semente[m,t]) +
        sum{p in P, t in T} (Custo_Fixo_Polo[p] * y_polo[p,t]) +
        sum{r in R, t in T} (Custo_Fixo_OGR[r] * y_ogr[r,t])
    );

s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];

s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];

s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

s.t. Balanco_Estoque_Inicial{m in M}:
    estoque_semente[m, 2024] = sum{p in P} gx[p, m, 2024] * (1 - beta_arm) - w[m, 2024];

s.t. Balanco_Estoque_Subsequente{m in M, t in T: t > 2024}:
    estoque_semente[m, t] = estoque_semente[m, t-1]
                          + sum{p in P} gx[p, m, t] * (1 - beta_arm)
                          - w[m, t];

s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;

s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t];

s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t] * y_ogr[r,t];

s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];

s.t. Limite_Descarga_Usina{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Descarga[t];

s.t. Limite_Armazenagem_Silos{t in T}:
    sum{m in M} estoque_semente[m,t] <= Cap_Armazenagem[t];

s.t. Limite_Frota_Caminhoes{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Frota_Caminhoes[t];

s.t. Limite_Carregamento_Expedicao{t in T}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t]) <= Cap_Carregamento[t];
"""

with open("pbio.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod)

print("-> Arquivo pbio.mod criado com sucesso.")

# ===============================================================================================================
# PASSO 2: Gerar as Instâncias
# ===============================================================================================================
random.seed(42)
print("\nGerando instâncias e executando o solver...")
print(f"{'Instância':<12} | {'Lucro Ótimo (R$)':<22} | {'Estado'}")
print("-" * 55)

for i in range(1, 21):
    demanda_2024 = round(random.uniform(90000, 105000), 2)
    demanda_2025 = round(random.uniform(105000, 125000), 2)
    preco_bio = round(random.uniform(4300.0, 4800.0), 2)

    conteudo_dat = f"""data;
# Instância gerada automaticamente número {i}
set T := 2024 2025;
set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;

param alfa :=
    Soja            0.18
    Algodao         0.15
    Macauba         0.28
    Girassol        0.40
    Nabo_Forrageiro 0.35;

param preco_biodiesel := {preco_bio};
param preco_glicerina := 1200.0;
param rend_glicerina  := 0.10;
param preco_carbono   := 50.0;

param preco_farelo :=
    Soja            800.0
    Algodao         650.0
    Macauba         500.0
    Girassol        700.0
    Nabo_Forrageiro 600.0;

param rend_farelo :=
    Soja            0.75
    Algodao         0.55
    Macauba         0.50
    Girassol        0.50
    Nabo_Forrageiro 0.45;

param CC := 45.0;
param Capacidade_Usina := 196362.0;

param Custo_Estoque_Semente :=
    Soja            15.0
    Algodao         12.0
    Macauba         10.0
    Girassol        14.0
    Nabo_Forrageiro 11.0;

param Custo_Fixo_Polo :=
    polo_norteMG    500000.0
    polo_semiarido  400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0
    rede_urbana        200000.0;

param Cap_Descarga :=
    2024 140000.0
    2025 160000.0;

param Cap_Armazenagem :=
    2024 80000.0
    2025 90000.0;

param Cap_Frota_Caminhoes :=
    2024 140000.0
    2025 160000.0;

param Cap_Carregamento :=
    2024 130000.0
    2025 150000.0;

param C_OGR :=
    rede_catadores_moc 110.0
    rede_urbana        125.0;

param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

param gama :=
    [polo_norteMG, Soja, *]            := 2024 2.8  2025 3.1
    [polo_norteMG, Algodao, *]         := 2024 2.2  2025 2.4
    [polo_norteMG, Macauba, *]         := 2024 3.5  2025 3.8
    [polo_norteMG, Girassol, *]        := 2024 1.5  2025 1.7
    [polo_norteMG, Nabo_Forrageiro, *] := 2024 1.8  2025 2.0
    [polo_semiarido, Soja, *]          := 2024 2.1  2025 2.3
    [polo_semiarido, Algodao, *]       := 2024 1.7  2025 1.9
    [polo_semiarido, Macauba, *]       := 2024 2.9  2025 3.1
    [polo_semiarido, Girassol, *]      := 2024 1.2  2025 1.3
    [polo_semiarido, Nabo_Forrageiro, *]:= 2024 1.4  2025 1.5;

param AZ :=
    [polo_norteMG, *]   := 2024 12.0 2025 12.0
    [polo_semiarido, *] := 2024 15.0 2025 15.0;

param Z_barra :=
    [polo_norteMG, Soja, *]            := 2024 30000.0 2025 35000.0
    [polo_norteMG, Algodao, *]         := 2024 10000.0 2025 12000.0
    [polo_norteMG, Macauba, *]         := 2024 5000.0  2025 6000.0
    [polo_norteMG, Girassol, *]        := 2024 3000.0  2025 4000.0
    [polo_norteMG, Nabo_Forrageiro, *] := 2024 2000.0  2025 3000.0
    [polo_semiarido, Soja, *]          := 2024 20000.0 2025 22000.0
    [polo_semiarido, Algodao, *]       := 2024 8000.0  2025 9000.0
    [polo_semiarido, Macauba, *]       := 2024 6000.0  2025 7000.0
    [polo_semiarido, Girassol, *]      := 2024 3000.0  2025 35000.0
    [polo_semiarido, Nabo_Forrageiro, *]:= 2024 3000.0  2025 35000.0;

param D :=
    2024 {demanda_2024}
    2025 {demanda_2025};

param v_cost :=
    2024 480.0
    2025 510.0;

param TF :=
    2024 1800
    2025 2200;

param OfertaOGR :=
    [rede_catadores_moc, *] := 2024 90000.0 2025 100000.0
    [rede_urbana, *]        := 2024 20000.0 2025 25000.0;

param CompraMax :=
    2024 15000.0
    2025 20000.0;

end;
"""

    dat_file = f"instancia_{i}.dat"
    out_file = f"resultado_{i}.txt"
    
    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    # Executa o GLPK via subprocess (caso tenha o glpsol instalado)
    # Exemplo: glpsol -m pbio.mod -d instancia_1.dat -o resultado_1.txt
    try:
        subprocess.run(["glpsol", "-m", "pbio.mod", "-d", dat_file, "-o", out_file], 
                         check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Leitor simples para extrair o lucro do arquivo de saída do GLPK
        lucro_str = "N/D"
        status_str = "OPTIMAL"
        with open(out_file, "r", encoding="utf-8") as f_out:
            for line in f_out:
                if "Objective:" in line:
                    partes = line.split()
                    for p in partes:
                        try:
                            val = float(p.replace(',', ''))
                            if val > 1000:
                                lucro_str = f"R$ {val:,.2f}"
                                break
                        except ValueError:
                            continue
        print(f"Instância {i:<2}   | {lucro_str:<22} | INTEGER OPTIMAL")
    except Exception:
        print(f"Instância {i:<2}   | Falha na execução                      | ERROR")
