# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO 7 ESTOCÁSTICO) - Instância 1 (Pequeno)
# =============================================================================================================

data;

# Conjuntos
set P := polo_norteMG polo_semiarido;
set R := rede_catadores_moc rede_urbana;
set M := Soja Algodao Macauba Girassol Nabo_Forrageiro;
set S := S1 S2 S3;                                    # Conjunto de cenários

# Probabilidade de cada cenário ocorrer (pi_omega)
param pi :=
    S1  0.2
    S2  0.5
    S3  0.3;

# Parâmetros de rendimento e perdas de cada matéria-prima (m)
param alfa :=
    Soja                0.18
    Algodao             0.15
    Macauba             0.28
    Girassol            0.40
    Nabo_Forrageiro     0.35;

# Preços e receitas
param preco_biodiesel := 4619.71;         # valor da venda unitária do biodiesel por tonelada
param preco_glicerina := 1200.0;         # valor de venda unitária do coproduto (glicerina)
param rend_glicerina  := 0.10;           # rendimento da glicerina
param preco_carbono   := 50.0;           # créditos de carbono gerados pelo processo

param preco_farelo :=
    Soja                800.0                # preço de venda do farelo de soja: R$ 800,00 por tonelada
    Algodao             650.0                # preço de venda do farelo de algodão: R$ 650,00 por tonelada
    Macauba             500.0                # preço de venda do farelo de macaúba: R$ 500,00 por tonelada
    Girassol            700.0                # preço de venda do farelo de girassol: R$ 700,00 por tonelada
    Nabo_Forrageiro     600.0;               # preço de venda do farelo de nabo: R$ 600,00 por tonelada

param rend_farelo :=
    Soja                0.75                 # rendimento do farelo de cada matéria-prima
    Algodao             0.55
    Macauba             0.50
    Girassol            0.50
    Nabo_Forrageiro     0.45;

# Custos e capacidades gerais
param CC := 45.0;                            # Custo de Conversão | R$ 45,00 por tonelada
param Capacidade_Usina := 16362;       # Capacidade máxima de esmagamento na usina

param Custo_Estoque_Semente :=
    Soja                15.0
    Algodao             12.0
    Macauba             10.0
    Girassol            14.0
    Nabo_Forrageiro     11.0;

param Custo_Fixo_Polo :=
    polo_norteMG      500000.0                # 500 K
    polo_semiarido    400000.0;

param Custo_Fixo_OGR :=
    rede_catadores_moc 150000.0              # 150 K
    rede_urbana        200000.0;

# Limites operacionais variáveis por mês (1 a 24) para simular gargalos logísticos sazonais
param Cap_Descarga :=
    1 7200 2 7200 3 8400 4 9000 5 9000 6 8400 7 7200 8 6600 9 6600 10 6600 11 7200 12 7200 13 7800 14 7800 15 9000 16 9600 17 9600 18 9000 19 7800 20 7200 21 7200 22 7800 23 7800 24 7800;

param Cap_Armazenagem :=
    1 4500 2 4500 3 5400 4 6000 5 6000 6 5400 7 4800 8 4500 9 4500 10 4500 11 4500 12 4500 13 4800 14 4800 15 5700 16 6300 17 6300 18 5700 19 5100 20 4800 21 4800 22 4800 23 4800 24 4800;

param Cap_Frota_Caminhoes :=
    1 7200 2 7200 3 8400 4 9000 5 9000 6 8400 7 7200 8 6600 9 6600 10 6600 11 7200 12 7200 13 7800 14 7800 15 9000 16 9600 17 9600 18 9000 19 7800 20 7200 21 7200 22 7800 23 7800 24 7800;

param Cap_Carregamento :=
    1 6600 2 6600 3 7200 4 7800 5 7800 6 7200 7 6600 8 6600 9 6600 10 6600 11 6600 12 6600 13 7200 14 7200 15 7800 16 8400 17 8400 18 7800 19 7200 20 7200 21 7200 22 7200 23 7200 24 7200;

param C_OGR := rede_catadores_moc 110.0 rede_urbana 125.0;

param PC :=
    [polo_norteMG, *]     := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

