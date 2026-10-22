# ==============================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 4)
# ==============================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo
set P; # Zonas produtoras de oleaginosas
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas

# PARÂMETROS
param alfa{M};                     # Rendimento de óleo específico para cada matéria-prima m
param beta_trans := 0.02;          # Percentual de perda física no transporte (2%)
param beta_arm   := 0.01;          # Percentual de perda física na armazenagem/silos (1%)
param beta_proc  := 0.015;         # Percentual de perda física no esmagamento industrial (1.5%)
param gama{P, M, T};               # Produtividade agrícola da zona p para a matéria m no período t
param AZ{P, T};                    # Tamanho médio dos lotes das famílias na zona p
param Z_barra{P, M, T};            # Área máxima disponível para cultivo da matéria m na zona p
param D{T};                        # Demanda total de biodiesel/óleo no período t
param TF{T};                       # Número mínimo de famílias do Selo Social no período t
param Capacidade_Usina;            # Capacidade máxima de esmagamento na usina
param OfertaOGR{R, T};             # Disponibilidade máxima de OGR por fonte
param CompraMax{T};                # Limite máximo de compra externa de óleo

# NOVOS PARÂMETROS DE CAPACIDADE LOGÍSTICA (Sugestão 9)
param Cap_Descarga{T};             # Limite máximo de descarga de matéria-prima na usina
param Cap_Armazenagem{T};          # Limite de capacidade dos silos/armazenagem
param Cap_Frota_Caminhoes{T};      # Limite total de volume transportável pela frota
param Cap_Carregamento{T};         # Limite máximo de expedição/carregamento de produtos

# PARÂMETROS DE PREÇO DE VENDA E RECEITAS
param preco_biodiesel;
param preco_farelo{M};
param rend_farelo{M};
param preco_glicerina;
param rend_glicerina;
param preco_carbono;

# PARÂMETROS DE CUSTO
param PC{P, M};
param GTC{P};
param CC;
param C_OGR{R};
param v_cost{T};

# VARIÁVEIS DE DECISÃO
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima
var gx{P, M, T} >= 0;              # Volume de sementes transportadas por matéria-prima
var ogr_x{R, T} >= 0;              # Volume de OGR adquirido
var w{M, T} >= 0;                  # Total de sementes líquidas trituradas
var v{T} >= 0;                     # Óleo complementar adquirido do mercado

# ==============================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Total da Cadeia
# ==============================================================================
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
        sum{t in T} (v_cost[t] * v[t])
    );

# ==============================================================================
# RESTRIÇÕES DO SISTEMA (Incluindo as novas restrições logísticas)
# ==============================================================================

s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];

s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t];

s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

s.t. Balanco_Processamento_Armazenagem{m in M, t in T}:
    w[m,t] = (1 - beta_arm) * sum{p in P} gx[p,m,t];

s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;

s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t];

s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t];

s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];

# --- NOVAS RESTRIÇÕES LOGÍSTICAS (Sugestão 9) ---

# 1. Limite de Descarga na Usina (Volume total de matéria-prima que chega)
s.t. Limite_Descarga_Usina{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Descarga[t];

# 2. Limite de Armazenagem nos Silos (Volume armazenado antes do esmagamento)
s.t. Limite_Armazenagem_Silos{t in T}:
    sum{p in P, m in M} ((1 - beta_trans) * gama[p,m,t] * z[p,m,t]) <= Cap_Armazenagem[t];

# 3. Limite da Frota de Caminhões (Volume total transportado das zonas)
s.t. Limite_Frota_Caminhoes{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Frota_Caminhoes[t];

# 4. Limite de Carregamento/Expedição (Volume total de biodiesel expedido)
s.t. Limite_Carregamento_Expedicao{t in T}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t]) <= Cap_Carregamento[t];

