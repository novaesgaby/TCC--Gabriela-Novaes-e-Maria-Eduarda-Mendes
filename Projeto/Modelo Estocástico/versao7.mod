# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 7 - Modelo Estocástico)
# ========================================================================================================================

# CONJUNTOS (Índices)

set T := 1..24; # Períodos de tempo (1 a 24 meses - S&OP)
set P;          # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R;          # Fontes de Óleos e Gorduras Residuais (OGR)
set M;          # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)
set S;          # Conjunto de Cenários (omega)

# PARÂMETROS AGRÍCOLAS 
param pi{S};                       # Probabilidade do cenário omega ocorrer (pi_omega)

param alfa{M};                     # Rendimento de óleo por matéria-prima
param beta_trans := 0.02;          # Perda física no transporte (2%)
param beta_arm   := 0.01;          # Perda física na armazenagem (1%)
param beta_proc  := 0.015;         # Perda física no esmagamento (1.5%)

param gama{P, M, T, S};            # Produtividade agrícola [t/ha]
param D{T, S};                     # Demanda total de biodiesel
param v_cost{T, S};                # Custo de aquisição de óleo externo 

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
param PC{P, M};                       # Custo de cultivo [R$/ha]
param GTC{P};                         # Custo de transporte de grãos [R$/t]
param CC;                             # Custo de esmagamento/processamento [R$/t]
param C_OGR{R};                       # Custo de aquisição de OGR [R$/t]
param Custo_Estoque_Semente{M};       # Custo de armazenagem de sementes [R$/t]
param penalidade_deficit default preco_biodiesel * 1.2;  # Penalidade pelo não atendimento da demanda

# VARIÁVEIS DE 1º ESTÁGIO (Decisões Estruturais)
var z{P, M, T} >= 0;                  # Área de terra alocada por matéria-prima [ha]
var y_polo{P, T} binary;              # 1 se o polo agrícola p for aberto no período t
var y_ogr{R, T} binary;               # 1 se a rede de OGR r for contratada no período t

# VARIÁVEIS DE 2º ESTÁGIO (Decisões Operacionais por Cenário)
var gx{P, M, T, S} >= 0;                    # Quantidade de sementes (t)
var ogr_x{R, T, S} >= 0;                    # Volume de óleo adquirido de OGR 
var w{M, T, S} >= 0;                        # Quantidade de matéria-prima esmagada/triturada (t)
var v{T, S} >= 0;                           # Oléo comprado do mercado (terceiro/externo)
var estoque_semente{M, T, S} >= 0;          # Estoque das sementes/matéria-prima
var deficit{T, S} >= 0;                     # Perda de venda da demanda 
var sub_ogr{t in T, s in S} >= 0;           # Variável para suprir o mínimo de oléo OGR, caso falte OGR

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
                    + v_cost[t,s] * sub_ogr[t,s]  # Custo do óleo vegetal substituto para a cota de OGR
                    + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s])
                    + penalidade_deficit * deficit[t,s]
)
    );

# ====================================================================================================================================
#                                                       RESTRIÇÕES DO SISTEMA
# ====================================================================================================================================

# ==================================================== RESTRIÇÕES DE 1º ESTÁGIO ======================================================

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

# ==================================== RESTRIÇÕES DE 2º ESTÁGIO (Replicadas para os 27 cenários) ======================================

# Restrição (4), atendimento da demanda sob incerteza. Garante que a soma do óleo extraído do esmagamento 
# (descontada a perda industrial), do OGR processado, do óleo de terceiros e do eventual déficit atinja a demanda estocástica do período t no cenário s.
s.t. Atendimento_Demanda{t in T, s in S}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s] + deficit[t,s] >= D[t,s];
# =====================================================================================================================================

# Restrição (5), determina o balanço de massa. Estabelece que o volume total de sementes transportados até a usina em cada cenário -
# - corresponde a colheira bruta abatida da taxa de perda em transporte.
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T, s in S}:
    gx[p,m,t,s] = (1 - beta_trans) * gama[p,m,t,s] * z[p,m,t];
