# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO Determinística)
# ========================================================================================================================

# CONJUNTOS (Índices)

set T := 1..24; # Períodos de tempo 
set P;          # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R;          # Fontes de Óleos e Gorduras Residuais (OGR)
set M;          # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)

# PARÂMETROS AGRÍCOLAS 
param alfa{M};                     # Rendimento de óleo por matéria-prima
param beta_trans := 0.02;          # Perda física no transporte (2%)
param beta_arm   := 0.01;          # Perda física na armazenagem (1%)
param beta_proc  := 0.015;         # Perda física no esmagamento (1.5%)

param gama{P, M, T};               # Produtividade agrícola [t/ha]
param D{T};                        # Demanda total de biodiesel
param v_cost{T};                   # Custo de aquisição de óleo externo 

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
param preco_biodiesel;             # Valor de venda do produto final 
param preco_farelo{M};             # Coproduto, no qual gera receita adicional para a Usina
param rend_farelo{M};              # Rendimento do Coproduto de cada Matéria-prima
param preco_glicerina;             # Coproduto gerado através do processo químico de transesterificação
param rend_glicerina;              # Rendimento do Coproduto de Glicerina
param preco_carbono;               # Valor adquirido pelos créditos de descarbonização (bônus financeiro ambiental)

# PARÂMETROS DE CUSTO OPERACIONAL [R$]
param PC{P, M};                        # Custo de cultivo [R$/ha]
param GTC{P};                          # Custo de transporte de grãos [R$/t]
param CC;                              # Custo de esmagamento/processamento [R$/t]
param C_OGR{R};                        # Custo de aquisição de OGR [R$/t]
param Custo_Estoque_Semente{M};        # Custo de armazenagem de sementes [R$/t]
param penalidade_deficit default preco_biodiesel * 1.2;  # Penalidade pelo não atendimento da demanda

# VARIÁVEIS DE DECISÃO (Sem a dimensão de cenários)
var z{P, M, T} >= 0;                   # Área de terra alocada por matéria-prima [ha]
var y_polo{P, T} binary;               # 1 se o polo agrícola p for aberto no período t
var y_ogr{R, T} binary;                # 1 se a rede de OGR r for contratada no período t

var gx{P, M, T} >= 0;                  # Quantidade de sementes (t)
var ogr_x{R, T} >= 0;                  # Volume de óleo adquirido de OGR 
var w{M, T} >= 0;                      # Quantidade de matéria-prima esmagada/triturada (t)
var v{T} >= 0;                         # Oléo comprado do mercado (terceiro/externo)
var estoque_semente{M, T} >= 0;        # Estoque das sementes/matéria-prima
var deficit{T} >= 0;                   # Perda de venda da demanda 
var sub_ogr{t in T} >= 0;              # Variável para suprir o mínimo de oléo OGR, caso falte OGR

# FUNÇÃO OBJETIVO: Maximizar o Lucro Total Determinístico
maximize Lucro_Total:
    - sum{p in P, t in T} (Custo_Fixo_Polo[p] * y_polo[p,t])
    - sum{r in R, t in T} (Custo_Fixo_OGR[r] * y_ogr[r,t])
    - sum{p in P, m in M, t in T} (PC[p,m] * z[p,m,t])
    + sum{t in T} (
        preco_biodiesel * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t])
        + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t])
        + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])
        + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t])
    )
    - sum{t in T} (
        sum{p in P, m in M} (GTC[p] * gx[p,m,t])
        + sum{m in M} (CC * w[m,t])
        + sum{r in R} (C_OGR[r] * ogr_x[r,t])
        + v_cost[t] * v[t]
        + v_cost[t] * sub_ogr[t]  # Custo do óleo vegetal substituto para a cota de OGR
        + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t])
        + penalidade_deficit * deficit[t]
    );

# ====================================================================================================================================
#                                               RESTRIÇÕES DO SISTEMA
# ====================================================================================================================================


