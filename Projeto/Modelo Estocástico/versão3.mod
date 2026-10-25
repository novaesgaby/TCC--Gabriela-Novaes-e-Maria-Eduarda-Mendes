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