# =====================================================================================================================================

# Restrição (6), determina o balanço de estoque inicial no primeiro período (t = 1) para cada cenário s.
s.t. Balanco_Estoque_Inicial{m in M, s in S}:
    estoque_semente[m, 1, s] = sum{p in P} gx[p, m, 1, s] * (1 - beta_arm) - w[m, 1, s];
# =====================================================================================================================================

# Restrição (7), determina o balanço de massa subsequente (t > 1) para cada cenário s.
s.t. Balanco_Estoque_Subsequente{m in M, t in T, s in S: t > 1}:
    estoque_semente[m, t, s] = estoque_semente[m, t-1, s] 
                             + sum{p in P} gx[p, m, t, s] * (1 - beta_arm) 
                             - w[m, t, s];
# =====================================================================================================================================

# Restrição (8), determina a capacidade industrial de esmagamento em cada cenário.
# A soma de todas as sementes enviadas para o esmagamento industrial no ano t, no cenário s, não pode ultrapassar a capacidade da usina.
s.t. Capacidade_Industrial{t in T, s in S}:
    sum{m in M} w[m,t,s] <= Capacidade_Usina;
# =====================================================================================================================================

# Restrição (9) estabelece o percentual mínimo de OGR (14%) exigido por lei em relação à demanda do cenário.
# Garante 14% de OGR ou insumo substituto equivalente em caso de escassez
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] + sub_ogr[t,s] >= 0.14 * D[t,s];
# =====================================================================================================================================

# Restrição (10) garante a disponibilidade máxima de OGR em cada cenário.
# Garante que a compra de OGR respeite o teto de oferta local de cada rede e só ocorra se a respectiva parceria for contratada (y_ogr[r,t] = 1).
s.t. Disponibilidade_Max_OGR{r in R, t in T, s in S}:
    ogr_x[r,t,s] <= OfertaOGR[r,t] * y_ogr[r,t];
# =====================================================================================================================================

# Restrição (11) limita a aquisição de óleo externo por cenário. 
# Limita a dependência de fornecedores externos ao teto operacional fixado para o período.
s.t. Teto_Compra_Externa{t in T, s in S}:
    v[t,s] <= CompraMax[t];
# =====================================================================================================================================

# Restrição (12) limita a capacidade de descarga na usina em cada cenário. 
# Limita o fluxo físico de recepção e moega na fábrica frente aos limites logísticos.
s.t. Limite_Descarga_Usina{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Descarga[t];
# =====================================================================================================================================

# Restrição (13) limita a capacidade do Parque de Silos em cada cenário. 
# Limita a quantidade máxima acumulada de sementes nos silos da planta.
s.t. Limite_Armazenagem_Silos{t in T, s in S}:
    sum{m in M} estoque_semente[m,t,s] <= Cap_Armazenagem[t];
# =====================================================================================================================================

# Restrição (14) limita a capacidade da frota de caminhões em cada cenário. 
# Limita o volume máximo de sementes transportadas das roças à fábrica pelo teto da frota disponível.
s.t. Limite_Frota_Caminhoes{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Frota_Caminhoes[t];
# =====================================================================================================================================

# Restrição (15) limita a capacidade de expedição e carregamento em cada cenário. 
# Limita o volume total escoado de biodiesel expedido em carretas no carregamento da usina.
s.t. Limite_Carregamento_Expedicao{t in T, s in S}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s]) <= Cap_Carregamento[t];

# =====================================================================================================================================
# =====================================================================
# SOLUÇÃO DO MODELO
# =====================================================================
solve;

printf "\n\n";
printf "--------------------------------------------------------------------------------------------\n";
printf "                           Petrobras Biocombustível  | PLANEJAMENTO S&OP                    \n";
printf "--------------------------------------------------------------------------------------------\n";
printf "                                       RELATÓRIO DE RESULTADOS                              \n";
printf "                                         HORIZONTE: 24 MESES                                \n";
printf "--------------------------------------------------------------------------------------------\n";

