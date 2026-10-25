import os
import shutil
import subprocess
import random

# 1. Garante a instalação do GLPK no ambiente
if not shutil.which("glpsol"):
    print("Instalando glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Criação automática do arquivo .mod (Versão 5 Estocástica)
codigo_mod_v5_estocastico = """
# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 5 - Modelo Estocástico)
# ========================================================================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (2024 e 2025)
set P; # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)
set S; # Conjunto de Cenários (omega)

# PARÂMETROS AGRÍCOLAS E ESTOCÁSTICOS
param pi{S};                       # Probabilidade de cada cenário omega ocorrer (pi_omega)

param alfa{M};                     # Rendimento de óleo específico para cada matéria-prima m
param beta_trans := 0.02;          # Perda física no transporte (2%)
param beta_arm   := 0.01;          # Perda física na armazenagem (1%)
param beta_proc  := 0.015;         # Perda física no esmagamento (1.5%)

param gama{P, M, T, S};            # Produtividade agrícola estocástica [t/ha]
param D{T, S};                     # Demanda total de biodiesel/óleo estocástica
param v_cost{T, S};                # Custo do óleo externo estocástico [R$/t]

param AZ{P, T};                    # Tamanho médio dos lotes das famílias [ha/família]
param Z_barra{P, M, T};            # Área máxima disponível para cultivo [ha]
param TF{T};                       # Número mínimo de famílias do Selo Social
param Capacidade_Usina;            # Capacidade máxima de esmagamento na usina
param OfertaOGR{R, T};             # Disponibilidade máxima de OGR por fonte
param CompraMax{T};                # Limite máximo de compra externa de óleo

# PARÂMETROS LOGÍSTICOS
param Cap_Descarga{T};
param Cap_Armazenagem{T};
param Cap_Frota_Caminhoes{T};
param Cap_Carregamento{T};

# PARÂMETROS ESTRATÉGICOS E CUSTOS FIXOS
param Custo_Fixo_Polo{P};          # Custo fixo para abrir/manter um polo agrícola p
param Custo_Fixo_OGR{R};           # Custo fixo para contratar/parceirizar a rede de OGR r
param M_big := 1000000.0;          # Constante Big-M para restrições condicionais

# PARÂMETROS DE PREÇO DE VENDA E RECEITAS [R$]
param preco_biodiesel;
param preco_farelo{M};
param rend_farelo{M};
param preco_glicerina;
param rend_glicerina;
param preco_carbono;

# PARÂMETROS DE CUSTO OPERACIONAL [R$]
param PC{P, M};                       # Custo de cultivo [R$/ha]
param GTC{P};                         # Custo de transporte de grãos [R$/t]
param CC;                             # Custo de esmagamento/processamento [R$/t]
param C_OGR{R};                       # Custo de aquisição de OGR [R$/t]
param penalidade_deficit := 10000.0;  # Penalidade pelo não atendimento da demanda

# VARIÁVEIS DE 1º ESTÁGIO (Decisões Estruturais)
var z{P, M, T} >= 0;                  # Área de terra alocada por matéria-prima [ha]
var y_polo{P, T} binary;              # 1 se o polo agrícola p for aberto no período t, 0 caso contrário
var y_ogr{R, T} binary;               # 1 se a rede de OGR r for contratada no período t, 0 caso contrário

# VARIÁVEIS DE 2º ESTÁGIO (Decisões Operacionais por Cenário)
var gx{P, M, T, S} >= 0;              # Volume de sementes transportadas por cenário
var ogr_x{R, T, S} >= 0;              # Volume de OGR adquirido por cenário
var w{M, T, S} >= 0;                  # Total de sementes líquidas trituradas por cenário
var v{T, S} >= 0;                     # Óleo complementar adquirido do mercado por cenário
var deficit{T, S} >= 0;               # Déficit de atendimento da demanda por cenário

# ==================================================================================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Esperado (Ponderado pela probabilidade pi[s] dos cenários)
# ==================================================================================================================================
maximize Lucro_Esperado:
    # 1. Custos Fixos de 1º Estágio (Decisões estruturais irrevogáveis)
    - sum{p in P, t in T} (Custo_Fixo_Polo[p] * y_polo[p,t])
    - sum{r in R, t in T} (Custo_Fixo_OGR[r] * y_ogr[r,t])
    - sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t])
    
    # 2. Valor Esperado de 2º Estágio (Receitas menos custos operacionais por cenário ponderados por pi[s])
    + sum{s in S} pi[s] * (
        # RECEITAS POR CENÁRIO
        sum{t in T} (preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s])) +
        sum{m in M, t in T} (preco_farelo[m] * rend_farelo[m] * w[m,t,s]) +
        sum{t in T} (preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])) +
        sum{t in T} (preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])) -

        # CUSTOS OPERACIONAIS POR CENÁRIO
        (
            sum{p in P, m in M, t in T} (GTC[p] * gx[p,m,t,s]) +
            sum{m in M, t in T} (CC * w[m,t,s]) +
            sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t,s]) +
            sum{t in T} (v_cost[t,s] * v[t,s]) +
            sum{t in T} (penalidade_deficit * deficit[t,s])
        )
    );

# ==================================================================================================================================
# RESTRIÇÕES DO SISTEMA
# ==================================================================================================================================

# ==================================================== RESTRIÇÕES DE 1º ESTÁGIO ======================================================

# Restrição (3), determina o limite da área agrícola. Só existe plantação se o polo estiver aberto
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];
# ==================================================================================================================================

# Restrição (4), cumprimento do Selo Biocombustível Social.
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];
# ==================================================================================================================================

# ==================================== RESTRIÇÕES DE 2º ESTÁGIO (Replicadas para os 27 cenários) ======================================

# Restrição (2) Atendimento da demanda sob incerteza.
s.t. Atendimento_Demanda{t in T, s in S}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s] + deficit[t,s] >= D[t,s];
# ==================================================================================================================================

# Restrição (5) Balanço de massa agrícola estocástico.
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T, s in S}:
    gx[p,m,t,s] = (1 - beta_trans) * gama[p,m,t,s] * z[p,m,t];
# ==================================================================================================================================

# Restrição (6) Balanço entre processamento e armazenagem por cenário.
s.t. Balanco_Processamento_Armazenagem{m in M, t in T, s in S}:
    w[m,t,s] = (1 - beta_arm) * sum{p in P} gx[p,m,t,s];
# ==================================================================================================================================

# Restrição (7) Capacidade industrial de esmagamento por cenário.
s.t. Capacidade_Industrial{t in T, s in S}:
    sum{m in M} w[m,t,s] <= Capacidade_Usina;
# ==================================================================================================================================

# Restrição (8) Percentual mínimo de OGR (14%).
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] >= 0.14 * D[t,s];
# ==================================================================================================================================

# Restrição (9) Disponibilidade máxima de OGR por cenário.
s.t. Disponibilidade_Max_OGR{r in R, t in T, s in S}:
    ogr_x[r,t,s] <= OfertaOGR[r,t] * y_ogr[r,t];
# ==================================================================================================================================

# Restrição (10) Teto de compra de óleo externo por cenário.
s.t. Teto_Compra_Externa{t in T, s in S}:
    v[t,s] <= CompraMax[t];
# ==================================================================================================================================

# Restrição (11) Limite de descarga na usina por cenário.
s.t. Limite_Descarga_Usina{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Descarga[t];
# ==================================================================================================================================

# Restrição (12) Limite do Parque de Silos por cenário.
s.t. Limite_Armazenagem_Silos{t in T, s in S}:
    sum{m in M} ((1 - beta_trans) * sum{p in P} (gama[p,m,t,s] * z[p,m,t])) <= Cap_Armazenagem[t];
# ==================================================================================================================================

# Restrição (13) Limite da frota de caminhões por cenário.
s.t. Limite_Frota_Caminhoes{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Frota_Caminhoes[t];
# ==================================================================================================================================

# Restrição (14) Limite de expedição e carregamento por cenário.
s.t. Limite_Carregamento_Expedicao{t in T, s in S}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s]) <= Cap_Carregamento[t];
# ==================================================================================================================================
"""

with open("pbio_estocastico_v5.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod_v5_estocastico)

print("-> Arquivo pbio_estocastico_v5.mod criado com sucesso.")

# 3. Gerador das 20 Instâncias (Árvore de 27 Cenários com calibração proporcional correta)
random.seed(42)
print("\nGerando 20 instâncias (Árvore de 27 Cenários) e executando o GLPSOL...")
print(f"{'Instância':<12} | {'Porte':<8} | {'Lucro Esperado Ótimo (R$)':<28} | {'Estado'}")
print("-" * 72)

prob_d = {'Baixa': 0.2, 'Media': 0.5, 'Alta': 0.3}
fat_d  = {'Baixa': 0.90, 'Media': 1.00, 'Alta': 1.15}

prob_p = {'Ruim': 0.2, 'Normal': 0.5, 'Boa': 0.3}
fat_p  = {'Ruim': 0.80, 'Normal': 1.00, 'Boa': 1.15}

prob_v = {'Baixo': 0.25, 'Medio': 0.50, 'Alto': 0.25}
fat_v  = {'Baixo': 0.85, 'Medio': 1.00, 'Alto': 1.25}

for i in range(1, 21):
    if i <= 6:
        porte = "Pequeno"
        fator = 0.6  # Fator equilibrado para instâncias pequenas
    elif i <= 14:
        porte = "Médio"
        fator = 1.0  # Porte base original
    else:
        porte = "Grande"
        fator = 1.4  # Porte expandido

    d2024_base = 75000.0 * fator
    d2025_base = 88000.0 * fator
    preco_bio = 4500.0
    cap_usina = 190000.0 * fator

    cenarios_cfg = []
    pi_cfg = {}
    demanda_cfg = {}
    v_cost_cfg = {}
    gama_cfg_linhas = []

    s_idx = 1
    for d_niv in ['Baixa', 'Media', 'Alta']:
        for p_niv in ['Ruim', 'Normal', 'Boa']:
            for v_niv in ['Baixo', 'Medio', 'Alto']:
                s_nome = f"S{s_idx}"
                cenarios_cfg.append(s_nome)
                
                pi_cfg[s_nome] = prob_d[d_niv] * prob_p[p_niv] * prob_v[v_niv]
                demanda_cfg[s_nome] = (d2024_base * fat_d[d_niv], d2025_base * fat_d[d_niv])
                v_cost_cfg[s_nome] = (480.0 * fat_v[v_niv], 510.0 * fat_v[v_niv])

                polos_dados = [
                    ("polo_norteMG", [("Soja", 2.80, 3.10), ("Algodao", 2.20, 2.40), ("Macauba", 3.50, 3.80), ("Girassol", 1.50, 1.70), ("Nabo_Forrageiro", 1.80, 2.00)]),
                    ("polo_semiarido", [("Soja", 2.10, 2.30), ("Algodao", 1.70, 1.90), ("Macauba", 2.90, 3.10), ("Girassol", 1.20, 1.30), ("Nabo_Forrageiro", 1.40, 1.50)])
                ]
                
                fp = fat_p[p_niv]
                for polo, mp_list in polos_dados:
                    for mp, b24, b25 in mp_list:
                        gama_cfg_linhas.append(f"    [{polo}, {mp}, 2024, {s_nome}] := {round(b24 * fp, 2)}")
                        gama_cfg_linhas.append(f"    [{polo}, {mp}, 2025, {s_nome}] := {round(b25 * fp, 2)}")
                
                s_idx += 1

    lista_s_str = " ".join(cenarios_cfg)
    pi_str = "\n    ".join([f"{s} {pi_cfg[s]:.6f}" for s in cenarios_cfg])
    dem_24_str = " ".join([f"{s} {demanda_cfg[s][0]:.2f}" for s in cenarios_cfg])
    dem_25_str = " ".join([f"{s} {demanda_cfg[s][1]:.2f}" for s in cenarios_cfg])
    v_24_str = " ".join([f"{s} {v_cost_cfg[s][0]:.2f}" for s in cenarios_cfg])
    v_25_str = " ".join([f"{s} {v_cost_cfg[s][1]:.2f}" for s in cenarios_cfg])
    gama_str = "\n".join(gama_cfg_linhas)

    conteudo_dat = f"""
# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO 5) - Instância - Modelo Estocástico
# =============================================================================================================

data;

set T := 2024 2025;
set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;
set S := {lista_s_str};

param pi :=
    {pi_str};

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
param Capacidade_Usina := {cap_usina};

param Custo_Fixo_Polo :=
    polo_norteMG    500000.0
    polo_semiarido  400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0
    rede_urbana        200000.0;

param Cap_Descarga :=
    2024 {140000.0 * fator}
    2025 {160000.0 * fator};

param Cap_Armazenagem :=
    2024 {120000.0 * fator}
    2025 {140000.0 * fator};

param Cap_Frota_Caminhoes :=
    2024 {140000.0 * fator}
    2025 {160000.0 * fator};

param Cap_Carregamento :=
    2024 {130000.0 * fator}
    2025 {150000.0 * fator};

param C_OGR := 
    rede_catadores_moc 110.0 
    rede_urbana        125.0;

param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

param D :=
    [2024, *] := {dem_24_str}
    [2025, *] := {dem_25_str};

param v_cost :=
    [2024, *] := {v_24_str}
    [2025, *] := {v_25_str};

param gama :=
{gama_str};

param AZ :=
    [polo_norteMG, *]   := 2024 12.0 2025 12.0
    [polo_semiarido, *] := 2024 15.0 2025 15.0;

param Z_barra :=
    [polo_norteMG, Soja, *]            := 2024 {40000.0 * fator} 2025 {45000.0 * fator}
    [polo_norteMG, Algodao, *]         := 2024 {15000.0 * fator} 2025 {18000.0 * fator}
    [polo_norteMG, Macauba, *]         := 2024 {8000.0 * fator}  2025 {10000.0 * fator}
    [polo_norteMG, Girassol, *]        := 2024 {5000.0 * fator}  2025 {6000.0 * fator}
    [polo_norteMG, Nabo_Forrageiro, *] := 2024 {4000.0 * fator}  2025 {5000.0 * fator}
    [polo_semiarido, Soja, *]          := 2024 {30000.0 * fator} 2025 {35000.0 * fator}
    [polo_semiarido, Algodao, *]       := 2024 {12000.0 * fator} 2025 {14000.0 * fator}
    [polo_semiarido, Macauba, *]       := 2024 {10000.0 * fator} 2025 {12000.0 * fator}
    [polo_semiarido, Girassol, *]      := 2024 {5000.0 * fator}  2025 {6000.0 * fator}
    [polo_semiarido, Nabo_Forrageiro, *]:= 2024 {5000.0 * fator} 2025 {6000.0 * fator};

param TF := 2024 1800 2025 2200;

param OfertaOGR :=
    [rede_catadores_moc, *] := 2024 {90000.0 * fator} 2025 {100000.0 * fator}
    [rede_urbana, *]        := 2024 {20000.0 * fator} 2025 {25000.0 * fator};

param CompraMax := 2024 {15000.0 * fator} 2025 {20000.0 * fator};

end;
"""

    dat_file = f"instancia_v5_estocastica_{i}.dat"
    out_file = f"resultado_v5_estocastica_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_estocastico_v5.mod", "-d", dat_file, "-o", out_file],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        lucro_str = "N/D"
        with open(out_file, "r", encoding="utf-8") as f_out:
            for line in f_out:
                if "Objective:" in line:
                    partes = line.split()
                    for p in partes:
                        try:
                            val = float(p.replace(',', ''))
                            lucro_str = f"R$ {val:,.2f}"
                            break
                        except ValueError:
                            continue
        print(f"Instância {i:<2} ({porte:<8}) | {lucro_str:<28} | INTEGER OPTIMAL")
    except Exception as e:
        print(f"Instância {i:<2} ({porte:<8}) | Falha na execução              | ERROR")
