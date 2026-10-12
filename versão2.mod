# ==============================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (COM MÚLTIPLAS MATÉRIAS-PRIMAS E PERDAS)
# ==============================================================================

# Adicionando sujestão 6. Rendimento Fixo

# CONJUNTOS (Índices)
set T; # Períodos de tempo
set P; # Zonas produtoras de oleaginosas
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)

# PARÂMETROS
param alfa{M};                     # Rendimento de óleo específico para cada matéria-prima m
param beta_trans := 0.02;          # Percentual de perda física no transporte (2%)
param beta_proc := 0.015;          # Percentual de perda física no esmagamento (1.5%)
param gama{P, M, T};               # Produtividade agrícola da zona p para a matéria m no período t
param AZ{P, T};                    # Tamanho médio dos lotes das famílias na zona p
param Z_barra{P, M, T};            # Área máxima disponível para cultivo da matéria m na zona p
param D{T};                        # Demanda total de biodiesel/óleo no período t
param TF{T};                       # Número mínimo de famílias do Selo Social no período t
param Capacidade_Usina;            # Capacidade máxima de esmagamento na usina
param OfertaOGR{R, T};             # Disponibilidade máxima de OGR por fonte
param CompraMax{T};                # Limite máximo de compra externa de óleo

# PARÂMETROS DE CUSTO
param PC{P, M};                    # Custo unitário de produção agrícola por matéria-prima
param GTC{P};                      # Custo de transporte de sementes da zona p até a usina
param CC;                          # Custo unitário de esmagamento na usina
param C_OGR{R};                    # Custo unitário de aquisição de OGR
param v_cost{T};                   # Custo de oportunidade para compra de óleo externo

# VARIÁvEIS DE DECISÃO
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima
var gx{P, M, T} >= 0;              # Volume de sementes transportadas por matéria-prima
var ogr_x{R, T} >= 0;              # Volume de OGR adquirido
var w{M, T} >= 0;                  # Total de sementes de cada matéria-prima trituradas na planta
var v{T} >= 0;                     # Óleo complementar adquirido do mercado

# ==============================================================================
# FUNÇÃO OBJETIVO: Minimizar o Custo Total
# ==============================================================================
minimize Custo_Total:
    sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t]) + 
    sum{p in P, m in M, t in T} (GTC[p] * gx[p,m,t]) + 
    sum{m in M, t in T} (CC * w[m,t]) + 
    sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) + 
    sum{t in T} (v_cost[t] * v[t]);

# ==============================================================================
# RESTRIÇÕES DO SISTEMA
# ==============================================================================

# Restrição (2): Atendimento da Demanda (com rendimento específico e perdas industriais)
s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];

# Restrição (3): Limite de Área Agrícola Disponível por Cultura
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t];

# Restrição (4): Cumprimento do Selo Biocombustível Social (considerando a área total de todas as culturas)
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

# Restrição (5): Balanço de Massa Agrícola (com desconto de perdas no transporte)
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

# Restrição (6): Balanço de Processamento Industrial por Matéria-Prima
s.t. Balanco_Processamento{m in M, t in T}:
    w[m,t] = sum{p in P} gx[p,m,t];

# Restrição (7): Capacidade Industrial Total da Usina (Soma de todas as sementes)
s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;

# Restrição (8): Percentual Mínimo de OGR (14%)
s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t];

# Restrição (9): Limite Máximo de Disponibilidade de OGR
s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t];

# Restrição (10): Limite Máximo para Aquisição Externa de Óleo
s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];