# =====================================================================
# DECLARAÇÕES AUXILIARES PARA O RESUMO EXECUTIVO E TOTAIS
# =====================================================================
param total_lucro := sum{t in T, s in S} pi[s] * (
    sum{m in M} (preco_biodiesel * alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} (preco_biodiesel * ogr_x[r,t,s]) + preco_biodiesel * v[t,s]
    + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
    + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
    + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
    - (sum{p in P, m in M} GTC[p] * gx[p,m,t,s] + sum{m in M} CC * w[m,t,s] + sum{r in R} C_OGR[r] * ogr_x[r,t,s] + v_cost[t,s] * v[t,s] + sum{m in M} Custo_Estoque_Semente[m] * estoque_semente[m,t,s] + penalidade_deficit * deficit[t,s])
);

param total_transporte := sum{t in T, s in S, p in P, m in M} pi[s] * GTC[p] * gx[p,m,t,s];

param total_custo := sum{t in T, s in S} pi[s] * (
    sum{p in P, m in M} (GTC[p] * gx[p,m,t,s]) + sum{m in M} (CC * w[m,t,s]) + sum{r in R} (C_OGR[r] * ogr_x[r,t,s]) + v_cost[t,s] * v[t,s] + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s]) + penalidade_deficit * deficit[t,s]
);

param total_receita := total_lucro + total_custo;

param prod_total := sum{t in T} ((sum{s in S, m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s])) / card(S));
param dem_total  := sum{t in T} ((sum{s in S} D[t,s]) / card(S));
param def_total  := sum{t in T} ((sum{s in S} deficit[t,s]) / card(S));


# =====================================================================
# 0. RESUMO EXECUTIVO (TOPO DO RELATÓRIO)
# =====================================================================
printf "\n";
printf "----------------------------------------------------------------------------------------\n";
printf "|                                                                                      |\n";
printf "|                           RESULTADO ECONOMICO ESPERADO                               |\n";
printf "|                            R$ %12.2f milhões                                   |\n", total_lucro / 1000000;
printf "|                                                                                      |\n";
printf "|                                     RECEITA TOTAL                                    |\n";
printf "|                            R$ %12.2f milhões                                   |\n", total_receita / 1000000;
printf "|                                                                                      |\n";
printf "|                                      CUSTO TOTAL                                     |\n";
printf "|                            R$ %12.2f milhões                                   |\n", total_custo / 1000000;
printf "|                                                                                      |\n";
printf "|                       PRODUCAO TOTAL : %15.2f toneladas                     |\n", prod_total;
printf "|                       DEMANDA TOTAL  : %15.2f toneladas                     |\n", dem_total;
printf "|                       DEFICIT TOTAL  : %15.2f toneladas                     |\n", def_total;
printf "|                                                                                      |\n";
printf "----------------------------------------------------------------------------------------\n\n";


# =====================================================================
# 1. PAINEL EXECUTIVO DE PRODUÇÃO E LOGÍSTICA
# =====================================================================
printf "\n========================================================================================\n";
printf "                                 PAINEL 1: PRODUÇÃO, DEMANDA E LOGÍSTICA                  \n";
printf "========================================================================================\n\n";
printf " %-8s | %-14s  | %-14s | %-14s | %-14s | %-12s\n", 
    "PERIODO", "PRODUCAO (t)", "DEMANDA (t)", "COMPRA EXT. (t)", "SUBST. OGR (t)", "DEFICIT (t)";
printf "------------------------------------------------------------------------------------------\n";

for {t in T} {
    printf " Mes %-4d | %11.1f t   | %11.1f t   | %11.1f t   | %11.1f t   | %10.1f t\n", 
        t, 
        (sum{s in S, m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s])) / card(S),
        (sum{s in S} D[t,s]) / card(S),
        (sum{s in S} v[t,s]) / card(S),
        (sum{s in S} sub_ogr[t,s]) / card(S),
        (sum{s in S} deficit[t,s]) / card(S);
}

