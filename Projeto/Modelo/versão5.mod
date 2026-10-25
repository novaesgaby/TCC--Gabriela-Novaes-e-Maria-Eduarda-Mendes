# ============================================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 5: MILP / ESTRATÉGICO)
# ============================================================================================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (2024 e 2025)
set P; # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R; # Fontes de Óleos e Gorduras Residuais (OGR)
set M; # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)

# PARÂMETROS
param alfa{M};                     # Rendimento de óleo específico para cada matéria-prima m
param beta_trans := 0.02;          # Perda física no transporte (2%)
param beta_arm   := 0.01;          # Perda física na armazenagem (1%)
param beta_proc  := 0.015;         # Perda física no esmagamento (1.5%)
param gama{P, M, T};               # Produtividade agrícola
param AZ{P, T};                    # Tamanho médio dos lotes das famílias
param Z_barra{P, M, T};            # Área máxima disponível para cultivo
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

# NOVOS PARÂMETROS ESTRATÉGICOS (Sugestão 10)
param Custo_Fixo_Polo{P};          # Custo fixo para abrir/manter um polo agrícola p
param Custo_Fixo_OGR{R};           # Custo fixo para contratar/parceirizar a rede de OGR r
param M_big := 1000000.0;          # Constante Big-M para restrições condicionais

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

# VARIÁVEIS DE DECISÃO CONTÍNUAS
var z{P, M, T} >= 0;               # Área de terra alocada por matéria-prima
var gx{P, M, T} >= 0;              # Volume de sementes transportadas
var ogr_x{R, T} >= 0;              # Volume de OGR adquirido
var w{M, T} >= 0;                  # Total de sementes líquidas trituradas
var v{T} >= 0;                     # Óleo complementar adquirido do mercado

# NOVAS VARIÁVEIS DE DECISÃO BINÁRIAS (Sugestão 10 - MILP)
var y_polo{P, T} binary;           # 1 se o polo agrícola p for aberto no período t, 0 caso contrário
var y_ogr{R, T} binary;            # 1 se a rede de OGR r for contratada no período t, 0 caso contrário

# ==================================================================================================================================
# FUNÇÃO OBJETIVO: Maximizar o Lucro Total (Incluindo custos fixos estratégicos)
# ==================================================================================================================================
maximize Lucro_Total:
    # 1. RECEITAS
    sum{t in T} (preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t])) +
    sum{m in M, t in T} (preco_farelo[m] * rend_farelo[m] * w[m,t]) +
    sum{t in T} (preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) +
    sum{t in T} (preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])) -

    # 2. CUSTOS (Operacionais + Fixos de Abertura Estratégica)
    (
        sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t]) +
        sum{p in P, m in M, t in T} (GTC[p] * gx[p,m,t]) +
        sum{m in M, t in T} (CC * w[m,t]) +
        sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) +
        sum{t in T} (v_cost[t] * v[t]) +
        # Custos fixos das binárias estratégicas
        sum{p in P, t in T} (Custo_Fixo_Polo[p] * y_polo[p,t]) +
        sum{r in R, t in T} (Custo_Fixo_OGR[r] * y_ogr[r,t])
    );

# ==============================================================================
# RESTRIÇÕES DO SISTEMA
# ==============================================================================

# Restrição (2) se dá pelo atendimento da demanda. Garante que a soma do óleo extraído do esmagamento agrícola
# (descontada a perda industrial proc), do OGR processado e do óleo de terceiros atinja a demanda total do período t.  
s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];
# ==================================================================================================================================

# Restrição (3), determina o limite da área agrícola. Só existe plantação se o polo estiver aberto
# Se o modelo decidir não abrir o polo (y_polo[p,t] = 0), o limite de plantio é multiplicado por zero, forçando a área plantada (z) a ser 0. 
# Se o polo estiver aberto (y_polo[p,t] = 1), a área plantada pode crescer até atingir o teto máximo de terra disponível (Z_barra).
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];
# ==================================================================================================================================

# Restrição (4), leva em consideração o cumprimento do Selo Biocombustível Social.
# O total de famílias inseridas no programa (calculado pela área total dividida pelo lote médio familiar) deve atingir a meta mínima. 
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];
# ==================================================================================================================================

# Restrição (5) determina o balanço de massa agrícola.
# Estabelece que o volume total de sementes transportadas até a usina corresponde à colheita bruta abatida da taxa de perda em transporte.
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

# ==================================================================================================================================

# Restrição (6)
s.t. Balanco_Processamento_Armazenagem{m in M, t in T}:
    w[m,t] = (1 - beta_arm) * sum{p in P} gx[p,m,t];
# ==================================================================================================================================

#  Restrição (7) determina a capacidade industrial de esmagamento
# A soma de todas as sementes enviadas para o esmagamento industrial no ano t não pode ultrapassar a capacidade
s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;
# ==================================================================================================================================

# Restrição (8) estabelece o percentual mínimo de OGR(14%).
s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t];
# ==================================================================================================================================

# Restrição (9) garante a disponibilidade máxima de OGR.
# Garante que a compra de OGR respeite o teto de oferta local de cada rede e só ocorra se a respectiva parceria for contratada (y_ogrr,t=1). 
s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t] * y_ogr[r,t];
# ==================================================================================================================================

# Restrição (10) limita a aquisição de óleo externo. Limita a dependência de fornecedores externos ao teto operacional fixado para o período. 
# Limita a qtd máxima de óleo comprado pronto de terceiro
s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];
# ==================================================================================================================================

# Restrição (11) limita a capacidade de descarga na usina. Limita o fluxo físico diário/anual de recepção e moega na fábrica
# Restrições Logísticas: limite de descarga / capacidade caminhões
s.t. Limite_Descarga_Usina{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Descarga[t];
# ==================================================================================================================================

# Restrição (12) limita a capacidade do Parque de Silos. Limita a quantidade máxima acumulada de sementes nos silos da planta. 
s.t. Limite_Armazenagem_Silos{t in T}:
    sum{p in P, m in M} ((1 - beta_trans) * gama[p,m,t] * z[p,m,t]) <= Cap_Armazenagem[t];
# ==================================================================================================================================

# Restrição (13) limita a capacidade da frota de caminhões. Limita o volume máximo de sementes transportadas das roças à fábrica pelo teto da frota disponível.
s.t. Limite_Frota_Caminhoes{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Frota_Caminhoes[t];
# ==================================================================================================================================

# Restrição (14) limita a capacidade de expedição e carregamento. Limita o volume total escoado de biodiesel expedido em carretas no carregamento da usina.
s.t. Limite_Carregamento_Expedicao{t in T}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t]) <= Cap_Carregamento[t];
# ==================================================================================================================================
# ==================================================================================================================================

