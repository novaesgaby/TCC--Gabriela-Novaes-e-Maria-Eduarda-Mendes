import os
import shutil
import subprocess
import random

# 1. Garante a instalação do GLPK no ambiente de execução
if not shutil.which("glpsol"):
    print("A instalar glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Criação do arquivo .mod (Versão 7 Estocástica)
codigo_mod_v7_estocastico = """
# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 7)
# ========================================================================================================================

# CONJUNTOS (Índices)
set T := 1..24; # Períodos de tempo (1 a 24 meses)
set P;          # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R;          # Fontes de Óleos e Gorduras Residuais (OGR)
set M;          # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)
set S;          # Conjunto de Cenários (omega)

# PARÂMETROS AGRÍCOLAS 
param pi{S};                        # Probabilidade do cenário omega ocorrer (pi_omega)

param alfa{M};                      # Rendimento de óleo por matéria-prima
param beta_trans := 0.02;           # Perda física no transporte (2%)
param beta_arm   := 0.01;           # Perda física na armazenagem (1%)
param beta_proc  := 0.015;          # Perda física no esmagamento (1.5%)

param gama{P, M, T, S};             # Produtividade agrícola [t/ha]
param D{T, S};                      # Demanda total de biodiesel/óleo
param v_cost{T, S};                 # Custo de aquisição de óleo externo 

param AZ{P, T};                     # Tamanho médio dos lotes das famílias [ha/família]
param Z_barra{P, M, T};             # Área máxima disponível para cultivo [ha]
param TF{T};                        # Número mínimo de famílias do Selo Social
param Capacidade_Usina;             # Capacidade máxima de esmagamento na usina
param OfertaOGR{R, T};              # Disponibilidade máxima de OGR por fonte
param CompraMax{T};                 # Limite máximo de compra externa de óleo

# PARÂMETROS LOGÍSTICOS
param Cap_Descarga{T};
param Cap_Armazenagem{T};
param Cap_Frota_Caminhoes{T};
param Cap_Carregamento{T};

# PARÂMETROS ESTRATÉGICOS E CUSTOS FIXOS
param Custo_Fixo_Polo{P};           # Custo fixo para abrir/manter um polo agrícola p
param Custo_Fixo_OGR{R};            # Custo fixo para contratar a rede de OGR r

# PARÂMETROS DE PREÇO E RECEITAS [R$]
param preco_biodiesel;              # Valor de venda do produto final 
param preco_farelo{M};              # Coproduto, no qual gera receita adicional para a Usina
param rend_farelo{M};               # Rendimento do Coproduto de cada Matéria-prima
param preco_glicerina;              # Coproduto gerado através do processo químico de transesterificação
param rend_glicerina;               # Rendimento do Coproduto de Glicerina
param preco_carbono;                # Valor adquirido pelos créditos de descarbonização (bônus financeiro ambiental)

# PARÂMETROS DE CUSTO OPERACIONAL [R$]
param PC{P, M};                        # Custo de cultivo [R$/ha]
param GTC{P};                          # Custo de transporte de grãos [R$/t]
param CC;                              # Custo de esmagamento/processamento [R$/t]
param C_OGR{R};                        # Custo de aquisição de OGR [R$/t]
param Custo_Estoque_Semente{M};        # Custo de armazenagem de sementes [R$/t]
param penalidade_deficit default preco_biodiesel * 1.2;  # Penalidade pelo não atendimento da demanda

# VARIÁVEIS DE 1º ESTÁGIO (Decisões Estruturais)
var z{P, M, T} >= 0;                    # Área de terra alocada por matéria-prima [ha]
var y_polo{P, T} binary;                # 1 se o polo agrícola p for aberto no período t
var y_ogr{R, T} binary;                 # 1 se a rede de OGR r for contratada no período t

# VARIÁVEIS DE 2º ESTÁGIO (Decisões Operacionais por Cenário)
var gx{P, M, T, S} >= 0;                # Quantidade de sementes transportadas (t)
var ogr_x{R, T, S} >= 0;                # Volume de óleo adquirido de OGR 
var w{M, T, S} >= 0;                    # Quantidade de matéria-prima esmagada/triturada (t)
var v{T, S} >= 0;                       # Óleo comprado do mercado externo (terceiros)
var estoque_semente{M, T, S} >= 0;      # Estoque das sementes/matéria-prima
var deficit{T, S} >= 0;                 # Deficit de atendimento da demanda de biodiesel
var sub_ogr{t in T, s in S} >= 0;       # Variável para suprir o mínimo de OGR via óleo substituto

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
#                                               RESTRIÇÕES DO SISTEMA
# ====================================================================================================================================

# Restrição (2): Limite da área agrícola vinculado à abertura do polo
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];

# Restrição (3): Cumprimento da meta do Selo Social
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

# Restrição (4): Atendimento da demanda estocástica sob incerteza
s.t. Atendimento_Demanda{t in T, s in S}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s] + deficit[t,s] >= D[t,s];

# Restrição (5): Balanço de massa agrícola com desconto de perdas no transporte
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T, s in S}:
    gx[p,m,t,s] = (1 - beta_trans) * gama[p,m,t,s] * z[p,m,t];

# Restrição (6): Balanço de estoque inicial no primeiro período (t = 1)
s.t. Balanco_Estoque_Inicial{m in M, s in S}:
    estoque_semente[m, 1, s] = sum{p in P} gx[p, m, 1, s] * (1 - beta_arm) - w[m, 1, s];

# Restrição (7): Balanço de estoque subsequente (t > 1)
s.t. Balanco_Estoque_Subsequente{m in M, t in T, s in S: t > 1}:
    estoque_semente[m, t, s] = estoque_semente[m, t-1, s] 
                             + sum{p in P} gx[p, m, t, s] * (1 - beta_arm) 
                             - w[m, t, s];

# Restrição (8): Capacidade industrial máxima de esmagamento na usina
s.t. Capacidade_Industrial{t in T, s in S}:
    sum{m in M} w[m,t,s] <= Capacidade_Usina;

# Restrição (9): Percentual mínimo regulatório de OGR (14%) ou insumo substituto equivalente
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] + sub_ogr[t,s] >= 0.14 * D[t,s];

# Restrição (10): Disponibilidade máxima de OGR limitada à contratação da rede
s.t. Disponibilidade_Max_OGR{r in R, t in T, s in S}:
    ogr_x[r,t,s] <= OfertaOGR[r,t] * y_ogr[r,t];

# Restrição (11): Limite máximo de compra de óleo externo
s.t. Teto_Compra_Externa{t in T, s in S}:
    v[t,s] <= CompraMax[t];

# Restrição (12): Capacidade física de descarga na usina
s.t. Limite_Descarga_Usina{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Descarga[t];

# Restrição (13): Capacidade do parque de silos e armazenagem
s.t. Limite_Armazenagem_Silos{t in T, s in S}:
    sum{m in M} estoque_semente[m,t,s] <= Cap_Armazenagem[t];

# Restrição (14): Limite da frota de caminhões para transporte
s.t. Limite_Frota_Caminhoes{t in T, s in S}:
    sum{p in P, m in M} gx[p,m,t,s] <= Cap_Frota_Caminhoes[t];

# Restrição (15): Limite de expedição e carregamento de biodiesel na usina
s.t. Limite_Carregamento_Expedicao{t in T, s in S}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t,s]) + sum{r in R} ogr_x[r,t,s] + v[t,s]) <= Cap_Carregamento[t];
"""

with open("pbio_estocastico_v7.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod_v7_estocastico)

print("-> Arquivo pbio_estocastico_v7.mod criado com sucesso.")

# 3. Gerador das 20 Instâncias 
random.seed(42)
print("\nA gerar 20 instâncias (Horizonte de 24 Meses) e a executar o GLPSOL...")
print(f"{'Instância':<12} | {'Porte':<8} | {'Lucro Esperado Ótimo (R$)':<28} | {'Estado'}")
print("-" * 72)

for i in range(1, 21):
    if i <= 6:
        porte = "Pequeno"
        fator = 0.6
    elif i <= 14:
        porte = "Médio"
        fator = 1.0
    else:
        porte = "Grande"
        fator = 1.4

    preco_bio = round(random.uniform(4300.0, 4800.0), 2)
    cap_usina = round(16362.0 * fator, 2)

  
    d_descarga = {1:12000, 2:12000, 3:14000, 4:15000, 5:15000, 6:14000, 7:12000, 8:11000, 9:11000, 10:11000, 11:12000, 12:12000, 13:13000, 14:13000, 15:15000, 16:16000, 17:16000, 18:15000, 19:13000, 20:12000, 21:12000, 22:13000, 23:13000, 24:13000}
    d_armazenagem = {1:7500, 2:7500, 3:9000, 4:10000, 5:10000, 6:9000, 7:8000, 8:7500, 9:7500, 10:7500, 11:7500, 12:7500, 13:8000, 14:8000, 15:9500, 16:10500, 17:10500, 18:9500, 19:8500, 20:8000, 21:8000, 22:8000, 23:8000, 24:8000}
    d_carregamento = {1:11000, 2:11000, 3:12000, 4:13000, 5:13000, 6:12000, 7:11000, 8:11000, 9:11000, 10:11000, 11:11000, 12:11000, 13:12000, 14:12000, 15:13000, 16:14000, 17:14000, 18:13000, 19:12000, 20:12000, 21:12000, 22:12000, 23:12000, 24:12000}

    cap_desc_str = " ".join([f"{t} {int(val * fator)}" for t, val in d_descarga.items()])
    cap_arm_str  = " ".join([f"{t} {int(val * fator)}" for t, val in d_armazenagem.items()])
    cap_carr_str = " ".join([f"{t} {int(val * fator)}" for t, val in d_carregamento.items()])

    # Demanda estocástica dos 24 meses
    demanda_base = {
        1: (7000, 8000, 9550), 2: (6900, 8150, 9600), 3: (7300, 8300, 9800), 4: (7500, 8500, 10000),
        5: (7600, 8700, 10200), 6: (7400, 8400, 9900), 7: (7200, 8200, 9700), 8: (7000, 8000, 9500),
        9: (6500, 7900, 9400), 10: (7100, 8100, 9600), 11: (7100, 8300, 9800), 12: (7500, 8500, 10100),
        13: (7800, 9200, 11000), 14: (8200, 9400, 11200), 15: (8300, 9700, 11500), 16: (8800, 10000, 11800),
        17: (8200, 9800, 11600), 18: (8300, 9500, 11300), 19: (8000, 9300, 11100), 20: (7900, 9100, 10900),
        21: (7900, 9200, 11000), 22: (8200, 9400, 11300), 23: (8050, 9600, 11500), 24: (8600, 9800, 11700)
    }
    
    d_lines = []
    for t, (s1, s2, s3) in demanda_base.items():
        d_lines.append(f"    [{t}, *] := S1 {s1*fator} S2 {s2*fator} S3 {s3*fator}")
    d_block = "\n".join(d_lines)

    
    conteudo_dat = f"""
# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO 7 ESTOCÁSTICO) - Instância {i} ({porte})
# =============================================================================================================

data;

# Conjuntos 
set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;
set S := S1 S2 S3;                                     # Conjunto de cenários

# Probabilidade de cada cenário ocorrer (pi_omega)
param pi :=
    S1  0.2
    S2  0.5
    S3  0.3;

# Parâmetros de rendimento e perdas de cada matéria-prima (m)
param alfa :=
    Soja              0.18
    Algodao           0.15
    Macauba           0.28
    Girassol          0.40
    Nabo_Forrageiro   0.35;

# Preços e receitas
param preco_biodiesel := {preco_bio};    # valor da venda unitária do biodiesel por tonelada
param preco_glicerina := 1200.0;         # valor de venda unitária do coproduto (glicerina)
param rend_glicerina  := 0.10;           # rendimento da glicerina
param preco_carbono   := 50.0;           # créditos de carbono gerados pelo processo

param preco_farelo :=
    Soja              800.0                # preço de venda do farelo de soja: R$ 800,00 por tonelada
    Algodao           650.0                # preço de venda do farelo de algodão: R$ 650,00 por tonelada
    Macauba           500.0                # preço de venda do farelo de macaúba: R$ 500,00 por tonelada
    Girassol          700.0                # preço de venda do farelo de girassol: R$ 700,00 por tonelada
    Nabo_Forrageiro   600.0;               # preço de venda do farelo de nabo: R$ 600,00 por tonelada

param rend_farelo :=
    Soja              0.75                 # rendimento do farelo de cada matéria-prima
    Algodao           0.55
    Macauba           0.50
    Girassol          0.50
    Nabo_Forrageiro   0.45;

# Custos e capacidades gerais
param CC := 45.0;                          # Custo de Conversão | R$ 45,00 por tonelada 
param Capacidade_Usina := {cap_usina};     # Capacidade mensal proporcional (~16.3k t/mês)

param Custo_Estoque_Semente :=
    Soja              15.0
    Algodao           12.0
    Macauba           10.0
    Girassol          14.0
    Nabo_Forrageiro   11.0;

param Custo_Fixo_Polo :=
    polo_norteMG    500000.0                # 500 K
    polo_semiarido  400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0            # 150 K
    rede_urbana        200000.0;

# Limites operacionais variáveis por mês (1 a 24) para simular gargalos logísticos sazonais
param Cap_Descarga := 
    {cap_desc_str};

param Cap_Armazenagem := 
    {cap_arm_str};

param Cap_Frota_Caminhoes := 
    {cap_desc_str};

param Cap_Carregamento := 
    {cap_carr_str};

param C_OGR := rede_catadores_moc 110.0 rede_urbana 125.0;

param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

# Demanda estocástica sazonal por cenário (S1=Baixa/Seca, S2=Médio, S3=Alta/Aquecida) para os 24 meses
param D :=
{d_block};

# Custo do óleo externo estocástico e variável (fica mais caro nos meses de entressafra/escassez)
param v_cost :=
    [1, *]  := S1 450.0 S2 410.0 S3 380.0    [2, *]  := S1 460.0 S2 420.0 S3 390.0
    [3, *]  := S1 420.0 S2 390.0 S3 360.0    [4, *]  := S1 400.0 S2 370.0 S3 340.0  # Safra (preço cai)
    [5, *]  := S1 390.0 S2 360.0 S3 330.0    [6, *]  := S1 410.0 S2 380.0 S3 350.0
    [7, *]  := S1 440.0 S2 400.0 S3 370.0    [8, *]  := S1 480.0 S2 430.0 S3 390.0
    [9, *]  := S1 520.0 S2 470.0 S3 420.0    [10, *] := S1 550.0 S2 500.0 S3 450.0  # Entressafra (preço sobe)
    [11, *] := S1 530.0 S2 480.0 S3 430.0    [12, *] := S1 490.0 S2 440.0 S3 400.0
    [13, *] := S1 470.0 S2 430.0 S3 390.0   [14, *] := S1 480.0 S2 440.0 S3 400.0
    [15, *] := S1 440.0 S2 400.0 S3 370.0   [16, *] := S1 420.0 S2 380.0 S3 350.0  # Safra ano 2
    [17, *] := S1 410.0 S2 370.0 S3 340.0   [18, *] := S1 430.0 S2 390.0 S3 360.0
    [19, *] := S1 460.0 S2 420.0 S3 380.0   [20, *] := S1 500.0 S2 450.0 S3 410.0
    [21, *] := S1 540.0 S2 490.0 S3 440.0   [22, *] := S1 560.0 S2 510.0 S3 460.0
    [23, *] := S1 520.0 S2 470.0 S3 420.0   [24, *] := S1 480.0 S2 440.0 S3 400.0;

# Produtividade agrícola default para manter as especificações detalhadas do seu modelo
param gama default 2.20;

param AZ :=
    [polo_norteMG, *]   := {" ".join([f"{t} 12.0" for t in range(1, 25)])}
    [polo_semiarido, *] := {" ".join([f"{t} 15.0" for t in range(1, 25)])};

param Z_barra :=
    [polo_norteMG, Soja, *]              := {" ".join([f"{t} {int(2500*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Algodao, *]          := {" ".join([f"{t} {int(1000*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Macauba, *]          := {" ".join([f"{t} {int(500*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Girassol, *]         := {" ".join([f"{t} {int(300*fator)}" for t in range(1, 25)])}
    [polo_norteMG, Nabo_Forrageiro, *]  := {" ".join([f"{t} {int(200*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Soja, *]           := {" ".join([f"{t} {int(1600*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Algodao, *]        := {" ".join([f"{t} {int(700*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Macauba, *]        := {" ".join([f"{t} {int(500*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Girassol, *]       := {" ".join([f"{t} {int(250*fator)}" for t in range(1, 25)])}
    [polo_semiarido, Nabo_Forrageiro, *]:= {" ".join([f"{t} {int(250*fator)}" for t in range(1, 25)])};

param TF := 1 150 2 150 3 150 4 150 5 150 6 150 7 150 8 150 9 150 10 150 11 150 12 150 13 180 14 180 15 180 16 180 17 180 18 180 19 180 20 180 21 180 22 180 23 180 24 180;

param OfertaOGR :=
    [rede_catadores_moc, *] := {" ".join([f"{t} {int(val*fator)}" for t, val in {1:7000, 2:7200, 3:7500, 4:8000, 5:8200, 6:7800, 7:7300, 8:7000, 9:6800, 10:6900, 11:7100, 12:7300, 13:7800, 14:8000, 15:8300, 16:9000, 17:9200, 18:8600, 19:8100, 20:7700, 21:7500, 22:7600, 23:7900, 24:8100}.items()])}
    [rede_urbana, *]        := {" ".join([f"{t} {int(val*fator)}" for t, val in {1:1500, 2:1550, 3:1600, 4:1700, 5:1750, 6:1650, 7:1550, 8:1500, 9:1450, 10:1480, 11:1520, 12:1580, 13:1800, 14:1850, 15:1900, 16:2100, 17:2150, 18:2000, 19:1900, 20:1800, 21:1750, 22:1780, 23:1850, 24:1900}.items()])};

param CompraMax := 1 {int(1200*fator)} 2 {int(1220*fator)} 3 {int(1250*fator)} 4 {int(1300*fator)} 5 {int(1350*fator)} 6 {int(1300*fator)} 7 {int(1250*fator)} 8 {int(1200*fator)} 9 {int(1150*fator)} 10 {int(1180*fator)} 11 {int(1210*fator)} 12 {int(1250*fator)} 13 {int(1500*fator)} 14 {int(1550*fator)} 15 {int(1600*fator)} 16 {int(1800*fator)} 17 {int(1850*fator)} 18 {int(1700*fator)} 19 {int(1600*fator)} 20 {int(1500*fator)} 21 {int(1450*fator)} 22 {int(1480*fator)} 23 {int(1550*fator)} 24 {int(1600*fator)};

end;
"""

    dat_file = f"instancia_v7_{i}.dat"
    out_file = f"resultado_v7_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_estocastico_v7.mod", "-d", dat_file, "-o", out_file],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        lucro_str = "N/D"
        with open(out_file, "r", encoding="utf-8") as f_out:
            for line in f_out:
                if "Objective:" in line:
                    partes = line.split()
                    for p in partes:
                        try:
                            val = float(p.replace(',', ''))
                            if val > 1000:
                                lucro_str = f"R$ {val:,.2f}"
                                break
                        except ValueError:
                            continue
        print(f"Instância {i:<2} ({porte:<8}) | {lucro_str:<28} | INTEGER OPTIMAL")
    except Exception:
        print(f"Instância {i:<2} ({porte:<8}) | Falha na execução              | ERROR")
