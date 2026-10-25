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
