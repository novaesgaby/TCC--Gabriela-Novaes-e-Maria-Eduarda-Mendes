
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (MONTES CLAROS)
# ==============================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (ex: 2024 e 2025)
set P; # Zonas produtoras de oleaginosas (Agricultura Familiar / Semiárido)
set R; # Cooperativas/Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas disponíveis (Soja, Algodão, Macaúba, etc.)

# PARÂMETROS
param alfa;                           # Rendimento de óleo na semente (ex: 0.19)
param gama{P, T};                     # Produtividade agrícola na zona p no período t
param AZ{P, T};                       # Tamanho médio dos lotes das famílias na zona p
param Z_barra{P, T};                  # Área máxima disponível para cultivo na zona p
param D{T};                           # Demanda total de biodiesel/óleo no período t
param TF{T};                          # Número mínimo de famílias do Selo Social no período t
param Capacidade_Usina;               # Capacidade máxima de trituração/esmagamento (Restrição 7)
param OfertaOGR{R, T};                # Disponibilidade máxima de OGR por fonte (Restrição 9)
param CompraMax{T};                   # Limite máximo de compra externa de óleo (Restrição 10)

# PARÂMETROS DE CUSTO
param PC{P};                          # Custo unitário de produção agrícola na zona p
param GTC{P};                         # Custo de transporte de sementes da zona p até a usina
param CC;                             # Custo unitário de esmagamento na usina
param C_OGR{R};                       # Custo unitário de aquisição de OGR da fonte r
param v_cost{T};                      # Custo de oportunidade para compra de óleo externo

# VARIÁVEIS DE DECISÃO (Todas com não-negatividade explicita - Restrição 11)
var z{P, T} >= 0;                     # Área de terra alocada para agricultura familiar
var gx{P, T} >= 0;                    # Volume de sementes transportadas
var ogr_x{R, T} >= 0;                 # Volume de OGR adquirido
var w{T} >= 0;                        # Total de sementes trituradas na planta
var v{T} >= 0;                        # Óleo complementar adquirido do mercado

# ==============================================================================
# FUNÇÃO OBJETIVO: Minimizar o Custo Total de Produção e Logística (1)
# ==============================================================================
minimize Custo_Total:
    sum{p in P, t in T} (PC[p] * z[p,t]) +         # Custos de fomento agrícola
    sum{p in P, t in T} (GTC[p] * gx[p,t]) +       # Custos de transporte (Inbound)
    sum{t in T} (CC * w[t]) +                      # Custos industriais de esmagamento
    sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) +  # Custos de aquisição de OGR
    sum{t in T} (v_cost[t] * v[t]);                # Custo de compra externa

# ==============================================================================
# RESTRIÇÕES DO SISTEMA
# ==============================================================================

# Restrição (2): Atendimento da Demanda
# A produção precisa cobrir exatamente a quantidade da demanda
s.t. Atendimento_Demanda{t in T}:
    (alfa * w[t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];
# ================================================================================

# Restrição (3): Limite de Área Agrícola Disponível
# Não podemos plantar além da capacidade máxima do solo fértil
s.t. Limite_Area_Disponivel{p in P, t in T}:
    z[p,t] <= Z_barra[p,t];
# ================================================================================

# Restrição (4): Cumprimento do Selo Biocombustível Social
# Restrição garante o benefício discal do governo ao ajudar famílias no plantio 
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P} (z[p,t] / AZ[p,t]) >= TF[t];
# ================================================================================

# Restrição (5): Balanço de Massa Agrícola
# Qtd de sementes que sai de um polo para a usina deve ser exatamento o resultado da área plantada multiplicada pela produtividade da terra
s.t. Balanco_Massa_Agricola{p in P, t in T}:
    gx[p,t] = gama[p,t] * z[p,t];
# ================================================================================

# Restrição (6): Balanço de Processamento Industrial
# Garante que o total de sementes que a usina decide esmagar é igual a soma das sementes que chegam
s.t. Balanco_Processamento{t in T}:
    w[t] = sum{p in P} gx[p,t];
# ================================================================================

# Restrição (7): Capacidade Industrial da Usina
s.t. Capacidade_Industrial{t in T}:
    w[t] <= Capacidade_Usina;
# ================================================================================

# Restrição (8): Percentual Mínimo de OGR (14%)
# Por questões ambientais, a empresa é obrigada a usar 14% de óleos e gorduras na produção
s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t];
# ================================================================================

# Restrição (9): Limite Máximo de Disponibilidade de OGR por Fornecedor
# Não temos óleo infinito, o modelo não pode comprar mais do que o estoque disponível no fornecedor
s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t];
# ================================================================================

# Restrição (10): Limite Máximo para Aquisição Externa de Óleo
# Comprar óleo pronto de terceiro é caro, a restrição é importante para ter um teto máximo
s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];
