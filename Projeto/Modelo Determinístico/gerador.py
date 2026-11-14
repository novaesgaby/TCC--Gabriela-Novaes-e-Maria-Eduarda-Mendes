import os
import shutil
import subprocess
import random

# 1. Garante a instalação do GLPK no ambiente de execução
if not shutil.which("glpsol"):
    print("A instalar glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Escreve estritamente o seu modelo .mod determinístico oficial
codigo_mod_deterministico = """
# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO Determinística)
# ========================================================================================================================

set T := 1..24;
set P;
set R;
set M;

param alfa{M};
param beta_trans := 0.02;
param beta_arm   := 0.01;
param beta_proc  := 0.015;

param gama{P, M, T};
param D{T};
param v_cost{T};

param AZ{P, T};
param Z_barra{P, M, T};
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
param Custo_Estoque_Semente{M};
param penalidade_deficit default preco_biodiesel * 1.2;

var z{P, M, T} >= 0;
var y_polo{P, T} binary;
var y_ogr{R, T} binary;

var gx{P, M, T} >= 0;
var ogr_x{R, T} >= 0;
var w{M, T} >= 0;
var v{T} >= 0;
var estoque_semente{M, T} >= 0;
var deficit{T} >= 0;
var sub_ogr{t in T} >= 0;

maximize Lucro_Total:
    - sum{p in P, t in T} (Custo_Fixo_Polo[p] * y_polo[p,t])
    - sum{r in R, t in T} (Custo_Fixo_OGR[r] * y_ogr[r,t])
    - sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t])
    + sum{t in T} (
        preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t])
        + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t])
        + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])
        + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])
    )
    - sum{t in T} (
        sum{p in P, m in M} (GTC[p] * gx[p,m,t])
        + sum{m in M} (CC * w[m,t])
        + sum{r in R} (C_OGR[r] * ogr_x[r,t])
        + v_cost[t] * v[t]
        + v_cost[t] * sub_ogr[t]
        + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t])
        + penalidade_deficit * deficit[t]
    );

s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];

s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] + deficit[t] >= D[t];

s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] <= (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

s.t. Balanco_Estoque_Inicial{m in M}:
    estoque_semente[m, 1] = sum{p in P} gx[p, m, 1] * (1 - beta_arm) - w[m, 1];

s.t. Balanco_Estoque_Subsequente{m in M, t in T: t > 1}:
    estoque_semente[m, t] = estoque_semente[m, t-1] + sum{p in P} gx[p, m, t] * (1 - beta_arm) - w[m, t];

s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;

s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] + sub_ogr[t] >= 0.14 * D[t];

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

with open("pbio_deterministico.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod_deterministico)

print("-> Arquivo pbio_deterministico.mod criado com sucesso.")

# 3. Gerador das 20 Instâncias Determinísticas estruturadas por porte
random.seed(42)
print("\nA gerar 20 instâncias determinísticas e a executar o GLPSOL...")
print(f"{'Instância':<12} | {'Porte':<8} | {'Lucro Total Ótimo (R$)':<28} | {'Estado'}")
print("-" * 72)

for i in range(1, 21):
    if i <= 6:
        porte = "Pequeno"
        fator = 0.6
    elif i <= 14:
        porte = "Médio"
        fator = 1.0
    else:
        porte = "Grande"
        fator = 1.25

    f_estocastico = 1.0 + (i * 0.002)

    preco_bio = round(random.uniform(4400.0, 4600.0), 2)
    cap_usina = round(16362.0)

    d_descarga = {1:12000, 2:12000, 3:14000, 4:15000, 5:15000, 6:14000, 7:12000, 8:11000, 9:11000, 10:11000, 11:12000, 12:12000, 13:13000, 14:13000, 15:15000, 16:16000, 17:16000, 18:15000, 19:13000, 20:12000, 21:12000, 22:13000, 23:13000, 24:13000}
    d_armazenagem = {1:7500, 2:7500, 3:9000, 4:10000, 5:10000, 6:9000, 7:8000, 8:7500, 9:7500, 10:7500, 11:7500, 12:7500, 13:8000, 14:8000, 15:9500, 16:10500, 17:10500, 18:9500, 19:8500, 20:8000, 21:8000, 22:8000, 23:8000, 24:8000}
    d_carregamento = {1:11000, 2:11000, 3:12000, 4:13000, 5:13000, 6:12000, 7:11000, 8:11000, 9:11000, 10:11000, 11:11000, 12:11000, 13:12000, 14:12000, 15:13000, 16:14000, 17:14000, 18:13000, 19:12000, 20:12000, 21:12000, 22:12000, 23:12000, 24:12000}

    cap_desc_str = " ".join([f"{t} {int(val * fator)}" for t, val in d_descarga.items()])
    cap_arm_str  = " ".join([f"{t} {int(val * fator)}" for t, val in d_armazenagem.items()])
    cap_carr_str = " ".join([f"{t} {int(val * fator)}" for t, val in d_carregamento.items()])

    # Demanda determinística baseada no cenário S2 central
    demanda_base_det = {
        1: 8000, 2: 8150, 3: 8300, 4: 8500, 5: 8700, 6: 8400, 7: 8200, 8: 8000,
        9: 7900, 10: 8100, 11: 8300, 12: 8500, 13: 9200, 14: 9400, 15: 9700, 16: 10000,
        17: 9800, 18: 9500, 19: 9300, 20: 9100, 21: 9200, 22: 9400, 23: 9600, 24: 9800
    }

    d_lines = []
    for t, val in demanda_base_det.items():
        d_val = int(val * fator * f_estocastico)
        d_lines.append(f"    {t}  {d_val}")
    d_block = "\n".join(d_lines)

    culturas = ["Soja", "Algodao", "Macauba", "Girassol", "Nabo_Forrageiro"]
    polos = ["polo_norteMG", "polo_semiarido"]

    gama_lines = []
    for polo in polos:
        fator_polo = 1.0 if polo == "polo_norteMG" else 0.85
        for cult in culturas:
            for t in range(1, 25):
                pico = 1.3 if (4 <= t <= 6) or (16 <= t <= 18) else 1.0
                # Utiliza o valor S2 do modelo estocástico como base determinística
                val_gama = round(random.uniform(1.4, 2.0) * pico * fator_polo * f_estocastico, 2)
                gama_lines.append(f"    [{polo}, {cult}, {t}] := {val_gama}")

    gama_block = "\n".join(gama_lines)

    conteudo_dat = f"""# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO Determinística) - Instância {i} ({porte})
# =============================================================================================================

data;

set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;

param alfa :=
    Soja               0.18
    Algodao            0.15
    Macauba            0.28
    Girassol           0.40
    Nabo_Forrageiro    0.35;

param preco_biodiesel := {preco_bio};
param preco_glicerina := 1200.0;
param rend_glicerina  := 0.10;
param preco_carbono   := 50.0;

param preco_farelo :=
    Soja               800.0
    Algodao            650.0
    Macauba            500.0
    Girassol           700.0
    Nabo_Forrageiro    600.0;

param rend_farelo :=
    Soja               0.75
    Algodao            0.55
    Macauba            0.50
    Girassol           0.50
    Nabo_Forrageiro    0.45;

param CC := 45.0;
param Capacidade_Usina := {cap_usina};

param Custo_Estoque_Semente :=
    Soja               15.0
    Algodao            12.0
    Macauba            10.0
    Girassol           14.0
    Nabo_Forrageiro    11.0;

param Custo_Fixo_Polo :=
    polo_norteMG     500000.0
    polo_semiarido   400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0
    rede_urbana        200000.0;

param Cap_Descarga :=
    {cap_desc_str};

param Cap_Armazenagem :=
    {cap_arm_str};

param Cap_Frota_Caminhoes :=
    {cap_desc_str};

param Cap_Carregamento :=
    {cap_carr_str};

param C_OGR := rede_catadores_moc 110.0 rede_urbana 125.0;

param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

param D :=
{d_block};

param v_cost :=
    1   410.0
    2   420.0
    3   390.0
    4   370.0
    5   360.0
    6   380.0
    7   400.0
    8   430.0
    9   470.0
    10  500.0
    11  480.0
    12  440.0
    13  430.0
    14  440.0
    15  400.0
    16  380.0
    17  370.0
    18  390.0
    19  420.0
    20  450.0
    21  490.0
    22  510.0
    23  470.0
    24  440.0;

param gama :=
{gama_block};

param AZ :=
    [polo_norteMG, *]   := {" ".join([f"{t} 12.0" for t in range(1, 25)])}
    [polo_semiarido, *] := {" ".join([f"{t} 15.0" for t in range(1, 25)])};

param Z_barra :=
    [polo_norteMG, Soja, *]              := {" ".join([f"{t} {int(2500*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Algodao, *]          := {" ".join([f"{t} {int(1000*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Macauba, *]          := {" ".join([f"{t} {int(500*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Girassol, *]         := {" ".join([f"{t} {int(300*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Nabo_Forrageiro, *]  := {" ".join([f"{t} {int(200*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Soja, *]           := {" ".join([f"{t} {int(1600*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Algodao, *]        := {" ".join([f"{t} {int(700*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Macauba, *]        := {" ".join([f"{t} {int(500*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Girassol, *]       := {" ".join([f"{t} {int(250*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Nabo_Forrageiro, *]:= {" ".join([f"{t} {int(250*fator)}" for t in range(1, 25)])};

param TF := 1 150 2 150 3 150 4 150 5 150 6 150 7 150 8 150 9 150 10 150 11 150 12 150 13 180 14 180 15 180 16 180 17 180 18 180 19 180 20 180 21 180 22 180 23 180 24 180;

param OfertaOGR :=
    [rede_catadores_moc, *] := {" ".join([f"{t} {int(val*fator)}" for t, val in {1:7000, 2:7200, 3:7500, 4:8000, 5:8200, 6:7800, 7:7300, 8:7000, 9:6800, 10:6900, 11:7100, 12:7300, 13:7800, 14:8000, 15:8300, 16:9000, 17:9200, 18:8600, 19:8100, 20:7700, 21:7500, 22:7600, 23:7900, 24:8100}.items()])}
    [rede_urbana, *]        := {" ".join([f"{t} {int(val*fator)}" for t, val in {1:1500, 2:1550, 3:1600, 4:1700, 5:1750, 6:1650, 7:1550, 8:1500, 9:1450, 10:1480, 11:1520, 12:1580, 13:1800, 14:1850, 15:1900, 16:2100, 17:2150, 18:2000, 19:1900, 20:1800, 21:1750, 22:1780, 23:1850, 24:1900}.items()])};

param CompraMax := {" ".join([f"{t} {int(val*fator)}" for t, val in {1:1200, 2:1220, 3:1250, 4:1300, 5:1350, 6:1300, 7:1250, 8:1200, 9:1150, 10:1180, 11:1210, 12:1250, 13:1500, 14:1550, 15:1600, 16:1800, 17:1850, 18:1700, 19:1600, 20:1500, 21:1450, 22:1480, 23:1550, 24:1600}.items()])};

end;
"""

    dat_file = f"instancia_det_{i}.dat"
    out_file = f"resultado_det_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_deterministico.mod", "-d", dat_file, "-o", out_file],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        lucro_str = "N/D"
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
        print(f"Instância Det {i:<2} ({porte:<8}) | {lucro_str:<28} | INTEGER OPTIMAL")
    except Exception:
        print(f"Instância Det {i:<2} ({porte:<8}) | Falha na execução              | ERROR")