printf "----------------------------------------------------------------------------------------\n";
printf " %-8s |%13.1f t  | %13.1f t  | %13.1f t   | %12.1f t\n",
    "TOTAL",
    sum{t in T} ((sum{s in S, m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s])) / card(S)),
    sum{t in T} ((sum{s in S} D[t,s]) / card(S)),
    sum{t in T} ((sum{s in S} v[t,s]) / card(S)),
    sum{t in T} ((sum{s in S} deficit[t,s]) / card(S));
printf "========================================================================================\n\n";


# =====================================================================
# 2. PAINEL FINANCEIRO E ECONÔMICO
# =====================================================================
printf "\n=============================================================================\n";
printf "                                PAINEL 2: FINANCEIRO                           \n";
printf "=============================================================================\n\n";
printf " %-8s  | %-26s| %-24s|%-24s\n", "PERÍODO", "LUCRO LIQUIDO (R$)", "CUSTO TRANSP. (R$)", "CUSTO OP. REAL (R$)";
printf "--------------------------------------------------------------------------------\n";

for {t in T} {
    printf " Mes %-4d | R$ %3d.%03d.%03d,%02d", 
        t,
        (sum{s in S} pi[s] * (
            sum{m in M} (preco_biodiesel * alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} (preco_biodiesel * ogr_x[r,t,s]) + preco_biodiesel * v[t,s]
            + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
            + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            - (sum{p in P, m in M} GTC[p] * gx[p,m,t,s] + sum{m in M} CC * w[m,t,s] + sum{r in R} C_OGR[r] * ogr_x[r,t,s] + v_cost[t,s] * v[t,s] + sum{m in M} Custo_Estoque_Semente[m] * estoque_semente[m,t,s] + penalidade_deficit * deficit[t,s])
        )) div 1000000,
        ((sum{s in S} pi[s] * (
            sum{m in M} (preco_biodiesel * alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} (preco_biodiesel * ogr_x[r,t,s]) + preco_biodiesel * v[t,s]
            + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
            + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            - (sum{p in P, m in M} GTC[p] * gx[p,m,t,s] + sum{m in M} CC * w[m,t,s] + sum{r in R} C_OGR[r] * ogr_x[r,t,s] + v_cost[t,s] * v[t,s] + sum{m in M} Custo_Estoque_Semente[m] * estoque_semente[m,t,s] + penalidade_deficit * deficit[t,s])
        )) div 1000) mod 1000,
        (sum{s in S} pi[s] * (
            sum{m in M} (preco_biodiesel * alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} (preco_biodiesel * ogr_x[r,t,s]) + preco_biodiesel * v[t,s]
            + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
            + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            - (sum{p in P, m in M} GTC[p] * gx[p,m,t,s] + sum{m in M} CC * w[m,t,s] + sum{r in R} C_OGR[r] * ogr_x[r,t,s] + v_cost[t,s] * v[t,s] + sum{m in M} Custo_Estoque_Semente[m] * estoque_semente[m,t,s] + penalidade_deficit * deficit[t,s])
        )) mod 1000,
        ((sum{s in S} pi[s] * (
            sum{m in M} (preco_biodiesel * alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} (preco_biodiesel * ogr_x[r,t,s]) + preco_biodiesel * v[t,s]
            + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
            + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            - (sum{p in P, m in M} GTC[p] * gx[p,m,t,s] + sum{m in M} CC * w[m,t,s] + sum{r in R} C_OGR[r] * ogr_x[r,t,s] + v_cost[t,s] * v[t,s] + sum{m in M} Custo_Estoque_Semente[m] * estoque_semente[m,t,s] + penalidade_deficit * deficit[t,s])
        )) * 100) mod 100;

    printf "         |     R$ %3d.%03d.%03d,%02d",
        (sum{s in S, p in P, m in M} pi[s] * GTC[p] * gx[p,m,t,s]) div 1000000,
        ((sum{s in S, p in P, m in M} pi[s] * GTC[p] * gx[p,m,t,s]) div 1000) mod 1000,
        (sum{s in S, p in P, m in M} pi[s] * GTC[p] * gx[p,m,t,s]) mod 1000,
        ((sum{s in S, p in P, m in M} pi[s] * GTC[p] * gx[p,m,t,s]) * 100) mod 100;

    printf "        | R$ %3d.%03d.%03d,%02d\n",
        (sum{s in S} pi[s] * (
            sum{p in P, m in M} (GTC[p] * gx[p,m,t,s]) + sum{m in M} (CC * w[m,t,s]) + sum{r in R} (C_OGR[r] * ogr_x[r,t,s]) + v_cost[t,s] * v[t,s] + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s]) + penalidade_deficit * deficit[t,s]
        )) div 1000000,
        ((sum{s in S} pi[s] * (
            sum{p in P, m in M} (GTC[p] * gx[p,m,t,s]) + sum{m in M} (CC * w[m,t,s]) + sum{r in R} (C_OGR[r] * ogr_x[r,t,s]) + v_cost[t,s] * v[t,s] + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s]) + penalidade_deficit * deficit[t,s]
        )) div 1000) mod 1000,
        (sum{s in S} pi[s] * (
            sum{p in P, m in M} (GTC[p] * gx[p,m,t,s]) + sum{m in M} (CC * w[m,t,s]) + sum{r in R} (C_OGR[r] * ogr_x[r,t,s]) + v_cost[t,s] * v[t,s] + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s]) + penalidade_deficit * deficit[t,s]
        )) mod 1000,
        ((sum{s in S} pi[s] * (
            sum{p in P, m in M} (GTC[p] * gx[p,m,t,s]) + sum{m in M} (CC * w[m,t,s]) + sum{r in R} (C_OGR[r] * ogr_x[r,t,s]) + v_cost[t,s] * v[t,s] + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s]) + penalidade_deficit * deficit[t,s]
        )) * 100) mod 100;
}

