# =====================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 6 - Modelo Estocástico)
# =====================================================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (2024 e 2025)
set P; # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)
set S; # Conjunto de Cenários (omega)

# PARÂMETROS AGRÍCOLAS 
param pi{S}; # Adicionando a probabilidade do cenário omega ocorrer (pi_omega)

param alfa{M};                     # Rendimento de óleo por matéria-prima
param beta_trans := 0.02;          # Perda física no transporte (2%)
param beta_arm   := 0.01;          # Perda física na armazenagem (1%)
param beta_proc  := 0.015;         # Perda física no esmagamento (1.5%)

param gama{P, M, T, S};            # Produtividade agrícola [t/ha]
param D{T, S};                     # Demanda total de biodiesel/óleo
param v_cost{T, S};      

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
param Custo_Fixo_OGR{R};           # Custo fixo para contratar a rede de OGR r

# PARÂMETROS DE PREÇO E RECEITAS [R$]
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
param Custo_Estoque_Semente{M};       # Custo de armazenagem de sementes [R$/t]
param penalidade_deficit := 8000.0;  # Penalidade pelo não atendimento da demanda

# VARIÁVEIS DE 1º ESTÁGIO (Decisões Estruturais)
var z{P, M, T} >= 0;                  # Área de terra alocada por matéria-prima [ha]
var y_polo{P, T} binary;              # 1 se o polo agrícola p for aberto no período t
var y_ogr{R, T} binary;               # 1 se a rede de OGR r for contratada no período t

# VARIÁVEIS DE 2º ESTÁGIO (Decisões Operacionais por Cenário)
var gx{P, M, T, S} >= 0;
var ogr_x{R, T, S} >= 0;
var w{M, T, S} >= 0;
var v{T, S} >= 0;
var estoque_semente{M, T, S} >= 0;
var deficit{T, S} >= 0;

# FUNÇÃO OBJETIVO: Maximizar o Lucro Esperado ponderado por pi[s]
maximize Lucro_Esperado:
    - sum{p in P, t in T} (Custo_Fixo_Polo[p] * y_polo[p,t])
    - sum{r in R, t in T} (Custo_Fixo_OGR[r] * y_ogr[r,t])
    - sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t])
    + sum{s in S} pi[s] * (
        sum{t in T} (
            preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s])
            + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
            + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
        )
        - sum{t in T} (
            sum{p in P, m in M} (GTC[p] * gx[p,m,t,s])
            + sum{m in M} (CC * w[m,t,s])
            + sum{r in R} (C_OGR[r] * ogr_x[r,t,s])
            + v_cost[t,s] * v[t,s]
            + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s])
            + penalidade_deficit * deficit[t,s]
        )
    );

# ===============================================================================================================
# RESTRIÇÕES DO SISTEMA
# ===============================================================================================================

# ====================== RESTRIÇÕES DE 1º ESTÁGIO =================================

# Restrição (2) determina o limite da área agrícola. Só existe plantação se o polo estiver aberto
# Se o modelo decidir não abrir o polo (y_polo[p,t] = 0), o limite de plantio é multiplicado por zero, forçando a área plantada (z) a ser 0. 
# Se o polo estiver aberto (y_polo[p,t] = 1), a área plantada pode crescer até atingir o teto máximo de terra disponível (Z_barra).

s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];
# ====================================================================================

# Restrição (3), garante o cumprimento do Selo Social. 
# Total de famílias inseridas no programa (calculado pela área total / lote médio familiar) deve atingir a meta mínima.
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];
# ==============================================================================

# =========== RESTRIÇÕES DE 2º ESTÁGIO (Replicadas para os 27 cenários) =============

# Restrição (4), atendimento da demanda sob incerteza. Garante que a soma do óleo extraído do esmagamento 
# (descontada a perda industrial), do OGR processado, do óleo de terceiros e do eventual déficit atinja a demanda estocástica do período t no cenário s.
s.t. Atendimento_Demanda{t in T, s in S}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s] + deficit[t,s] >= D[t,s];
# ====================================================================================

# Restrição (5), determina o balanço de massa. Estabelece que o volume total de sementes transportados até a usina em cada cenário -
# - corresponde a colheira bruta abatida da taxa de perda em transporte.
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T, s in S}:
    gx[p,m,t,s] = (1 - beta_trans) * gama[p,m,t,s] * z[p,m,t];
# =======================================================================================

# Restrição (6), determina o balanço de estoque incicial de sementes (t = 2024) para cada cenário s.
s.t. Balanco_Estoque_Inicial{m in M, s in S}:
    estoque_semente[m, 2024, s] = sum{p in P} gx[p, m, 2024, s] * (1 - beta_arm) - w[m, 2024, s];
# =====================================================================================

# Restrição (7), determina o balanço de massa subsequente (t > 2024) para cada cenário s.
s.t. Balanco_Estoque_Subsequente{m in M, t in T, s in S: t > 2024}:
    estoque_semente[m, t, s] = estoque_semente[m, t-1, s] 
                             + sum{p in P} gx[p, m, t, s] * (1 - beta_arm) 
                             - w[m, t, s];
# ======================================================================================

# Restrição (8), determina a capacidade industrial de esmagamento em cada cenário.
# A soma de todas as sementes enviadas para o esmagamento industrial no ano t, no cenário s, não pode ultrapassar a capacidade da usina.
s.t. Capacidade_Industrial{t in T, s in S}:
    sum{m in M} w[m,t,s] <= Capacidade_Usina;
# =======================================================================================

# Restrição (9) estabelece o percentual mínimo de OGR (14%) exigido por lei em relação à demanda do cenário.
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] >= 0.14 * D[t,s];
# =======================================================================================

# Restrição (10) garante a disponibilidade máxima de OGR em cada cenário.
# Garante que a compra de OGR respeite o teto de oferta local de cada rede e só ocorra se a respectiva parceria for contratada (y_ogr[r,t] = 1).
s.t. Disponibilidade_Max_OGR{r in R, t in T, s in S}:
    ogr_x[r,t,s] <= OfertaOGR[r,t] * y_ogr[r,t];
# ======================================================================================

# Restrição (11) limita a aquisição de óleo externo por cenário. 
# Limita a dependência de fornecedores externos ao teto operacional fixado para o período.
s.t. Teto_Compra_Externa{t in T, s in S}:
    v[t,s] <= CompraMax[t];
# =======================================================================================

# Restrição (12) limita a capacidade de descarga na usina em cada cenário. 
# Limita o fluxo físico de recepção e moega na fábrica frente aos limites logísticos.
s.t. Limite_Descarga_Usina{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Descarga[t];
# ======================================================================================

# Restrição (13) limita a capacidade do Parque de Silos em cada cenário. 
# Limita a quantidade máxima acumulada de sementes nos silos da planta.
s.t. Limite_Armazenagem_Silos{t in T, s in S}:
    sum{m in M} estoque_semente[m,t,s] <= Cap_Armazenagem[t];
# ======================================================================================

# Restrição (14) limita a capacidade da frota de caminhões em cada cenário. 
# Limita o volume máximo de sementes transportadas das roças à fábrica pelo teto da frota disponível.
s.t. Limite_Frota_Caminhoes{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Frota_Caminhoes[t];

# ======================================================================================

# Restrição (15) limita a capacidade de expedição e carregamento em cada cenário. 
# Limita o volume total escoado de biodiesel expedido em carretas no carregamento da usina.
s.t. Limite_Carregamento_Expedicao{t in T, s in S}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s]) <= Cap_Carregamento[t];

# ========================================================================================
# ==========================================================================================
