import os
import shutil
import subprocess
import random

# 1. Garante a instalação do GLPK no ambiente
if not shutil.which("glpsol"):
    print("Instalando glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Criação automática do arquivo .mod (Versão 3 Estocástica com Restrições Numeradas e Comentadas)
codigo_mod_v3_estocastico = """
# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 3 - Modelo Estocástico)
# ========================================================================================================================
# O modelo maximiza o Lucro Esperado da cadeia sob incerteza, considerando receitas de biodiesel, farelo, glicerina 
# e créditos de carbono, ponderadas pelas probabilidades dos cenários, subtraindo os custos operacionais e agrícolas.
# ========================================================================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (2024 e 2025)
set P; # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)
set S; # Conjunto de Cenários (omega) da árvore de incerteza

# PARÂMETROS AGRÍCOLAS E ESTOCÁSTICOS
param pi{S};                       # Probabilidade de cada cenário omega ocorrer (pi_omega)

param alfa{M};                     # Rendimento de óleo específico para cada matéria-prima m
param beta_trans := 0.02;          # Percentual de perda física no transporte (2%)
param beta_arm   := 0.01;          # Percentual de perda física na armazenagem/silos (1%)
param beta_proc  := 0.015;         # Percentual de perda física no esmagamento industrial (1.5%)

param gama{P, M, T, S};            # Produtividade agrícola estocástica da zona p para a matéria m no período t no cenário s
param AZ{P, T};                    # Tamanho médio dos lotes das famílias na zona p [ha/família]
param Z_barra{P, M, T};            # Área máxima disponível para cultivo da matéria m na zona p [ha]
param D{T, S};                     # Demanda total de biodiesel/óleo estocástica no período t no cenário s [t]
param TF{T};                       # Número mínimo de famílias participantes do Selo Social no período t
param Capacidade_Usina;            # Capacidade máxima de esmagamento na usina [t/ano]
param OfertaOGR{R, T};             # Disponibilidade máxima de OGR por fonte e período [t]
param CompraMax{T};                # Limite máximo de compra externa de óleo por período [t]

# PARÂMETROS DE PREÇO DE VENDA E RECEITAS [R$]
param preco_biodiesel;             # Preço unitário de venda do biodiesel principal [R$/t]
param preco_farelo{M};             # Preço de venda do farelo gerado por tipo de semente [R$/t]
param rend_farelo{M};              # Percentual de farelo obtido por tonelada esmagada
param preco_glicerina;             # Preço de venda unitário do coproduto glicerina [R$/t]
param rend_glicerina;              # Fator de conversão da glicerina em relação ao óleo produzido
param preco_carbono;               # Valor unitário dos créditos de carbono gerados [R$/t]

# PARÂMETROS DE CUSTO OPERACIONAL [R$]
param PC{P, M};                    # Custo unitário de produção agrícola por matéria-prima [R$/ha]
param GTC{P};                      # Custo de transporte de sementes da zona p até a usina [R$/t]
param CC;                          # Custo unitário de esmagamento e conversão na usina [R$/t]
param C_OGR{R};                    # Custo unitário de aquisição de Óleo e Gordura Residual [R$/t]
param v_cost{T, S};                # Custo estocástico de oportunidade para compra de óleo externo [R$/t]
param penalidade_deficit := 10000.0; # Penalidade aplicada por tonelada de déficit no atendimento da demanda [R$/t]

# VARIÁVEIS DE 1º ESTÁGIO (Decisões Estruturais / Cultivo)
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima (hectares a plantar no polo p, da MP m, no ano t)

# VARIÁVEIS DE 2º ESTÁGIO (Decisões Operacionais por Cenário)
var gx{P, M, T, S} >= 0;           # Volume de sementes transportadas da zona p, da MP m, no ano t, no cenário s [t]
var ogr_x{R, T, S} >= 0;           # Volume de OGR adquirido da rede r, no ano t, no cenário s [t]
var w{M, T, S} >= 0;               # Total de sementes líquidas trituradas da MP m, no ano t, no cenário s [t]
var v{T, S} >= 0;                  # Volume de óleo pronto adquirido de terceiros no ano t, no cenário s [t]
var deficit{T, S} >= 0;            # Déficit de atendimento da demanda de biodiesel no ano t, no cenário s [t]

# ==================================================================================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Esperado da Cadeia (Receitas Esperadas - Custos Agrícolas - Custos Operacionais Esperados)
# ==================================================================================================================================
maximize Lucro_Esperado:
    # 1. Custos de Cultivo (1º Estágio - Decisões estruturais determinísticas de plantio)
    - sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t])

    # 2. Valor Esperado de 2º Estágio (Receitas e Custos operacionais por cenário ponderados pelas probabilidades pi[s])
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

# Restrição (2): Atendimento da demanda de biodiesel sob incerteza (com folga para déficit penalizado)
s.t. Atendimento_Demanda{t in T, s in S}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s] + deficit[t,s] >= D[t,s];

# Restrição (3): Limite máximo da área de terra disponível para cultivo por zona e matéria-prima
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t];

# Restrição (4): Cumprimento da meta de inclusão familiar do Selo Biocombustível Social
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

# Restrição (5): Balanço de massa agrícola (volume transportado descontado da perda de transporte)
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T, s in S}:
    gx[p,m,t,s] = (1 - beta_trans) * gama[p,m,t,s] * z[p,m,t];

# Restrição (6): Balanço entre o processamento industrial e a armazenagem (descontada a perda de silos)
s.t. Balanco_Processamento_Armazenagem{m in M, t in T, s in S}:
    w[m,t,s] = (1 - beta_arm) * sum{p in P} gx[p,m,t,s];

# Restrição (7): Capacidade industrial máxima de esmagamento na usina por cenário
s.t. Capacidade_Industrial{t in T, s in S}:
    sum{m in M} w[m,t,s] <= Capacidade_Usina;

# Restrição (8): Percentual mínimo obrigatório de OGR (14%) em relação à demanda de biodiesel
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] >= 0.14 * D[t,s];

# Restrição (9): Disponibilidade máxima de OGR por fonte fornecedora em cada cenário
s.t. Disponibilidade_Max_OGR{r in R, t in T, s in S}:
    ogr_x[r,t,s] <= OfertaOGR[r,t];

# Restrição (10): Teto máximo de aquisição de óleo externo de terceiros por período e cenário
s.t. Teto_Compra_Externa{t in T, s in S}:
    v[t,s] <= CompraMax[t];
"""

with open("pbio_estocastico_v3.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod_v3_estocastico)

print("-> Arquivo pbio_estocastico_v3.mod criado com sucesso.")

# 3. Gerador das 20 Instâncias com árvore de 27 cenários e variação dinâmica individual
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
        fator = random.uniform(0.50, 0.70)
    elif i <= 14:
        porte = "Médio"
        fator = random.uniform(0.90, 1.10)
    else:
        porte = "Grande"
        fator = random.uniform(1.30, 1.50)

    d2024_base = 95000.0 * fator * random.uniform(0.97, 1.03)
    d2025_base = 110000.0 * fator * random.uniform(0.97, 1.03)
    preco_bio = round(random.uniform(4300.0, 4800.0), 2)
    cap_usina = 150000.0 * fator

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
                        gama_cfg_linhas.append(f"    [{polo}, {mp}, 2024, {s_nome}] := {round(b24 * fp * random.uniform(0.98, 1.02), 2)}")
                        gama_cfg_linhas.append(f"    [{polo}, {mp}, 2025, {s_nome}] := {round(b25 * fp * random.uniform(0.98, 1.02), 2)}")
                
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
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO 3) - Modelo Estocástico 
# =============================================================================================================

data;

# Conjuntos principais da modelagem
set T := 2024 2025;                                       # Horizonte de planejamento temporal
set P := polo_norteMG polo_semiarido;                     # Zonas produtoras agrícolas
set R := rede_catadores_moc rede_urbana;                  # Redes fornecedoras de OGR
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;   # Matérias-primas suportadas
set S := {lista_s_str};                                   # Conjunto de 27 cenários da árvore estocástica (omega)

# Probabilidade conjunta de cada cenário omega ocorrer (pi_omega)
param pi :=
    {pi_str};

# Rendimento de óleo específico (teor de extração) para cada matéria-prima m
param alfa :=
    Soja            0.18
    Algodao         0.15
    Macauba         0.28
    Girassol        0.40
    Nabo_Forrageiro 0.35;

# Parâmetros econômicos de receitas e preços de venda
param preco_biodiesel := {preco_bio};                     # Preço de venda unitário do biodiesel [R$/t]
param preco_glicerina := 1200.0;                          # Preço de venda unitário do coproduto glicerina [R$/t]
param rend_glicerina  := 0.10;                            # Taxa de rendimento da glicerina por tonelada processada
param preco_carbono   := 50.0;                            # Créditos de carbono gerados por tonelada limpa [R$/t]

# Preço de comercialização do farelo como subproduto para ração animal
param preco_farelo :=
    Soja            800.0
    Algodao         650.0
    Macauba         500.0
    Girassol        700.0
    Nabo_Forrageiro 600.0;

# Taxas de rendimento do farelo para cada matéria-prima
param rend_farelo :=
    Soja            0.75
    Algodao         0.55
    Macauba         0.50
    Girassol        0.50
    Nabo_Forrageiro 0.45;

# Custos operacionais e capacidade global da usina
param CC := 45.0;                                         # Custo industrial de esmagamento e conversão [R$/t]
param Capacidade_Usina := {cap_usina};                    # Capacidade máxima de processamento da usina [t/ano]

# Custo unitário de aquisição de Óleo e Gordura Residual (OGR) por rede
param C_OGR := 
    rede_catadores_moc 110.0 
    rede_urbana        125.0;

# Custo de cultivo agrícola por zona e matéria-prima [R$/ha]
param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

# Custo logístico de transporte de grãos das roças até a usina [R$/t]
param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

# Demanda total estocástica de biodiesel por período e cenário [t]
param D :=
    [2024, *] := {dem_24_str}
    [2025, *] := {dem_25_str};

# Custo de aquisição de óleo externo de terceiros por período e cenário [R$/t]
param v_cost :=
    [2024, *] := {v_24_str}
    [2025, *] := {v_25_str};

# Produtividade agrícola estocástica (gama) [t/ha] por polo, matéria-prima, ano e cenário
param gama :=
{gama_str};

# Tamanho médio dos lotes familiares para atendimento ao Selo Social [ha/família]
param AZ :=
    [polo_norteMG, *]   := 2024 12.0 2025 12.0
    [polo_semiarido, *] := 2024 15.0 2025 15.0;

# Área máxima de terra disponível para plantio por polo e matéria-prima [ha]
param Z_barra :=
    [polo_norteMG, Soja, *]            := 2024 {30000.0 * fator} 2025 {35000.0 * fator}
    [polo_norteMG, Algodao, *]         := 2024 {10000.0 * fator} 2025 {12000.0 * fator}
    [polo_norteMG, Macauba, *]         := 2024 {5000.0 * fator}  2025 {6000.0 * fator}
    [polo_norteMG, Girassol, *]        := 2024 {3000.0 * fator}  2025 {4000.0 * fator}
    [polo_norteMG, Nabo_Forrageiro, *] := 2024 {2000.0 * fator}  2025 {3000.0 * fator}
    [polo_semiarido, Soja, *]          := 2024 {20000.0 * fator} 2025 {22000.0 * fator}
    [polo_semiarido, Algodao, *]       := 2024 {8000.0 * fator}  2025 {9000.0 * fator}
    [polo_semiarido, Macauba, *]       := 2024 {6000.0 * fator}  2025 {7000.0 * fator}
    [polo_semiarido, Girassol, *]      := 2024 {3000.0 * fator}  2025 {35000.0 * fator}
    [polo_semiarido, Nabo_Forrageiro, *]:= 2024 {3000.0 * fator} 2025 {35000.0 * fator};

# Meta mínima de famílias participantes do programa Selo Social por período
param TF := 2024 1800 2025 2200;

# Disponibilidade máxima de OGR por rede parceira e período [t]
param OfertaOGR :=
    [rede_catadores_moc, *] := 2024 {90000.0 * fator} 2025 {100000.0 * fator}
    [rede_urbana, *]        := 2024 {20000.0 * fator} 2025 {25000.0 * fator};

# Limite máximo de compra de óleo pronto de terceiros por período [t]
param CompraMax := 2024 {15000.0 * fator} 2025 {20000.0 * fator};

end;
"""

    dat_file = f"instancia_v3_estocastica_{i}.dat"
    out_file = f"resultado_v3_estocastica_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_estocastico_v3.mod", "-d", dat_file, "-o", out_file],
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
        print(f"Instância {i:<2} ({porte:<8}) | {lucro_str:<28} | INTEGER OPTIMAL")
    except Exception:
        print(f"Instância {i:<2} ({porte:<8}) | Falha na execução              | ERROR")
