# ==============================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO 
# ==============================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo
set P; # Zonas produtoras de oleaginosas (Polos agrícolas)
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas

# PARÂMETROS AGRÍCOLAS E TÉCNICOS
param alfa{M};                     # Rendimento de óleo por matéria-prima
param beta_trans := 0.02;          # Perda física no transporte (2%)
param beta_arm   := 0.01;          # Perda física na armazenagem (1%)
param beta_proc  := 0.015;         # Perda física no esmagamento (1.5%)
param gama{P, M, T};               # Produtividade agrícola [t/ha]
param AZ{P, T};                    # Tamanho médio dos lotes das famílias [ha/família]
param Z_barra{P, M, T};            # Área máxima disponível para cultivo [ha]
param D{T};                        # Demanda total de biodiesel/óleo
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
param Custo_Fixo_OGR{R};           # Custo fixo para contratar a rede de OGR r

# PARÂMETROS DE PREÇO E RECEITAS [R$]
param preco_biodiesel;
param preco_farelo{M};
param rend_farelo{M};
param preco_glicerina;
param rend_glicerina;
param preco_carbono;

# PARÂMETROS DE CUSTO OPERACIONAL [R$]
param PC{P, M};                    # Custo de cultivo [R$/ha]
param GTC{P};                      # Custo de transporte de grãos [R$/t]
param CC;                          # Custo de esmagamento/processamento [R$/t]
param C_OGR{R};                    # Custo de aquisição de OGR [R$/t]
param v_cost{T};                   # Custo de compra externa de óleo [R$/t]
param Custo_Estoque_Semente{M};    # Custo de armazenagem de sementes [R$/t]

# VARIÁVEIS DE DECISÃO CONTÍNUAS
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima [ha]
var gx{P, M, T} >= 0;              # Volume de sementes transportadas [t]
var ogr_x{R, T} >= 0;              # Volume de OGR adquirido [t]
var w{M, T} >= 0;                  # Total de sementes líquidas trituradas [t]
var v{T} >= 0;                     # Óleo complementar adquirido do mercado [t]
var estoque_semente{M, T} >= 0;    # Estoque de sementes armazenado [t]

# VARIÁVEIS DE DECISÃO BINÁRIAS (MILP)
var y_polo{P, T} binary;           # 1 se o polo agrícola p for aberto no período t
var y_ogr{R, T} binary;            # 1 se a rede de OGR r for contratada no período t

# ==============================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Total
# ==============================================================================
maximize Lucro_Total:
    # 1. RECEITAS TOTAIS
    sum{t in T} (preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t])) +
    sum{m in M, t in T} (preco_farelo[m] * rend_farelo[m] * w[m,t]) +
    sum{t in T} (preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) +
    sum{t in T} (preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) -

    # 2. CUSTOS TOTAIS
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

# ==============================================================================
# RESTRIÇÕES DO SISTEMA
# ==============================================================================

s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];

s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];

s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

# Balanço de Estoque no Primeiro Período (2024 - Sem estoque inicial)
s.t. Balanco_Estoque_Inicial{m in M}:
    estoque_semente[m, 2024] = sum{p in P} gx[p, m, 2024] * (1 - beta_arm) - w[m, 2024];

# Balanço de Estoque nos Períodos Seguintes (2025 em diante)
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

# Restrições Logísticas
s.t. Limite_Descarga_Usina{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Descarga[t];

s.t. Limite_Armazenagem_Silos{t in T}:
    sum{m in M} estoque_semente[m,t] <= Cap_Armazenagem[t];

s.t. Limite_Frota_Caminhoes{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Frota_Caminhoes[t];

s.t. Limite_Carregamento_Expedicao{t in T}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t]) <= Cap_Carregamento[t];