# Demanda estocástica sazonal por cenário (S1=Baixa/Seca, S2=Médio, S3=Alta/Aquecida) para os 24 meses
param D :=
    [1, *] := S1 4001 S2 4572 S3 5458
    [2, *] := S1 4047 S2 4780 S3 5630
    [3, *] := S1 4259 S2 4842 S3 5717
    [4, *] := S1 4606 S2 5221 S3 6142
    [5, *] := S1 4641 S2 5312 S3 6228
    [6, *] := S1 4614 S2 5238 S3 6173
    [7, *] := S1 4142 S2 4717 S3 5580
    [8, *] := S1 4167 S2 4763 S3 5655
    [9, *] := S1 3717 S2 4517 S3 5375
    [10, *] := S1 4140 S2 4723 S3 5598
    [11, *] := S1 4262 S2 4983 S3 5883
    [12, *] := S1 4287 S2 4859 S3 5773
    [13, *] := S1 4539 S2 5354 S3 6401
    [14, *] := S1 4994 S2 5725 S3 6821
    [15, *] := S1 5002 S2 5846 S3 6931
    [16, *] := S1 5132 S2 5832 S3 6882
    [17, *] := S1 4964 S2 5932 S3 7022
    [18, *] := S1 5134 S2 5876 S3 6990
    [19, *] := S1 4563 S2 5305 S3 6331
    [20, *] := S1 4885 S2 5627 S3 6740
    [21, *] := S1 4834 S2 5629 S3 6731
    [22, *] := S1 4841 S2 5550 S3 6672
    [23, *] := S1 4664 S2 5562 S3 6662
    [24, *] := S1 5396 S2 6149 S3 7341;

# Custo do óleo externo estocástico e variável
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