# Restrição (2) determina o limite da área agrícola. Só existe plantação se o polo estiver aberto
# Se o modelo decidir não abrir o polo (y_polo[p,t] = 0), o limite de plantio é multiplicado por zero, forçando a área plantada (z) a ser 0. 
# Se o polo estiver aberto (y_polo[p,t] = 1), a área plantada pode crescer até atingir o teto máximo de terra disponível (Z_barra).

s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];
# =====================================================================================================================================

# Restrição (3), garante o cumprimento do Selo Social. 
# Total de famílias inseridas no programa (calculado pela área total / lote médio familiar) deve atingir a meta mínima.
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];
# =====================================================================================================================================


# Restrição (4), atendimento da demanda. Garante que a soma do óleo extraído do esmagamento 
# (descontada a perda industrial), do OGR processado, do óleo de terceiros e do eventual déficit atinja a demanda do período t.
s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] + deficit[t] >= D[t];
# =====================================================================================================================================

# Restrição (5), determina o balanço de massa. Estabelece que o volume total de sementes transportados até a usina -
# - corresponde a colheira bruta abatida da taxa de perda em transporte.
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];
# =====================================================================================================================================

# Restrição (6), determina o balanço de estoque inicial no primeiro período (t = 1).
s.t. Balanco_Estoque_Inicial{m in M}:
    estoque_semente[m, 1] = sum{p in P} gx[p, m, 1] * (1 - beta_arm) - w[m, 1];
# =====================================================================================================================================

# Restrição (7), determina o balanço de massa subsequente (t > 1).
s.t. Balanco_Estoque_Subsequente{m in M, t in T: t > 1}:
    estoque_semente[m, t] = estoque_semente[m, t-1] 
                         + sum{p in P} gx[p, m, t] * (1 - beta_arm) 
                         - w[m, t];
# =====================================================================================================================================

# Restrição (8), determina a capacidade industrial de esmagamento.
# A soma de todas as sementes enviadas para o esmagamento industrial no ano t não pode ultrapassar a capacidade da usina.
s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;
# =====================================================================================================================================

# Restrição (9) estabelece o percentual mínimo de OGR (14%) exigido por lei em relação à demanda.
# Garante 14% de OGR ou insumo substituto equivalente em caso de escassez
s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] + sub_ogr[t] >= 0.14 * D[t];
# =====================================================================================================================================

# Restrição (10) garante a disponibilidade máxima de OGR.
# Garante que a compra de OGR respeite o teto de oferta local de cada rede e só ocorra se a respectiva parceria for contratada (y_ogr[r,t] = 1).
s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t] * y_ogr[r,t];
# =====================================================================================================================================

# Restrição (11) limita a aquisição de óleo externo. 
# Limita a dependência de fornecedores externos ao teto operacional fixado para o período.
s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];
# =====================================================================================================================================

# Restrição (12) limita a capacidade de descarga na usina. 
# Limita o fluxo físico de recepção e moega na fábrica frente aos limites logísticos.
s.t. Limite_Descarga_Usina{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Descarga[t];
# =====================================================================================================================================

# Restrição (13) limita a capacidade do Parque de Silos. 
# Limita a quantidade máxima acumulada de sementes nos silos da planta.
s.t. Limite_Armazenagem_Silos{t in T}:
    sum{m in M} estoque_semente[m,t] <= Cap_Armazenagem[t];
# =====================================================================================================================================

# Restrição (14) limita a capacidade da frota de caminhões. 
# Limita o volume máximo de sementes transportadas das roças à fábrica pelo teto da frota disponível.
s.t. Limite_Frota_Caminhoes{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Frota_Caminhoes[t];
# =====================================================================================================================================

# Restrição (15) limita a capacidade de expedição e carregamento. 
# Limita o volume total escoado de biodiesel expedido em carretas no carregamento da usina.
s.t. Limite_Carregamento_Expedicao{t in T}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t]) <= Cap_Carregamento[t];