printf "------------------------------------------------------------------------------------\n";

# Impressão do TOTAL em partes curtas
printf " TOTAL    | R$ %4d.%03d.%03d,%02d",
    total_lucro div 1000000000,
    (total_lucro div 1000000) mod 1000,
    (total_lucro div 1000) mod 1000,
    total_lucro mod 1000,
    (total_lucro * 100) mod 100;

printf "       | R$ %4d.%03d.%03d,%02d",
    total_transporte div 1000000000,
    (total_transporte div 1000000) mod 1000,
    (total_transporte div 1000) mod 1000,
    total_transporte mod 1000,
    (total_transporte * 100) mod 100;

printf "           | R$ %4d.%03d.%03d,%02d\n",
    total_custo div 1000000000,
    (total_custo div 1000000) mod 1000,
    (total_custo div 1000) mod 1000,
    total_custo mod 1000,
    (total_custo * 100) mod 100;

printf "===============================================================================\n\n";

# ==============================================================================
# RELATÓRIO EXECUTIVO DE ÁREA PLANTADA - MESES ESPECÍFICOS DE MARCO
# ==============================================================================
printf "\n";
printf "-----------------------------------------------------------------------------\n";
printf "|                   PAINEL 3: PLANO DE ALOCAÇÃO DE ÁREAS                      |\n";
printf "------------------------------------------------------------------------------\n";
printf "|  %-6s       |  %-16s|   %-18s       |  %10s    |\n", "MES", "POLO", "MATÉRIA-PRIMA", "ÁREA (ha)";
printf "------------------------------------------------------------------------------\n";

# Altere a lista {1, 4, 8, 12, 16, 20, 24} para os meses que quiser exibir
for {t in {1, 2, 3, 4,5, 6, 7, 8, 12, 16, 20, 24}, p in P, m in M: z[p,m,t] > 0} {
    printf "|  Mês %-5d    | %-16s |    %-18s      | %10.2f |\n", t, p, m, z[p,m,t];
}

