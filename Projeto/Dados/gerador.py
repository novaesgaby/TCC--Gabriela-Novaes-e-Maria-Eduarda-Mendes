import os
import shutil
import subprocess
import random

# 1. Garante a instalação do GLPK no ambiente de execução
if not shutil.which("glpsol"):
    print("A instalar glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Criação do arquivo .mod (Versão Determinística )
codigo_mod_deterministico = """
# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO Determinística)
# ========================================================================================================================

# CONJUNTOS (Índices)

set T := 1..24; # Períodos de tempo (1 a 24 meses)
set P;          # Zonas produtoras de oleaginosas (Norte de MG e Semiárido)
set R;          # Fontes de Óleos e Gorduras Residuais (OGR)
set M;          # Matérias-primas / Oleaginosas (Soja, Algodão, Macaúba, Girassol, Nabo)

# PARÂMETROS AGRÍCOLAS 
param alfa{M};                      # Rendimento de óleo por matéria-prima
param beta_trans := 0.02;           # Perda física no transporte (2%)
param beta_arm   := 0.01;           # Perda física na armazenagem (1%)
param beta_proc  := 0.015;          # Perda física no esmagamento (1.5%)

param gama{P, M, T};                # Produtividade agrícola [t/ha]
param D{T};                         # Demanda total de biodiesel
param v_cost{T};                    # Custo de aquisição de óleo externo 

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
param PC{P, M};                         # Custo de cultivo [R$/ha]
param GTC{P};                           # Custo de transporte de grãos [R$/t]
param CC;                               # Custo de esmagamento/processamento [R$/t]
param C_OGR{R};                         # Custo de aquisição de OGR [R$/t]
param Custo_Estoque_Semente{M};         # Custo de armazenagem de sementes [R$/t]
param penalidade_deficit default preco_biodiesel * 1.2;  # Penalidade pelo não atendimento da demanda

# VARIÁVEIS DE DECISÃO (Sem a dimensão de cenários)
var z{P, M, T} >= 0;                    # Área de terra alocada por matéria-prima [ha]
var y_polo{P, T} binary;                # 1 se o polo agrícola p for aberto no período t
var y_ogr{R, T} binary;                 # 1 se a rede de OGR r for contratada no período t

var gx{P, M, T} >= 0;                   # Quantidade de sementes (t)
var ogr_x{R, T} >= 0;                   # Volume de óleo adquirido de OGR 
var w{M, T} >= 0;                       # Quantidade de matéria-prima esmagada/triturada (t)
var v{T} >= 0;                          # Óleo comprado do mercado (terceiro/externo)
var estoque_semente{M, T} >= 0;         # Estoque das sementes/matéria-prima
var deficit{T} >= 0;                    # Perda de venda da demanda 
var sub_ogr{t in T} >= 0;               # Variável para suprir o mínimo de óleo OGR, caso falte OGR

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
s.t. Limite_Area_Disponivel{p in P, m in M, t in T}:
    z[p,m,t] <= Z_barra[p,m,t] * y_polo[p,t];

# Restrição (3), garante o cumprimento do Selo Social. 
s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P, m in M} (z[p,m,t] / AZ[p,t]) >= TF[t];

# Restrição (4), atendimento da demanda.
s.t. Atendimento_Demanda{t in T}:
    sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t] + deficit[t] >= D[t];

# Restrição (5), determina o balanço de massa no transporte agrícola.
s.t. Balanco_Massa_Agricola{p in P, m in M, t in T}:
    gx[p,m,t] = (1 - beta_trans) * gama[p,m,t] * z[p,m,t];

# Restrição (6), determina o balanço de estoque inicial no primeiro período (t = 1).
s.t. Balanco_Estoque_Inicial{m in M}:
    estoque_semente[m, 1] = sum{p in P} gx[p, m, 1] * (1 - beta_arm) - w[m, 1];

# Restrição (7), determina o balanço de massa subsequente (t > 1).
s.t. Balanco_Estoque_Subsequente{m in M, t in T: t > 1}:
    estoque_semente[m, t] = estoque_semente[m, t-1] 
                         + sum{p in P} gx[p, m, t] * (1 - beta_arm) 
                         - w[m, t];

# Restrição (8), determina a capacidade industrial de esmagamento.
s.t. Capacidade_Industrial{t in T}:
    sum{m in M} w[m,t] <= Capacidade_Usina;

# Restrição (9) estabelece o percentual mínimo de OGR (14%) exigido por lei.
s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] + sub_ogr[t] >= 0.14 * D[t];

# Restrição (10) garante a disponibilidade máxima de OGR.
s.t. Disponibilidade_Max_OGR{r in R, t in T}:
    ogr_x[r,t] <= OfertaOGR[r,t] * y_ogr[r,t];

# Restrição (11) limita a aquisição de óleo externo. 
s.t. Teto_Compra_Externa{t in T}:
    v[t] <= CompraMax[t];

# Restrição (12) limita a capacidade de descarga na usina. 
s.t. Limite_Descarga_Usina{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Descarga[t];

# Restrição (13) limita a capacidade do Parque de Silos. 
s.t. Limite_Armazenagem_Silos{t in T}:
    sum{m in M} estoque_semente[m,t] <= Cap_Armazenagem[t];

# Restrição (14) limita a capacidade da frota de caminhões. 
s.t. Limite_Frota_Caminhoes{t in T}:
    sum{p in P, m in M} gx[p,m,t] <= Cap_Frota_Caminhoes[t];

# Restrição (15) limita a capacidade de expedição e carregamento. 
s.t. Limite_Carregamento_Expedicao{t in T}:
    (sum{m in M} (alfa[m] * (1 - beta_proc) * w[m,t]) + sum{r in R} ogr_x[r,t] + v[t]) <= Cap_Carregamento[t];
"""

with open("pbio_deterministico.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod_deterministico)

print("-> Arquivo pbio_deterministico.mod criado com sucesso.")

# 3. Gerador das 20 Instâncias Determinísticas baseadas no seu .dat oficial
random.seed(42)
print("\nA gerar 20 instâncias determinísticas (24 Meses) e a executar o GLPSOL...")
print(f"{'Instância':<12} | {'Porte':<8} | {'Lucro Total Ótimo (R$)':<28} | {'Estado'}")
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

    # Dados logísticos 
    d_descarga = {1:12000, 2:12000, 3:14000, 4:15000, 5:15000, 6:14000, 7:12000, 8:11000, 9:11000, 10:11000, 11:12000, 12:12000, 13:13000, 14:13000, 15:15000, 16:16000, 17:16000, 18:15000, 19:13000, 20:12000, 21:12000, 22:13000, 23:13000, 24:13000}
    d_armazenagem = {1:7500, 2:7500, 3:9000, 4:10000, 5:10000, 6:9000, 7:8000, 8:7500, 9:7500, 10:7500, 11:7500, 12:7500, 13:8000, 14:8000, 15:9500, 16:10500, 17:10500, 18:9500, 19:8500, 20:8000, 21:8000, 22:8000, 23:8000, 24:8000}
    d_carregamento = {1:11000, 2:11000, 3:12000, 4:13000, 5:13000, 6:12000, 7:11000, 8:11000, 9:11000, 10:11000, 11:11000, 12:11000, 13:12000, 14:12000, 15:13000, 16:14000, 17:14000, 18:13000, 19:12000, 20:12000, 21:12000, 22:12000, 23:12000, 24:12000}

    cap_desc_str = " ".join([f"{t} {int(val * fator)}" for t, val in d_descarga.items()])
    cap_arm_str  = " ".join([f"{t} {int(val * fator)}" for t, val in d_armazenagem.items()])
    cap_carr_str = " ".join([f"{t} {int(val * fator)}" for t, val in d_carregamento.items()])

    # Demanda determinística 
    demanda_det = {1:8000, 2:8150, 3:8300, 4:8500, 5:8700, 6:8400, 7:8200, 8:8000, 9:7900, 10:8100, 11:8300, 12:8500, 13:9200, 14:9400, 15:9700, 16:10000, 17:9800, 18:9500, 19:9300, 20:9100, 21:9200, 22:9400, 23:9600, 24:9800}
    d_str = " ".join([f"{t} {int(val * fator)}" for t, val in demanda_det.items()])

    # Custo de óleo externo
    v_cost_det = {1:410.0, 2:420.0, 3:390.0, 4:370.0, 5:360.0, 6:380.0, 7:400.0, 8:430.0, 9:470.0, 10:500.0, 11:480.0, 12:440.0, 13:430.0, 14:440.0, 15:400.0, 16:380.0, 17:370.0, 18:390.0, 19:420.0, 20:450.0, 21:490.0, 22:510.0, 23:470.0, 24:440.0}
    v_cost_str = " ".join([f"{t} {val}" for t, val in v_cost_det.items()])

    # Matriz completa de produtividade agrícola (gama)
    gama_str = """
    # --- POLO NORTE MG ---
    [polo_norteMG, Soja, 1] := 2.20     [polo_norteMG, Soja, 2] := 2.30
    [polo_norteMG, Soja, 3] := 2.70     [polo_norteMG, Soja, 4] := 3.50     # Pico Safra
    [polo_norteMG, Soja, 5] := 3.60     # Pico Safra
    [polo_norteMG, Soja, 6] := 3.10
    [polo_norteMG, Soja, 7] := 2.50     [polo_norteMG, Soja, 8] := 2.00
    [polo_norteMG, Soja, 9] := 1.80     [polo_norteMG, Soja, 10]:= 1.90
    [polo_norteMG, Soja, 11]:= 2.10     [polo_norteMG, Soja, 12]:= 2.20
    [polo_norteMG, Soja, 13]:= 2.30     [polo_norteMG, Soja, 14]:= 2.50
    [polo_norteMG, Soja, 15]:= 2.90     [polo_norteMG, Soja, 16]:= 3.70     # Pico Safra Ano 2
    [polo_norteMG, Soja, 17]:= 3.80     # Pico Safra Ano 2
    [polo_norteMG, Soja, 18]:= 3.20     [polo_norteMG, Soja, 19]:= 2.60
    [polo_norteMG, Soja, 20]:= 2.10     [polo_norteMG, Soja, 21]:= 1.90
    [polo_norteMG, Soja, 22]:= 2.00     [polo_norteMG, Soja, 23]:= 2.20
    [polo_norteMG, Soja, 24]:= 2.30

    [polo_norteMG, Algodao, 1]:= 1.70 [polo_norteMG, Algodao, 2]:= 1.80
    [polo_norteMG, Algodao, 3]:= 2.10 [polo_norteMG, Algodao, 4]:= 2.60
    [polo_norteMG, Algodao, 5]:= 2.70 [polo_norteMG, Algodao, 6]:= 2.30
    [polo_norteMG, Algodao, 7]:= 1.90 [polo_norteMG, Algodao, 8]:= 1.50
    [polo_norteMG, Algodao, 9]:= 1.40 [polo_norteMG, Algodao, 10]:= 1.40
    [polo_norteMG, Algodao, 11]:= 1.60 [polo_norteMG, Algodao, 12]:= 1.70
    [polo_norteMG, Algodao, 13]:= 1.80 [polo_norteMG, Algodao, 14]:= 1.90
    [polo_norteMG, Algodao, 15]:= 2.20 [polo_norteMG, Algodao, 16]:= 2.80
    [polo_norteMG, Algodao, 17]:= 2.90 [polo_norteMG, Algodao, 18]:= 2.40
    [polo_norteMG, Algodao, 19]:= 2.00 [polo_norteMG, Algodao, 20]:= 1.60
    [polo_norteMG, Algodao, 21]:= 1.40 [polo_norteMG, Algodao, 22]:= 1.50
    [polo_norteMG, Algodao, 23]:= 1.70 [polo_norteMG, Algodao, 24]:= 1.80

    [polo_norteMG, Macauba, 1]:= 2.80  [polo_norteMG, Macauba, 2]:= 2.90
    [polo_norteMG, Macauba, 3]:= 3.30  [polo_norteMG, Macauba, 4]:= 4.10
    [polo_norteMG, Macauba, 5]:= 4.20  [polo_norteMG, Macauba, 6]:= 3.70
    [polo_norteMG, Macauba, 7]:= 3.00  [polo_norteMG, Macauba, 8]:= 2.50
    [polo_norteMG, Macauba, 9]:= 2.20  [polo_norteMG, Macauba, 10]:= 2.30
    [polo_norteMG, Macauba, 11]:= 2.60 [polo_norteMG, Macauba, 12]:= 2.80
    [polo_norteMG, Macauba, 13]:= 2.90 [polo_norteMG, Macauba, 14]:= 3.00
    [polo_norteMG, Macauba, 15]:= 3.40 [polo_norteMG, Macauba, 16]:= 4.30
    [polo_norteMG, Macauba, 17]:= 4.40 [polo_norteMG, Macauba, 18]:= 3.80
    [polo_norteMG, Macauba, 19]:= 3.10 [polo_norteMG, Macauba, 20]:= 2.60
    [polo_norteMG, Macauba, 21]:= 2.30 [polo_norteMG, Macauba, 22]:= 2.50
    [polo_norteMG, Macauba, 23]:= 2.70 [polo_norteMG, Macauba, 24]:= 2.90

    [polo_norteMG, Girassol, 1]:= 1.10 [polo_norteMG, Girassol, 2]:= 1.20
    [polo_norteMG, Girassol, 3]:= 1.40 [polo_norteMG, Girassol, 4]:= 1.80
    [polo_norteMG, Girassol, 5]:= 1.90 [polo_norteMG, Girassol, 6]:= 1.60
    [polo_norteMG, Girassol, 7]:= 1.30 [polo_norteMG, Girassol, 8]:= 1.00
    [polo_norteMG, Girassol, 9]:= 0.90 [polo_norteMG, Girassol, 10]:= 1.00
    [polo_norteMG, Girassol, 11]:= 1.10 [polo_norteMG, Girassol, 12]:= 1.10
    [polo_norteMG, Girassol, 13]:= 1.20 [polo_norteMG, Girassol, 14]:= 1.30
    [polo_norteMG, Girassol, 15]:= 1.50 [polo_norteMG, Girassol, 16]:= 1.90
    [polo_norteMG, Girassol, 17]:= 2.00 [polo_norteMG, Girassol, 18]:= 1.70
    [polo_norteMG, Girassol, 19]:= 1.40 [polo_norteMG, Girassol, 20]:= 1.10
    [polo_norteMG, Girassol, 21]:= 1.00 [polo_norteMG, Girassol, 22]:= 1.10
    [polo_norteMG, Girassol, 23]:= 1.20 [polo_norteMG, Girassol, 24]:= 1.30

    [polo_norteMG, Nabo_Forrageiro, 1]:= 1.40 [polo_norteMG, Nabo_Forrageiro, 2]:= 1.50
    [polo_norteMG, Nabo_Forrageiro, 3]:= 1.80 [polo_norteMG, Nabo_Forrageiro, 4]:= 2.20
    [polo_norteMG, Nabo_Forrageiro, 5]:= 2.30 [polo_norteMG, Nabo_Forrageiro, 6]:= 2.00
    [polo_norteMG, Nabo_Forrageiro, 7]:= 1.60 [polo_norteMG, Nabo_Forrageiro, 8]:= 1.30
    [polo_norteMG, Nabo_Forrageiro, 9]:= 1.10 [polo_norteMG, Nabo_Forrageiro, 10]:= 1.20
    [polo_norteMG, Nabo_Forrageiro, 11]:= 1.30 [polo_norteMG, Nabo_Forrageiro, 12]:= 1.40
    [polo_norteMG, Nabo_Forrageiro, 13]:= 1.50 [polo_norteMG, Nabo_Forrageiro, 14]:= 1.60
    [polo_norteMG, Nabo_Forrageiro, 15]:= 1.90 [polo_norteMG, Nabo_Forrageiro, 16]:= 2.30
    [polo_norteMG, Nabo_Forrageiro, 17]:= 2.40 [polo_norteMG, Nabo_Forrageiro, 18]:= 2.00
    [polo_norteMG, Nabo_Forrageiro, 19]:= 1.70 [polo_norteMG, Nabo_Forrageiro, 20]:= 1.40
    [polo_norteMG, Nabo_Forrageiro, 21]:= 1.20 [polo_norteMG, Nabo_Forrageiro, 22]:= 1.30
    [polo_norteMG, Nabo_Forrageiro, 23]:= 1.50 [polo_norteMG, Nabo_Forrageiro, 24]:= 1.60

    # --- POLO SEMIÁRIDO ---
    [polo_semiarido, Soja, 1] := 1.60   [polo_semiarido, Soja, 2] := 1.70
    [polo_semiarido, Soja, 3] := 2.10   [polo_semiarido, Soja, 4] := 2.70
    [polo_semiarido, Soja, 5] := 2.80   [polo_semiarido, Soja, 6] := 2.40
    [polo_semiarido, Soja, 7] := 1.90   [polo_semiarido, Soja, 8] := 1.50
    [polo_semiarido, Soja, 9] := 1.30   [polo_semiarido, Soja, 10]:= 1.40
    [polo_semiarido, Soja, 11]:= 1.50  [polo_semiarido, Soja, 12]:= 1.60
    [polo_semiarido, Soja, 13]:= 1.70  [polo_semiarido, Soja, 14]:= 1.80
    [polo_semiarido, Soja, 15]:= 2.20  [polo_semiarido, Soja, 16]:= 2.90
    [polo_semiarido, Soja, 17]:= 3.00  [polo_semiarido, Soja, 18]:= 2.50
    [polo_semiarido, Soja, 19]:= 2.00  [polo_semiarido, Soja, 20]:= 1.60
    [polo_semiarido, Soja, 21]:= 1.40  [polo_semiarido, Soja, 22]:= 1.50
    [polo_semiarido, Soja, 23]:= 1.70  [polo_semiarido, Soja, 24]:= 1.70

    [polo_semiarido, Algodao, 1]:= 1.30 [polo_semiarido, Algodao, 2]:= 1.40
    [polo_semiarido, Algodao, 3]:= 1.60 [polo_semiarido, Algodao, 4]:= 2.10
    [polo_semiarido, Algodao, 5]:= 2.20 [polo_semiarido, Algodao, 6]:= 1.80
    [polo_semiarido, Algodao, 7]:= 1.50 [polo_semiarido, Algodao, 8]:= 1.10
    [polo_semiarido, Algodao, 9]:= 1.00 [polo_semiarido, Algodao, 10]:= 1.00
    [polo_semiarido, Algodao, 11]:= 1.10 [polo_semiarido, Algodao, 12]:= 1.30
    [polo_semiarido, Algodao, 13]:= 1.40 [polo_semiarido, Algodao, 14]:= 1.50
    [polo_semiarido, Algodao, 15]:= 1.70 [polo_semiarido, Algodao, 16]:= 2.30
    [polo_semiarido, Algodao, 17]:= 2.40 [polo_semiarido, Algodao, 18]:= 1.90
    [polo_semiarido, Algodao, 19]:= 1.60 [polo_semiarido, Algodao, 20]:= 1.20
    [polo_semiarido, Algodao, 21]:= 1.10 [polo_semiarido, Algodao, 22]:= 1.10
    [polo_semiarido, Algodao, 23]:= 1.30 [polo_semiarido, Algodao, 24]:= 1.40

    [polo_semiarido, Macauba, 1]:= 2.10  [polo_semiarido, Macauba, 2]:= 2.20
    [polo_semiarido, Macauba, 3]:= 2.60  [polo_semiarido, Macauba, 4]:= 3.20
    [polo_semiarido, Macauba, 5]:= 3.30  [polo_semiarido, Macauba, 6]:= 2.90
    [polo_semiarido, Macauba, 7]:= 2.30  [polo_semiarido, Macauba, 8]:= 1.90
    [polo_semiarido, Macauba, 9]:= 1.70  [polo_semiarido, Macauba, 10]:= 1.80
    [polo_semiarido, Macauba, 11]:= 2.00 [polo_semiarido, Macauba, 12]:= 2.10
    [polo_semiarido, Macauba, 13]:= 2.20 [polo_semiarido, Macauba, 14]:= 2.30
    [polo_semiarido, Macauba, 15]:= 2.70 [polo_semiarido, Macauba, 16]:= 3.40
    [polo_semiarido, Macauba, 17]:= 3.50 [polo_semiarido, Macauba, 18]:= 3.00
    [polo_semiarido, Macauba, 19]:= 2.40 [polo_semiarido, Macauba, 20]:= 2.00
    [polo_semiarido, Macauba, 21]:= 1.80 [polo_semiarido, Macauba, 22]:= 1.90
    [polo_semiarido, Macauba, 23]:= 2.10 [polo_semiarido, Macauba, 24]:= 2.20

    [polo_semiarido, Girassol, 1]:= 0.90 [polo_semiarido, Girassol, 2]:= 1.00
    [polo_semiarido, Girassol, 3]:= 1.20 [polo_semiarido, Girassol, 4]:= 1.50
    [polo_semiarido, Girassol, 5]:= 1.60 [polo_semiarido, Girassol, 6]:= 1.30
    [polo_semiarido, Girassol, 7]:= 1.10 [polo_semiarido, Girassol, 8]:= 0.80
    [polo_semiarido, Girassol, 9]:= 0.70 [polo_semiarido, Girassol, 10]:= 0.80
    [polo_semiarido, Girassol, 11]:= 0.90 [polo_semiarido, Girassol, 12]:= 0.90
    [polo_semiarido, Girassol, 13]:= 1.00 [polo_semiarido, Girassol, 14]:= 1.10
    [polo_semiarido, Girassol, 15]:= 1.30 [polo_semiarido, Girassol, 16]:= 1.60
    [polo_semiarido, Girassol, 17]:= 1.70 [polo_semiarido, Girassol, 18]:= 1.40
    [polo_semiarido, Girassol, 19]:= 1.20 [polo_semiarido, Girassol, 20]:= 1.00
    [polo_semiarido, Girassol, 21]:= 0.80 [polo_semiarido, Girassol, 22]:= 0.90
    [polo_semiarido, Girassol, 23]:= 1.00 [polo_semiarido, Girassol, 24]:= 1.10

    [polo_semiarido, Nabo_Forrageiro, 1]:= 1.00 [polo_semiarido, Nabo_Forrageiro, 2]:= 1.10
    [polo_semiarido, Nabo_Forrageiro, 3]:= 1.40 [polo_semiarido, Nabo_Forrageiro, 4]:= 1.70
    [polo_semiarido, Nabo_Forrageiro, 5]:= 1.80 [polo_semiarido, Nabo_Forrageiro, 6]:= 1.50
    [polo_semiarido, Nabo_Forrageiro, 7]:= 1.20 [polo_semiarido, Nabo_Forrageiro, 8]:= 1.00
    [polo_semiarido, Nabo_Forrageiro, 9]:= 0.80 [polo_semiarido, Nabo_Forrageiro, 10]:= 0.90
    [polo_semiarido, Nabo_Forrageiro, 11]:= 1.00 [polo_semiarido, Nabo_Forrageiro, 12]:= 1.10
    [polo_semiarido, Nabo_Forrageiro, 13]:= 1.10 [polo_semiarido, Nabo_Forrageiro, 14]:= 1.20
    [polo_semiarido, Nabo_Forrageiro, 15]:= 1.50 [polo_semiarido, Nabo_Forrageiro, 16]:= 1.80
    [polo_semiarido, Nabo_Forrageiro, 17]:= 1.90 [polo_semiarido, Nabo_Forrageiro, 18]:= 1.60
    [polo_semiarido, Nabo_Forrageiro, 19]:= 1.30 [polo_semiarido, Nabo_Forrageiro, 20]:= 1.10
    [polo_semiarido, Nabo_Forrageiro, 21]:= 1.00 [polo_semiarido, Nabo_Forrageiro, 22]:= 1.00
    [polo_semiarido, Nabo_Forrageiro, 23]:= 1.10 [polo_semiarido, Nabo_Forrageiro, 24]:= 1.20
    """

    conteudo_dat = f"""# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO DETERMINÍSTICA) - Instância {i} ({porte})
# =============================================================================================================

data;

set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;

# Parâmetros de rendimento e perdas de cada matéria-prima (m)
param alfa :=
    Soja               0.18
    Algodao            0.15
    Macauba            0.28
    Girassol           0.40
    Nabo_Forrageiro    0.35;

# Preços e receitas
param preco_biodiesel := {preco_bio};         # valor da venda unitária do biodiesel R$ 4.500,00 por tonelada
param preco_glicerina := 1200.0;         # valor de venda unitária do coproduto (glicerina)
param rend_glicerina  := 0.10;           # rendimento da glicerina
param preco_carbono   := 50.0;           # créditos de carbono gerados pelo processo

param preco_farelo :=
    Soja               800.0                # preço de venda do farelo de soja: R$ 800,00 por tonelada
    Algodao            650.0                # preço de venda do farelo de algodão: R$ 650,00 por tonelada
    Macauba            500.0                # preço de venda do farelo de macaúba: R$ 500,00 por tonelada
    Girassol           700.0                # preço de venda do farelo de girassol: R$ 700,00 por tonelada
    Nabo_Forrageiro    600.0;               # preço de venda do farelo de nabo: R$ 600,00 por tonelada

param rend_farelo :=
    Soja               0.75                 # rendimento do farelo de cada matéria-prima
    Algodao            0.55
    Macauba            0.50
    Girassol           0.50
    Nabo_Forrageiro    0.45;

# Custos e capacidades gerais
param CC := 45.0;                          # Custo de Conversão | R$ 45,00 por tonelada 
param Capacidade_Usina := {cap_usina};       # Capacidade mensal proporcional (~16.3k t/mês)

param Custo_Estoque_Semente :=
    Soja               15.0
    Algodao            12.0
    Macauba            10.0
    Girassol           14.0
    Nabo_Forrageiro    11.0;

param Custo_Fixo_Polo :=
    polo_norteMG     500000.0                # 500 K
    polo_semiarido   400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0            # 150 K
    rede_urbana        200000.0;

# Limites operacionais variáveis por mês (1 a 24) para simular gargalos logísticos sazonais
param Cap_Descarga := {cap_desc_str};

param Cap_Armazenagem := {cap_arm_str};

param Cap_Frota_Caminhoes := {cap_desc_str};

param Cap_Carregamento := {cap_carr_str};

param C_OGR := rede_catadores_moc 110.0 rede_urbana 125.0;

param PC :=
    [polo_norteMG, *]     := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

# Demanda determinística por mês 
param D := {d_str};

# Custo do óleo externo determinístico 
param v_cost := {v_cost_str};

# Produtividade agrícola determinística (gama) 
param gama := {gama_str};

param AZ :=
    [polo_norteMG, *]     := {" ".join([f"{t} 12.0" for t in range(1, 25)])}
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

    dat_file = f"instancia_det_{i}.dat"
    out_file = f"resultado_det_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_deterministico.mod", "-d", dat_file, "-o", out_file],
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