# Produtividade agrícola estocástica e sazonal (gama) gerada com dados completos por polo, matéria-prima, mês e cenário
param gama :=
    [polo_norteMG, Soja, 1, *] := S1 1.17 S2 1.64 S3 2.05
    [polo_norteMG, Soja, 2, *] := S1 1.05 S2 1.47 S3 1.84
    [polo_norteMG, Soja, 3, *] := S1 1.05 S2 1.47 S3 1.84
    [polo_norteMG, Soja, 4, *] := S1 1.85 S2 2.59 S3 3.24
    [polo_norteMG, Soja, 5, *] := S1 1.69 S2 2.37 S3 2.96
    [polo_norteMG, Soja, 6, *] := S1 1.82 S2 2.55 S3 3.19
    [polo_norteMG, Soja, 7, *] := S1 1.36 S2 1.9 S3 2.38
    [polo_norteMG, Soja, 8, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_norteMG, Soja, 9, *] := S1 1.49 S2 2.09 S3 2.61
    [polo_norteMG, Soja, 10, *] := S1 1.19 S2 1.67 S3 2.09
    [polo_norteMG, Soja, 11, *] := S1 1.28 S2 1.79 S3 2.24
    [polo_norteMG, Soja, 12, *] := S1 1.41 S2 1.97 S3 2.46
    [polo_norteMG, Soja, 13, *] := S1 1.31 S2 1.83 S3 2.29
    [polo_norteMG, Soja, 14, *] := S1 1.43 S2 2.0 S3 2.5
    [polo_norteMG, Soja, 15, *] := S1 1.29 S2 1.81 S3 2.26
    [polo_norteMG, Soja, 16, *] := S1 1.76 S2 2.46 S3 3.08
    [polo_norteMG, Soja, 17, *] := S1 1.33 S2 1.86 S3 2.33
    [polo_norteMG, Soja, 18, *] := S1 1.45 S2 2.03 S3 2.54
    [polo_norteMG, Soja, 19, *] := S1 1.14 S2 1.6 S3 2.0
    [polo_norteMG, Soja, 20, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_norteMG, Soja, 21, *] := S1 1.12 S2 1.57 S3 1.96
    [polo_norteMG, Soja, 22, *] := S1 1.05 S2 1.47 S3 1.84
    [polo_norteMG, Soja, 23, *] := S1 1.14 S2 1.6 S3 2.0
    [polo_norteMG, Soja, 24, *] := S1 1.32 S2 1.85 S3 2.31
    [polo_norteMG, Algodao, 1, *] := S1 1.18 S2 1.65 S3 2.06
    [polo_norteMG, Algodao, 2, *] := S1 1.19 S2 1.67 S3 2.09
    [polo_norteMG, Algodao, 3, *] := S1 1.1 S2 1.54 S3 1.93
    [polo_norteMG, Algodao, 4, *] := S1 1.47 S2 2.06 S3 2.58
    [polo_norteMG, Algodao, 5, *] := S1 1.91 S2 2.67 S3 3.34
    [polo_norteMG, Algodao, 6, *] := S1 1.72 S2 2.41 S3 3.01
    [polo_norteMG, Algodao, 7, *] := S1 1.3 S2 1.82 S3 2.27
    [polo_norteMG, Algodao, 8, *] := S1 1.09 S2 1.53 S3 1.91
    [polo_norteMG, Algodao, 9, *] := S1 1.36 S2 1.9 S3 2.38
    [polo_norteMG, Algodao, 10, *] := S1 1.08 S2 1.51 S3 1.89
    [polo_norteMG, Algodao, 11, *] := S1 1.19 S2 1.67 S3 2.09
    [polo_norteMG, Algodao, 12, *] := S1 1.49 S2 2.09 S3 2.61
    [polo_norteMG, Algodao, 13, *] := S1 1.32 S2 1.85 S3 2.31
    [polo_norteMG, Algodao, 14, *] := S1 1.28 S2 1.79 S3 2.24
    [polo_norteMG, Algodao, 15, *] := S1 1.34 S2 1.88 S3 2.35
    [polo_norteMG, Algodao, 16, *] := S1 1.85 S2 2.59 S3 3.24
    [polo_norteMG, Algodao, 17, *] := S1 1.8 S2 2.52 S3 3.15
    [polo_norteMG, Algodao, 18, *] := S1 1.45 S2 2.03 S3 2.54
    [polo_norteMG, Algodao, 19, *] := S1 1.02 S2 1.43 S3 1.79
    [polo_norteMG, Algodao, 20, *] := S1 1.16 S2 1.62 S3 2.03
    [polo_norteMG, Algodao, 21, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_norteMG, Algodao, 22, *] := S1 1.11 S2 1.55 S3 1.94
    [polo_norteMG, Algodao, 23, *] := S1 1.47 S2 2.06 S3 2.58
    [polo_norteMG, Algodao, 24, *] := S1 1.44 S2 2.02 S3 2.52
    [polo_norteMG, Macauba, 1, *] := S1 1.16 S2 1.62 S3 2.03
    [polo_norteMG, Macauba, 2, *] := S1 1.33 S2 1.86 S3 2.33
    [polo_norteMG, Macauba, 3, *] := S1 1.2 S2 1.68 S3 2.1
    [polo_norteMG, Macauba, 4, *] := S1 1.89 S2 2.65 S3 3.31
    [polo_norteMG, Macauba, 5, *] := S1 1.6 S2 2.24 S3 2.8
    [polo_norteMG, Macauba, 6, *] := S1 1.47 S2 2.06 S3 2.58
    [polo_norteMG, Macauba, 7, *] := S1 1.12 S2 1.57 S3 1.96
    [polo_norteMG, Macauba, 8, *] := S1 1.28 S2 1.79 S3 2.24
    [polo_norteMG, Macauba, 9, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_norteMG, Macauba, 10, *] := S1 1.29 S2 1.81 S3 2.26
    [polo_norteMG, Macauba, 11, *] := S1 1.45 S2 2.03 S3 2.54
    [polo_norteMG, Macauba, 12, *] := S1 1.2 S2 1.68 S3 2.1
    [polo_norteMG, Macauba, 13, *] := S1 1.11 S2 1.55 S3 1.94
    [polo_norteMG, Macauba, 14, *] := S1 1.5 S2 2.1 S3 2.62
    [polo_norteMG, Macauba, 15, *] := S1 1.25 S2 1.75 S3 2.19
    [polo_norteMG, Macauba, 16, *] := S1 1.36 S2 1.9 S3 2.38
    [polo_norteMG, Macauba, 17, *] := S1 1.33 S2 1.86 S3 2.33
    [polo_norteMG, Macauba, 18, *] := S1 1.37 S2 1.92 S3 2.4
    [polo_norteMG, Macauba, 19, *] := S1 1.31 S2 1.83 S3 2.29
    [polo_norteMG, Macauba, 20, *] := S1 1.4 S2 1.96 S3 2.45
    [polo_norteMG, Macauba, 21, *] := S1 1.21 S2 1.69 S3 2.11
    [polo_norteMG, Macauba, 22, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_norteMG, Macauba, 23, *] := S1 1.19 S2 1.67 S3 2.09
    [polo_norteMG, Macauba, 24, *] := S1 1.5 S2 2.1 S3 2.62
    [polo_norteMG, Girassol, 1, *] := S1 1.26 S2 1.76 S3 2.2
    [polo_norteMG, Girassol, 2, *] := S1 1.49 S2 2.09 S3 2.61
    [polo_norteMG, Girassol, 3, *] := S1 1.43 S2 2.0 S3 2.5
    [polo_norteMG, Girassol, 4, *] := S1 1.31 S2 1.83 S3 2.29
    [polo_norteMG, Girassol, 5, *] := S1 1.77 S2 2.48 S3 3.1
    [polo_norteMG, Girassol, 6, *] := S1 1.74 S2 2.44 S3 3.05
    [polo_norteMG, Girassol, 7, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_norteMG, Girassol, 8, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_norteMG, Girassol, 9, *] := S1 1.32 S2 1.85 S3 2.31
    [polo_norteMG, Girassol, 10, *] := S1 1.06 S2 1.48 S3 1.85
    [polo_norteMG, Girassol, 11, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_norteMG, Girassol, 12, *] := S1 1.23 S2 1.72 S3 2.15
    [polo_norteMG, Girassol, 13, *] := S1 1.48 S2 2.07 S3 2.59
    [polo_norteMG, Girassol, 14, *] := S1 1.44 S2 2.02 S3 2.52
    [polo_norteMG, Girassol, 15, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_norteMG, Girassol, 16, *] := S1 1.63 S2 2.28 S3 2.85
    [polo_norteMG, Girassol, 17, *] := S1 1.42 S2 1.99 S3 2.49
    [polo_norteMG, Girassol, 18, *] := S1 1.89 S2 2.65 S3 3.31
    [polo_norteMG, Girassol, 19, *] := S1 1.44 S2 2.02 S3 2.52
    [polo_norteMG, Girassol, 20, *] := S1 1.15 S2 1.61 S3 2.01
    [polo_norteMG, Girassol, 21, *] := S1 1.32 S2 1.85 S3 2.31
    [polo_norteMG, Girassol, 22, *] := S1 1.3 S2 1.82 S3 2.27
    [polo_norteMG, Girassol, 23, *] := S1 1.08 S2 1.51 S3 1.89
    [polo_norteMG, Girassol, 24, *] := S1 1.38 S2 1.93 S3 2.41
    [polo_norteMG, Nabo_Forrageiro, 1, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_norteMG, Nabo_Forrageiro, 2, *] := S1 1.39 S2 1.95 S3 2.44
    [polo_norteMG, Nabo_Forrageiro, 3, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_norteMG, Nabo_Forrageiro, 4, *] := S1 1.3 S2 1.82 S3 2.27
    [polo_norteMG, Nabo_Forrageiro, 5, *] := S1 1.51 S2 2.11 S3 2.64
    [polo_norteMG, Nabo_Forrageiro, 6, *] := S1 1.31 S2 1.83 S3 2.29
    [polo_norteMG, Nabo_Forrageiro, 7, *] := S1 1.46 S2 2.04 S3 2.55
    [polo_norteMG, Nabo_Forrageiro, 8, *] := S1 1.44 S2 2.02 S3 2.52
    [polo_norteMG, Nabo_Forrageiro, 9, *] := S1 1.42 S2 1.99 S3 2.49
    [polo_norteMG, Nabo_Forrageiro, 10, *] := S1 1.15 S2 1.61 S3 2.01
    [polo_norteMG, Nabo_Forrageiro, 11, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_norteMG, Nabo_Forrageiro, 12, *] := S1 1.44 S2 2.02 S3 2.52
    [polo_norteMG, Nabo_Forrageiro, 13, *] := S1 1.47 S2 2.06 S3 2.58
    [polo_norteMG, Nabo_Forrageiro, 14, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_norteMG, Nabo_Forrageiro, 15, *] := S1 1.24 S2 1.74 S3 2.17
    [polo_norteMG, Nabo_Forrageiro, 16, *] := S1 1.34 S2 1.88 S3 2.35
    [polo_norteMG, Nabo_Forrageiro, 17, *] := S1 1.79 S2 2.51 S3 3.14
    [polo_norteMG, Nabo_Forrageiro, 18, *] := S1 1.8 S2 2.52 S3 3.15
    [polo_norteMG, Nabo_Forrageiro, 19, *] := S1 1.06 S2 1.48 S3 1.85
    [polo_norteMG, Nabo_Forrageiro, 20, *] := S1 1.24 S2 1.74 S3 2.17
    [polo_norteMG, Nabo_Forrageiro, 21, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_norteMG, Nabo_Forrageiro, 22, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_norteMG, Nabo_Forrageiro, 23, *] := S1 1.44 S2 2.02 S3 2.52
    [polo_norteMG, Nabo_Forrageiro, 24, *] := S1 1.21 S2 1.69 S3 2.11
    [polo_semiarido, Soja, 1, *] := S1 0.94 S2 1.32 S3 1.65
    [polo_semiarido, Soja, 2, *] := S1 1.08 S2 1.51 S3 1.89
    [polo_semiarido, Soja, 3, *] := S1 1.16 S2 1.62 S3 2.03
    [polo_semiarido, Soja, 4, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Soja, 5, *] := S1 1.28 S2 1.79 S3 2.24
    [polo_semiarido, Soja, 6, *] := S1 1.65 S2 2.31 S3 2.89
    [polo_semiarido, Soja, 7, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_semiarido, Soja, 8, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_semiarido, Soja, 9, *] := S1 1.07 S2 1.5 S3 1.88
    [polo_semiarido, Soja, 10, *] := S1 0.9 S2 1.26 S3 1.57
    [polo_semiarido, Soja, 11, *] := S1 0.95 S2 1.33 S3 1.66
    [polo_semiarido, Soja, 12, *] := S1 0.99 S2 1.39 S3 1.74
    [polo_semiarido, Soja, 13, *] := S1 1.1 S2 1.54 S3 1.93
    [polo_semiarido, Soja, 14, *] := S1 0.95 S2 1.33 S3 1.66
    [polo_semiarido, Soja, 15, *] := S1 0.94 S2 1.32 S3 1.65
    [polo_semiarido, Soja, 16, *] := S1 1.14 S2 1.6 S3 2.0
    [polo_semiarido, Soja, 17, *] := S1 1.45 S2 2.03 S3 2.54
    [polo_semiarido, Soja, 18, *] := S1 1.23 S2 1.72 S3 2.15
    [polo_semiarido, Soja, 19, *] := S1 1.23 S2 1.72 S3 2.15
    [polo_semiarido, Soja, 20, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Soja, 21, *] := S1 0.88 S2 1.23 S3 1.54
    [polo_semiarido, Soja, 22, *] := S1 0.95 S2 1.33 S3 1.66
    [polo_semiarido, Soja, 23, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_semiarido, Soja, 24, *] := S1 0.94 S2 1.32 S3 1.65
    [polo_semiarido, Algodao, 1, *] := S1 0.91 S2 1.27 S3 1.59
    [polo_semiarido, Algodao, 2, *] := S1 1.25 S2 1.75 S3 2.19
    [polo_semiarido, Algodao, 3, *] := S1 1.09 S2 1.53 S3 1.91
    [polo_semiarido, Algodao, 4, *] := S1 1.37 S2 1.92 S3 2.4
    [polo_semiarido, Algodao, 5, *] := S1 1.54 S2 2.16 S3 2.7
    [polo_semiarido, Algodao, 6, *] := S1 1.55 S2 2.17 S3 2.71
    [polo_semiarido, Algodao, 7, *] := S1 0.93 S2 1.3 S3 1.62
    [polo_semiarido, Algodao, 8, *] := S1 0.89 S2 1.25 S3 1.56
    [polo_semiarido, Algodao, 9, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_semiarido, Algodao, 10, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_semiarido, Algodao, 11, *] := S1 1.05 S2 1.47 S3 1.84
    [polo_semiarido, Algodao, 12, *] := S1 1.16 S2 1.62 S3 2.03
    [polo_semiarido, Algodao, 13, *] := S1 1.14 S2 1.6 S3 2.0
    [polo_semiarido, Algodao, 14, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_semiarido, Algodao, 15, *] := S1 0.89 S2 1.25 S3 1.56
    [polo_semiarido, Algodao, 16, *] := S1 1.33 S2 1.86 S3 2.33
    [polo_semiarido, Algodao, 17, *] := S1 1.29 S2 1.81 S3 2.26
    [polo_semiarido, Algodao, 18, *] := S1 1.58 S2 2.21 S3 2.76
    [polo_semiarido, Algodao, 19, *] := S1 0.96 S2 1.34 S3 1.68
    [polo_semiarido, Algodao, 20, *] := S1 0.93 S2 1.3 S3 1.62
    [polo_semiarido, Algodao, 21, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_semiarido, Algodao, 22, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_semiarido, Algodao, 23, *] := S1 0.97 S2 1.36 S3 1.7
    [polo_semiarido, Algodao, 24, *] := S1 0.96 S2 1.34 S3 1.68
    [polo_semiarido, Macauba, 1, *] := S1 1.24 S2 1.74 S3 2.17
    [polo_semiarido, Macauba, 2, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_semiarido, Macauba, 3, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Macauba, 4, *] := S1 1.41 S2 1.97 S3 2.46
    [polo_semiarido, Macauba, 5, *] := S1 1.13 S2 1.58 S3 1.98
    [polo_semiarido, Macauba, 6, *] := S1 1.66 S2 2.32 S3 2.9
    [polo_semiarido, Macauba, 7, *] := S1 1.21 S2 1.69 S3 2.11
    [polo_semiarido, Macauba, 8, *] := S1 1.26 S2 1.76 S3 2.2
    [polo_semiarido, Macauba, 9, *] := S1 1.24 S2 1.74 S3 2.17
    [polo_semiarido, Macauba, 10, *] := S1 1.21 S2 1.69 S3 2.11
    [polo_semiarido, Macauba, 11, *] := S1 0.92 S2 1.29 S3 1.61
    [polo_semiarido, Macauba, 12, *] := S1 1.06 S2 1.48 S3 1.85
    [polo_semiarido, Macauba, 13, *] := S1 0.94 S2 1.32 S3 1.65
    [polo_semiarido, Macauba, 14, *] := S1 1.02 S2 1.43 S3 1.79
    [polo_semiarido, Macauba, 15, *] := S1 0.87 S2 1.22 S3 1.52
    [polo_semiarido, Macauba, 16, *] := S1 1.31 S2 1.83 S3 2.29
    [polo_semiarido, Macauba, 17, *] := S1 1.65 S2 2.31 S3 2.89
    [polo_semiarido, Macauba, 18, *] := S1 1.25 S2 1.75 S3 2.19
    [polo_semiarido, Macauba, 19, *] := S1 1.18 S2 1.65 S3 2.06
    [polo_semiarido, Macauba, 20, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_semiarido, Macauba, 21, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_semiarido, Macauba, 22, *] := S1 1.26 S2 1.76 S3 2.2
    [polo_semiarido, Macauba, 23, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_semiarido, Macauba, 24, *] := S1 1.09 S2 1.53 S3 1.91
    [polo_semiarido, Girassol, 1, *] := S1 1.16 S2 1.62 S3 2.03
    [polo_semiarido, Girassol, 2, *] := S1 0.92 S2 1.29 S3 1.61
    [polo_semiarido, Girassol, 3, *] := S1 0.98 S2 1.37 S3 1.71
    [polo_semiarido, Girassol, 4, *] := S1 1.64 S2 2.3 S3 2.88
    [polo_semiarido, Girassol, 5, *] := S1 1.42 S2 1.99 S3 2.49
    [polo_semiarido, Girassol, 6, *] := S1 1.4 S2 1.96 S3 2.45
    [polo_semiarido, Girassol, 7, *] := S1 1.17 S2 1.64 S3 2.05
    [polo_semiarido, Girassol, 8, *] := S1 0.87 S2 1.22 S3 1.52
    [polo_semiarido, Girassol, 9, *] := S1 1.1 S2 1.54 S3 1.93
    [polo_semiarido, Girassol, 10, *] := S1 1.06 S2 1.48 S3 1.85
    [polo_semiarido, Girassol, 11, *] := S1 1.21 S2 1.69 S3 2.11
    [polo_semiarido, Girassol, 12, *] := S1 0.92 S2 1.29 S3 1.61
    [polo_semiarido, Girassol, 13, *] := S1 1.26 S2 1.76 S3 2.2
    [polo_semiarido, Girassol, 14, *] := S1 0.88 S2 1.23 S3 1.54
    [polo_semiarido, Girassol, 15, *] := S1 0.93 S2 1.3 S3 1.62
    [polo_semiarido, Girassol, 16, *] := S1 1.43 S2 2.0 S3 2.5
    [polo_semiarido, Girassol, 17, *] := S1 1.48 S2 2.07 S3 2.59
    [polo_semiarido, Girassol, 18, *] := S1 1.23 S2 1.72 S3 2.15
    [polo_semiarido, Girassol, 19, *] := S1 0.9 S2 1.26 S3 1.57
    [polo_semiarido, Girassol, 20, *] := S1 1.23 S2 1.72 S3 2.15
    [polo_semiarido, Girassol, 21, *] := S1 0.95 S2 1.33 S3 1.66
    [polo_semiarido, Girassol, 22, *] := S1 1.1 S2 1.54 S3 1.93
    [polo_semiarido, Girassol, 23, *] := S1 1.11 S2 1.55 S3 1.94
    [polo_semiarido, Girassol, 24, *] := S1 1.03 S2 1.44 S3 1.8
    [polo_semiarido, Nabo_Forrageiro, 1, *] := S1 1.1 S2 1.54 S3 1.93
    [polo_semiarido, Nabo_Forrageiro, 2, *] := S1 1.07 S2 1.5 S3 1.88
    [polo_semiarido, Nabo_Forrageiro, 3, *] := S1 1.25 S2 1.75 S3 2.19
    [polo_semiarido, Nabo_Forrageiro, 4, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Nabo_Forrageiro, 5, *] := S1 1.5 S2 2.1 S3 2.62
    [polo_semiarido, Nabo_Forrageiro, 6, *] := S1 1.24 S2 1.74 S3 2.17
    [polo_semiarido, Nabo_Forrageiro, 7, *] := S1 1.02 S2 1.43 S3 1.79
    [polo_semiarido, Nabo_Forrageiro, 8, *] := S1 1.14 S2 1.6 S3 2.0
    [polo_semiarido, Nabo_Forrageiro, 9, *] := S1 0.98 S2 1.37 S3 1.71
    [polo_semiarido, Nabo_Forrageiro, 10, *] := S1 0.98 S2 1.37 S3 1.71
    [polo_semiarido, Nabo_Forrageiro, 11, *] := S1 1.17 S2 1.64 S3 2.05
    [polo_semiarido, Nabo_Forrageiro, 12, *] := S1 0.88 S2 1.23 S3 1.54
    [polo_semiarido, Nabo_Forrageiro, 13, *] := S1 1.04 S2 1.46 S3 1.82
    [polo_semiarido, Nabo_Forrageiro, 14, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_semiarido, Nabo_Forrageiro, 15, *] := S1 1.27 S2 1.78 S3 2.23
    [polo_semiarido, Nabo_Forrageiro, 16, *] := S1 1.15 S2 1.61 S3 2.01
    [polo_semiarido, Nabo_Forrageiro, 17, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Nabo_Forrageiro, 18, *] := S1 1.25 S2 1.75 S3 2.19
    [polo_semiarido, Nabo_Forrageiro, 19, *] := S1 1.25 S2 1.75 S3 2.19
    [polo_semiarido, Nabo_Forrageiro, 20, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Nabo_Forrageiro, 21, *] := S1 1.22 S2 1.71 S3 2.14
    [polo_semiarido, Nabo_Forrageiro, 22, *] := S1 1.01 S2 1.41 S3 1.76
    [polo_semiarido, Nabo_Forrageiro, 23, *] := S1 0.92 S2 1.29 S3 1.61
    [polo_semiarido, Nabo_Forrageiro, 24, *] := S1 1.2 S2 1.68 S3 2.1;

