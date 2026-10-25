# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 4 - Modelo Estocástico)
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
param beta_trans := 0.02;          # Percentual de perda física no transporte (2%)
param beta_arm   := 0.01;          # Percentual de perda física na armazenagem/silos (1%)
param beta_proc  := 0.015;         # Percentual de perda física no esmagamento industrial (1.5%)

param gama{P, M, T, S};            # Produtividade agrícola estocástica da zona p para a matéria m no período t no cenário s
param AZ{P, T};                    # Tamanho médio dos lotes das famílias na zona p
param Z_barra{P, M, T};            # Área máxima disponível para cultivo da matéria m na zona p
param D{T, S};                     # Demanda total de biodiesel/óleo estocástica no período t no cenário s
param TF{T};                       # Número mínimo de famílias do Selo Social no período t
param Capacidade_Usina;            # Capacidade máxima de esmagamento na usina
param OfertaOGR{R, T};             # Disponibilidade máxima de OGR por fonte
param CompraMax{T};                # Limite máximo de compra externa de óleo

# PARÂMETROS DE CAPACIDADE LOGÍSTICA
param Cap_Descarga{T};             # Limite máximo de descarga de matéria-prima na usina
param Cap_Armazenagem{T};          # Limite de capacidade dos silos/armazenagem
param Cap_Frota_Caminhoes{T};      # Limite total de volume transportável pela frota
param Cap_Carregamento{T};         # Limite máximo de expedição/carregamento de produtos

# PARÂMETROS DE PREÇO DE VENDA E RECEITAS [R$]
param preco_biodiesel;
param preco_farelo{M};
param rend_farelo{M};
param preco_glicerina;
param rend_glicerina;
param preco_carbono;

# PARÂMETROS DE CUSTO OPERACIONAL [R$]
param PC{P, M};                    # Custo de cultivo [R$/ha]
param GTC{P};                      # Custo de transporte de grãos [R$/t]
param CC;                          # Custo de esmagamento [R$/t]
param C_OGR{R};                    # Custo de aquisição de OGR [R$/t]
param v_cost{T, S};                # Custo estocástico do óleo externo [R$/t]
param penalidade_deficit := 10000.0; # Penalidade pelo não atendimento da demanda [R$/t]

# VARIÁVEIS DE 1º ESTÁGIO (Decisões Estruturais / Cultivo)
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima [ha]

# VARIÁVEIS DE 2º ESTÁGIO (Decisões Operacionais por Cenário)
var gx{P, M, T, S} >= 0;           # Volume de sementes transportadas por cenário
var ogr_x{R, T, S} >= 0;           # Volume de OGR adquirido por cenário
var w{M, T, S} >= 0;               # Total de sementes líquidas trituradas por cenário
var v{T, S} >= 0;                  # Óleo complementar adquirido do mercado por cenário
var deficit{T, S} >= 0;            # Déficit de atendimento da demanda por cenário

# ==================================================================================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Esperado
# ==================================================================================================================================
maximize Lucro_Esperado:
    - sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t])
    + sum{s in S} pi[s] * (
        sum{t in T} (preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s])) +
        sum{m in M, t in T} (preco_farelo[m] * rend_farelo[m] * w[m,t,s]) +
        sum{t in T} (preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])) +
        sum{t in T} (preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])) -
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

# Restrição (2): Limite da área agrícola disponível para cultivo
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t];

# Restrição (3): Cumprimento da meta do Selo Biocombustível Social
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

# Restrição (4): Atendimento da demanda de biodiesel sob incerteza (com déficit penalizado)
s.t. Atendimento_Demanda{t in T, s in S}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s] + deficit[t,s] >= D[t,s];

# Restrição (5): Balanço de massa agrícola (transporte x colheita bruta com perda)
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T, s in S}:
    gx[p,m,t,s] = (1 - beta_trans) * gama[p,m,t,s] * z[p,m,t];

# Restrição (6): Balanço entre processamento industrial e armazenagem por cenário
s.t. Balanco_Processamento_Armazenagem{m in M, t in T, s in S}:
    w[m,t,s] = (1 - beta_arm) * sum{p in P} gx[p,m,t,s];

# Restrição (7): Capacidade máxima de esmagamento industrial na usina
s.t. Capacidade_Industrial{t in T, s in S}:
    sum{m in M} w[m,t,s] <= Capacidade_Usina;

# Restrição (8): Percentual mínimo obrigatório de OGR (14%) em relação à demanda
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] >= 0.14 * D[t,s];

# Restrição (9): Disponibilidade máxima de OGR por fonte de suprimento
s.t. Disponibilidade_Max_OGR{r in R, t in T, s in S}:
    ogr_x[r,t,s] <= OfertaOGR[r,t];

# Restrição (10): Teto máximo de compra de óleo externo de terceiros
s.t. Teto_Compra_Externa{t in T, s in S}:
    v[t,s] <= CompraMax[t];

# Restrição (11): Limite de descarga de matéria-prima na usina
s.t. Limite_Descarga_Usina{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Descarga[t];

# Restrição (12): Limite de armazenagem no parque de silos
s.t. Limite_Armazenagem_Silos{t in T, s in S}:
    sum{m in M} ((1 - beta_trans) * sum{p in P} (gama[p,m,t,s] * z[p,m,t])) <= Cap_Armazenagem[t];

# Restrição (13): Limite operacional da frota de caminhões
s.t. Limite_Frota_Caminhoes{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Frota_Caminhoes[t];

# Restrição (14): Limite de carregamento e expedição de produtos finais
s.t. Limite_Carregamento_Expedicao{t in T, s in S}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s]) <= Cap_Carregamento[t];
