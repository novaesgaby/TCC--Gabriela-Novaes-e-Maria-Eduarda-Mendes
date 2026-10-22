# ===========================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 3)
# ===========================================================================================================

# ===========================================================================================================
# Acrescentando restrição de lucro
# O modelo minimiza custos apenas. Considerar receitas de: farelo, glicerina, créditos de carbono. 
# Novo modelo sendo de maximização do lucro
# ============================================================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (2024 e 2025)
set P; # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)

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

# PARÂMETROS DE PREÇO DE VENDA E RECEITAS
param preco_biodiesel;             # Preço unitário de venda do biodiesel/óleo principal
param preco_farelo{M};             # Preço de venda do farelo gerado por tipo de semente
param rend_farelo{M};              # Percentual de farelo obtido por tonelada esmagada
param preco_glicerina;             # Preço de venda da glicerina por unidade produzida
param rend_glicerina;              # Fator de conversão da glicerina em relação ao óleo produzido
param preco_carbono;               # Valor unitário do crédito de carbono por unidade de biodiesel limpo

# PARÂMETROS DE CUSTO
param PC{P, M};                    # Custo unitário de produção agrícola por matéria-prima
param GTC{P};                      # Custo de transporte de sementes da zona p até a usina
param CC;                          # Custo unitário de esmagamento na usina
param C_OGR{R};                    # Custo unitário de aquisição de OGR
param v_cost{T};                   # Custo de oportunidade para compra de óleo externo

# VARIÁVEIS DE DECISÃO
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima (Qtd de hectares a plantar no polo p, da MP m, no ano t)
var gx{P, M, T} >= 0;              # Volume de sementes que chegam na usina do polo p, da MP m, no ano t)
var ogr_x{R, T} >= 0;              # Volume de OGR adquirido da rede r, no ano t
var w{M, T} >= 0;                  # Total de sementes líquidas de cada matéria-prima trituradas na planta (após armazenagem) no ano t 
var v{T} >= 0;                     # Volume de óleo pronto comprado de terceiro no ano t 

# =============================================================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Total da Cadeia (Receitas - Custos)
# =============================================================================================================
maximize Lucro_Total:
    # 1. RECEITAS
    # Receita com a venda do Biodiesel produzido internamente e óleo complementar comercializado
    sum{t in T} (preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t])) +
    # Receita com a venda de Farelo (coproduto do esmagamento)
    sum{m in M, t in T} (preco_farelo[m] * rend_farelo[m] * w[m,t]) +
    # Receita com a venda de Glicerina
    sum{t in T} (preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) +
    # Receita com Créditos de Carbono
    sum{t in T} (preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) -

    # 2. CUSTOS (Subtraídos na maximização)
    (
        sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t]) +   # Custos agrícolas
        sum{p in P, m in M, t in T} (GTC[p] * gx[p,m,t]) +   # Custos de transporte de entrada
        sum{m in M, t in T} (CC * w[m,t]) +                  # Custos industriais de esmagamento
        sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) +        # Custos de aquisição de OGR
        sum{t in T} (v_cost[t] * v[t])                      # Custo de compra externa
    );

# ==============================================================================
# RESTRIÇÕES DO SISTEMA
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
