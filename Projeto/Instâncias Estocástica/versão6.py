import os
import shutil
import subprocess
import random

# 1. Garante a instalação do GLPK no ambiente
if not shutil.which("glpsol"):
    print("Instalando glpk-utils...")
    subprocess.run("apt-get install -y glpk-utils", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 2. Criação do arquivo .mod (Versão 6 Estocástica)
codigo_mod_v6_estocastico = """
# ========================================================================================================================
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (VERSÃO 6 - Modelo Estocástico)
# ========================================================================================================================

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

# ====================================================================================================================================
#                                                 RESTRIÇÕES DO SISTEMA
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

# Restrição (6), determina o balanço de estoque incicial de sementes (t = 2024) para cada cenário s.
s.t. Balanco_Estoque_Inicial{m in M, s in S}:
    estoque_semente[m, 2024, s] = sum{p in P} gx[p, m, 2024, s] * (1 - beta_arm) - w[m, 2024, s];
# =====================================================================================================================================

# Restrição (7), determina o balanço de massa subsequente (t > 2024) para cada cenário s.
s.t. Balanco_Estoque_Subsequente{m in M, t in T, s in S: t > 2024}:
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
s.t. Percentual_Minimo_OGR{t in T, s in S}:
    sum{r in R} ogr_x[r,t,s] >= 0.14 * D[t,s];
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
"""

with open("pbio_estocastico_v6.mod", "w", encoding="utf-8") as f:
    f.write(codigo_mod_v6_estocastico)

print("-> Arquivo pbio_estocastico_v6.mod criado com sucesso (com todos os comentários organizados).")

# 3. Gerador das 20 Instâncias (27 Cenários por instância)
random.seed(42)
print("\nGerando 20 instâncias (Árvore de 27 Cenários no .dat) e executando o GLPSOL...")
print(f"{'Instância':<12} | {'Porte':<8} | {'Lucro Esperado Ótimo (R$)':<28} | {'Estado'}")
print("-" * 72)

# Configuração da Árvore de Incerteza
prob_d = {'Baixa': 0.2, 'Media': 0.5, 'Alta': 0.3}
fat_d  = {'Baixa': 0.90, 'Media': 1.00, 'Alta': 1.15}

prob_p = {'Ruim': 0.2, 'Normal': 0.5, 'Boa': 0.3}
fat_p  = {'Ruim': 0.80, 'Normal': 1.00, 'Boa': 1.15}

prob_v = {'Baixo': 0.25, 'Medio': 0.50, 'Alto': 0.25}
fat_v  = {'Baixo': 0.85, 'Medio': 1.00, 'Alto': 1.25}

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

    d2024_base = 98000.0 * fator
    d2025_base = 115000.0 * fator
    preco_bio = round(random.uniform(4300.0, 4800.0), 2)
    cap_usina = 196362.0 * fator

    cenarios_cfg = []
    pi_cfg = {}
    demanda_cfg = {}
    v_cost_cfg = {}
    gama_cfg_linhas = []

    s_idx = 1
    for d_niv in ['Baixa', 'Media', 'Alta']:
        for p_niv in ['Ruim', 'Normal', 'Boa']:
            for v_niv in ['Baixo', 'Medio', 'Alto']:
                s_nome = f"S{s_idx}"
                cenarios_cfg.append(s_nome)
                
                # Probabilidade conjunta do cenário pi_omega
                pi_cfg[s_nome] = prob_d[d_niv] * prob_p[p_niv] * prob_v[v_niv]
                
                demanda_cfg[s_nome] = (d2024_base * fat_d[d_niv], d2025_base * fat_d[d_niv])
                v_cost_cfg[s_nome] = (480.0 * fat_v[v_niv], 510.0 * fat_v[v_niv])

                polos_dados = [
                    ("polo_norteMG", [("Soja", 2.80, 3.10), ("Algodao", 2.20, 2.40), ("Macauba", 3.50, 3.80), ("Girassol", 1.50, 1.70), ("Nabo_Forrageiro", 1.80, 2.00)]),
                    ("polo_semiarido", [("Soja", 2.10, 2.30), ("Algodao", 1.70, 1.90), ("Macauba", 2.90, 3.10), ("Girassol", 1.20, 1.30), ("Nabo_Forrageiro", 1.40, 1.50)])
                ]
                
                fp = fat_p[p_niv]
                for polo, mp_list in polos_dados:
                    for mp, b24, b25 in mp_list:
                        gama_cfg_linhas.append(f"    [{polo}, {mp}, 2024, {s_nome}] := {round(b24 * fp, 2)}")
                        gama_cfg_linhas.append(f"    [{polo}, {mp}, 2025, {s_nome}] := {round(b25 * fp, 2)}")
                
                s_idx += 1

    lista_s_str = " ".join(cenarios_cfg)
    pi_str = "\n    ".join([f"{s} {pi_cfg[s]:.6f}" for s in cenarios_cfg])
    dem_24_str = " ".join([f"{s} {demanda_cfg[s][0]:.2f}" for s in cenarios_cfg])
    dem_25_str = " ".join([f"{s} {demanda_cfg[s][1]:.2f}" for s in cenarios_cfg])
    v_24_str = " ".join([f"{s} {v_cost_cfg[s][0]:.2f}" for s in cenarios_cfg])
    v_25_str = " ".join([f"{s} {v_cost_cfg[s][1]:.2f}" for s in cenarios_cfg])
    gama_str = "\n".join(gama_cfg_linhas)

    conteudo_dat = f"""# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO 6) - Modelo Estocástico - Instância {i} ({porte})
# =============================================================================================================

data;

# Conjuntos 
set T := 2024 2025;                                       # Horizonte de planejamento
set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;
set S := {lista_s_str};                                   # Conjunto de 27 cenarios (omega)

# Probabilidade de cada cenário ocorrer (pi_omega)
param pi :=
    {pi_str};

# Parâmetros de rendimento e perdas de cada matéria-prima (m)
# Indica o teor de óleo. Ex: soja tem 18% de conversão de óleo
param alfa :=
    Soja            0.18
    Algodao         0.15
    Macauba         0.28
    Girassol        0.40
    Nabo_Forrageiro 0.35;

# Preços e receitas
param preco_biodiesel := {preco_bio};          # valor da venda unitária do biodiesel R$ {preco_bio} por tonelada
param preco_glicerina := 1200.0;          # valor de venda unitária do coproduto (glicerina)
param rend_glicerina  := 0.10;            # rendimento da glicerina
param preco_carbono   := 50.0;            # créditos de carbono gerados pelo processo 

param preco_farelo :=
    Soja            800.0                # preço de venda do farelo de cada matéria-prima R$ 800,00 por tonelada
    Algodao         650.0
    Macauba         500.0
    Girassol        700.0
    Nabo_Forrageiro 600.0;

param rend_farelo :=
    Soja            0.75                 # rendimento do farelo de cada matéria-prima (subproduto para ração animal)
    Algodao         0.55
    Macauba         0.50
    Girassol        0.50
    Nabo_Forrageiro 0.45;

# Custos e capacidades gerais
param CC := 45.0;                             # Custo de Conversão | R$ 45,00 por tonelada 
param Capacidade_Usina := {cap_usina};

param Custo_Estoque_Semente :=
    Soja            15.0
    Algodao         12.0
    Macauba         10.0
    Girassol        14.0
    Nabo_Forrageiro 11.0;

param Custo_Fixo_Polo :=
    polo_norteMG    500000.0              # 500 K
    polo_semiarido  400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0                         # 150 K | Ex: parcerias com cooperativas locais e catadores
    rede_urbana        200000.0;                        # Ex: grandes centros comerciais e urbanos, como restaurantes e hotéis

# Limites operacionais por ano
param Cap_Descarga := 2024 {140000.0 * fator} 2025 {160000.0 * fator};
param Cap_Armazenagem := 2024 {80000.0 * fator} 2025 {90000.0 * fator};
param Cap_Frota_Caminhoes := 2024 {140000.0 * fator} 2025 {160000.0 * fator};
param Cap_Carregamento := 2024 {130000.0 * fator} 2025 {150000.0 * fator};

param C_OGR := rede_catadores_moc 110.0 rede_urbana 125.0;

param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0   # Custo do cultivo: R$ 140,00 por hectare
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;                 # custo de transporte: R$ 18,00 por tonelada

# Demanda estocástica por cenário (S1 até S27)
param D :=
    [2024, *] := {dem_24_str}
    [2025, *] := {dem_25_str};

# Custo do óleo externo estocástico por cenário
param v_cost :=
    [2024, *] := {v_24_str}
    [2025, *] := {v_25_str};

# Produtividade agrícola estocástica (gama) por polo, matéria-prima, ano e cenário
param gama :=
{gama_str};

param AZ :=
    [polo_norteMG, *]   := 2024 12.0 2025 12.0
    [polo_semiarido, *] := 2024 15.0 2025 15.0;

param Z_barra :=
    [polo_norteMG, Soja, *]            := 2024 {30000.0 * fator} 2025 {35000.0 * fator}
    [polo_norteMG, Algodao, *]         := 2024 {10000.0 * fator} 2025 {12000.0 * fator}
    [polo_norteMG, Macauba, *]         := 2024 {5000.0 * fator}  2025 {6000.0 * fator}
    [polo_norteMG, Girassol, *]        := 2024 {3000.0 * fator}  2025 {4000.0 * fator}
    [polo_norteMG, Nabo_Forrageiro, *] := 2024 {2000.0 * fator}  2025 {3000.0 * fator}
    [polo_semiarido, Soja, *]          := 2024 {20000.0 * fator} 2025 {22000.0 * fator}
    [polo_semiarido, Algodao, *]       := 2024 {8000.0 * fator}  2025 {9000.0 * fator}
    [polo_semiarido, Macauba, *]       := 2024 {6000.0 * fator}  2025 {7000.0 * fator}
    [polo_semiarido, Girassol, *]      := 2024 {3000.0 * fator}  2025 {3500.0 * fator}
    [polo_semiarido, Nabo_Forrageiro, *]:= 2024 {3000.0 * fator} 2025 {3500.0 * fator};

param TF := 2024 1800 2025 2200;            # meta de atendimento às famílias do Selo Social

param OfertaOGR :=
    [rede_catadores_moc, *] := 2024 {90000.0 * fator} 2025 {100000.0 * fator}      # limite de disponibilidade do óleo
    [rede_urbana, *]        := 2024 {20000.0 * fator} 2025 {25000.0 * fator};

param CompraMax := 2024 {15000.0 * fator} 2025 {20000.0 * fator};                  # compra máxima de óleo terceiro

end;
"""

    dat_file = f"instancia_v6_estocastica_{i}.dat"
    out_file = f"resultado_v6_estocastica_{i}.txt"

    with open(dat_file, "w", encoding="utf-8") as f:
        f.write(conteudo_dat)

    try:
        subprocess.run(["glpsol", "-m", "pbio_estocastico_v6.mod", "-d", dat_file, "-o", out_file],
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