printf "------------------------------------------------------------------------------\n\n";

# ==============================================================================
# EXPORTAÇÃO PARA TXT APENAS DOS MESES SELECIONADOS (OU MANTÉM COMPLETO)
# ==============================================================================
printf "MES\tPOLO\tMATERIA-PRIMA\tAREA_HA\n" > 'relatorio_ma.csv';
for {t in {1,2,3, 4, 5, 6, 7, 8, 12, 16, 20, 24}, p in P, m in M: z[p,m,t] > 0} {
    printf "%d\t%s\t%s\t%.2f\n", t, p, m, z[p,m,t] >> 'relatorio_ma.csv';
}

# =====================================================================
# 3. RECOMENDAÇÕES ESTRATÉGICAS
# =====================================================================
printf ">>  RECOMENDAÇÕES:\n";
printf "------------------------------------------------------------------------------------\n";
printf "|                         PLANO DE AÇÃO (S&OP)                                     |\n";
printf "--------------------------+-------------------------+-------------------------------\n";
printf "| 1. EXPANSAO DE SILOS    | 2. CONTRATOS DE OGR     | 3. LOGISTICA                 |\n";
printf "| Investimento focado no  | Trava de preço e volume | Modulacao contratual de      |\n";
printf "| destravamento do pico   | para expandir OGR alem  | frete no pico da safra       |\n";
printf "| de colheita (t=5 a t=7).| dos 14%% regulatorios.   | (evitar gargalo de descarga).|\n";
printf "--------------------------+-------------------------+-------------------------------\n\n";


printf "------------------------------------------------------------------------------------\n";
printf "status: Painel de resultados gerado com sucesso!\n";
printf "====================================================================================\n";

# =====================================================================
# EXPORTAÇÃO DE DADOS
# =====================================================================
printf "Periodo,Producao_t,Demanda_t,Compra_Ext_t,Lucro_RS,Custo_Transp_RS,Custo_Op_RS\n" > "dados_graficos.csv";

for {t in T} {
    printf "%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n", 
        t, 
        # 1. Produção média (t)
        (sum{s in S, m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s])) / card(S),
        # 2. Demanda média (t)
        (sum{s in S} D[t,s]) / card(S),
        # 3. Compra Externa / Óleo Externo médio (t)
        (sum{s in S} v[t,s]) / card(S),
        # 4. Lucro Líquido Esperado do Mês (R$)
        (sum{s in S} pi[s] * (
            sum{m in M} (preco_biodiesel * alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} (preco_biodiesel * ogr_x[r,t,s]) + preco_biodiesel * v[t,s]
            + sum{m in M} (preco_farelo[m] * rend_farelo[m] * w[m,t,s])
            + preco_glicerina * rend_glicerina * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            + preco_carbono * (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s])
            - (sum{p in P, m in M} GTC[p] * gx[p,m,t,s] + sum{m in M} CC * w[m,t,s] + sum{r in R} C_OGR[r] * ogr_x[r,t,s] + v_cost[t,s] * v[t,s] + sum{m in M} Custo_Estoque_Semente[m] * estoque_semente[m,t,s] + penalidade_deficit * deficit[t,s])
        )),
        # 5. Custo de Transporte do Mês (R$)
        (sum{s in S, p in P, m in M} pi[s] * GTC[p] * gx[p,m,t,s]),
        # 6. Custo Operacional Real Total do Mês (R$)
        (sum{s in S} pi[s] * (
            sum{p in P, m in M} (GTC[p] * gx[p,m,t,s]) + sum{m in M} (CC * w[m,t,s]) + sum{r in R} (C_OGR[r] * ogr_x[r,t,s]) + v_cost[t,s] * v[t,s] + sum{m in M} (Custo_Estoque_Semente[m] * estoque_semente[m,t,s]) + penalidade_deficit * deficit[t,s]
        ))
        >> "dados_graficos.csv";
}