param AZ :=
    [polo_norteMG, *]     := 1 12.0 2 12.0 3 12.0 4 12.0 5 12.0 6 12.0 7 12.0 8 12.0 9 12.0 10 12.0 11 12.0 12 12.0 13 12.0 14 12.0 15 12.0 16 12.0 17 12.0 18 12.0 19 12.0 20 12.0 21 12.0 22 12.0 23 12.0 24 12.0
    [polo_semiarido, *] := 1 15.0 2 15.0 3 15.0 4 15.0 5 15.0 6 15.0 7 15.0 8 15.0 9 15.0 10 15.0 11 15.0 12 15.0 13 15.0 14 15.0 15 15.0 16 15.0 17 15.0 18 15.0 19 15.0 20 15.0 21 15.0 22 15.0 23 15.0 24 15.0;

param Z_barra :=
    [polo_norteMG, Soja, *]             := 1 1500 2 1500 3 1500 4 1500 5 1500 6 1500 7 1500 8 1500 9 1500 10 1500 11 1500 12 1500 13 1500 14 1500 15 1500 16 1500 17 1500 18 1500 19 1500 20 1500 21 1500 22 1500 23 1500 24 1500
    [polo_norteMG, Algodao, *]          := 1 600 2 600 3 600 4 600 5 600 6 600 7 600 8 600 9 600 10 600 11 600 12 600 13 600 14 600 15 600 16 600 17 600 18 600 19 600 20 600 21 600 22 600 23 600 24 600
    [polo_norteMG, Macauba, *]          := 1 300 2 300 3 300 4 300 5 300 6 300 7 300 8 300 9 300 10 300 11 300 12 300 13 300 14 300 15 300 16 300 17 300 18 300 19 300 20 300 21 300 22 300 23 300 24 300
    [polo_norteMG, Girassol, *]         := 1 180 2 180 3 180 4 180 5 180 6 180 7 180 8 180 9 180 10 180 11 180 12 180 13 180 14 180 15 180 16 180 17 180 18 180 19 180 20 180 21 180 22 180 23 180 24 180
    [polo_norteMG, Nabo_Forrageiro, *]  := 1 120 2 120 3 120 4 120 5 120 6 120 7 120 8 120 9 120 10 120 11 120 12 120 13 120 14 120 15 120 16 120 17 120 18 120 19 120 20 120 21 120 22 120 23 120 24 120
    [polo_semiarido, Soja, *]           := 1 960 2 960 3 960 4 960 5 960 6 960 7 960 8 960 9 960 10 960 11 960 12 960 13 960 14 960 15 960 16 960 17 960 18 960 19 960 20 960 21 960 22 960 23 960 24 960
    [polo_semiarido, Algodao, *]        := 1 420 2 420 3 420 4 420 5 420 6 420 7 420 8 420 9 420 10 420 11 420 12 420 13 420 14 420 15 420 16 420 17 420 18 420 19 420 20 420 21 420 22 420 23 420 24 420
    [polo_semiarido, Macauba, *]        := 1 300 2 300 3 300 4 300 5 300 6 300 7 300 8 300 9 300 10 300 11 300 12 300 13 300 14 300 15 300 16 300 17 300 18 300 19 300 20 300 21 300 22 300 23 300 24 300
    [polo_semiarido, Girassol, *]       := 1 150 2 150 3 150 4 150 5 150 6 150 7 150 8 150 9 150 10 150 11 150 12 150 13 150 14 150 15 150 16 150 17 150 18 150 19 150 20 150 21 150 22 150 23 150 24 150
    [polo_semiarido, Nabo_Forrageiro, *]:= 1 150 2 150 3 150 4 150 5 150 6 150 7 150 8 150 9 150 10 150 11 150 12 150 13 150 14 150 15 150 16 150 17 150 18 150 19 150 20 150 21 150 22 150 23 150 24 150;

param TF := 1 150 2 150 3 150 4 150 5 150 6 150 7 150 8 150 9 150 10 150 11 150 12 150 13 180 14 180 15 180 16 180 17 180 18 180 19 180 20 180 21 180 22 180 23 180 24 180;

param OfertaOGR :=
    [rede_catadores_moc, *] := 1 4200 2 4320 3 4500 4 4800 5 4920 6 4680 7 4380 8 4200 9 4080 10 4140 11 4260 12 4380 13 4680 14 4800 15 4980 16 5400 17 5520 18 5160 19 4860 20 4620 21 4500 22 4560 23 4740 24 4860
    [rede_urbana, *]        := 1 900 2 930 3 960 4 1020 5 1050 6 990 7 930 8 900 9 870 10 888 11 912 12 948 13 1080 14 1110 15 1140 16 1260 17 1290 18 1200 19 1140 20 1080 21 1050 22 1068 23 1110 24 1140;

param CompraMax := 1 720 2 732 3 750 4 780 5 810 6 780 7 750 8 720 9 690 10 708 11 726 12 750 13 900 14 930 15 960 16 1080 17 1110 18 1020 19 960 20 900 21 870 22 888 23 930 24 960;

end;
