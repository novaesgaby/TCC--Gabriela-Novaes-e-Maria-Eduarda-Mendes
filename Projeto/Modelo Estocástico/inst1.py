# =============================================================================================================
# SEÇÃO DE DADOS (DATA) - MODELO PBIO (VERSÃO 7 ESTOCÁSTICO) - Instância 1 
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
param preco_biodiesel := 4619.71;         # valor da venda unitária do biodiesel por tonelada
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
param Capacidade_Usina := 9817.2;       # Capacidade mensal proporcional (~16.3k t/mês)

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
    1 7200 2 7200 3 8400 4 9000 5 9000 6 8400 7 7200 8 6600 9 6600 10 6600 11 7200 12 7200 13 7800 14 7800 15 9000 16 9600 17 9600 18 9000 19 7800 20 7200 21 7200 22 7800 23 7800 24 7800;

param Cap_Armazenagem :=
    1 4500 2 4500 3 5400 4 6000 5 6000 6 5400 7 4800 8 4500 9 4500 10 4500 11 4500 12 4500 13 4800 14 4800 15 5700 16 6300 17 6300 18 5700 19 5100 20 4800 21 4800 22 4800 23 4800 24 4800;

param Cap_Frota_Caminhoes :=
    1 7200 2 7200 3 8400 4 9000 5 9000 6 8400 7 7200 8 6600 9 6600 10 6600 11 7200 12 7200 13 7800 14 7800 15 9000 16 9600 17 9600 18 9000 19 7800 20 7200 21 7200 22 7800 23 7800 24 7800;

param Cap_Carregamento :=
    1 6600 2 6600 3 7200 4 7800 5 7800 6 7200 7 6600 8 6600 9 6600 10 6600 11 6600 12 6600 13 7200 14 7200 15 7800 16 8400 17 8400 18 7800 19 7200 20 7200 21 7200 22 7200 23 7200 24 7200;

param C_OGR := rede_catadores_moc 110.0 rede_urbana 125.0;

param PC :=
    [polo_norteMG, *]   := Soja 140.0 Algodao 160.0 Macauba 120.0 Girassol 150.0 Nabo_Forrageiro 130.0
    [polo_semiarido, *] := Soja 155.0 Algodao 175.0 Macauba 135.0 Girassol 165.0 Nabo_Forrageiro 145.0;

param GTC := polo_norteMG 18.0 polo_semiarido 25.0;

# Demanda estocástica sazonal por cenário (S1=Baixa/Seca, S2=Médio, S3=Alta/Aquecida) para os 24 meses
param D :=
    [1, *] := S1 4200.0 S2 4800.0 S3 5730.0
    [2, *] := S1 4140.0 S2 4890.0 S3 5760.0
    [3, *] := S1 4380.0 S2 4980.0 S3 5880.0
    [4, *] := S1 4500.0 S2 5100.0 S3 6000.0
    [5, *] := S1 4560.0 S2 5220.0 S3 6120.0
    [6, *] := S1 4440.0 S2 5040.0 S3 5940.0
    [7, *] := S1 4320.0 S2 4920.0 S3 5820.0
    [8, *] := S1 4200.0 S2 4800.0 S3 5700.0
    [9, *] := S1 3900.0 S2 4740.0 S3 5640.0
    [10, *] := S1 4260.0 S2 4860.0 S3 5760.0
    [11, *] := S1 4260.0 S2 4980.0 S3 5880.0
    [12, *] := S1 4500.0 S2 5100.0 S3 6060.0
    [13, *] := S1 4680.0 S2 5520.0 S3 6600.0
    [14, *] := S1 4920.0 S2 5640.0 S3 6720.0
    [15, *] := S1 4980.0 S2 5820.0 S3 6900.0
    [16, *] := S1 5280.0 S2 6000.0 S3 7080.0
    [17, *] := S1 4920.0 S2 5880.0 S3 6960.0
    [18, *] := S1 4980.0 S2 5700.0 S3 6780.0
    [19, *] := S1 4800.0 S2 5580.0 S3 6660.0
    [20, *] := S1 4740.0 S2 5460.0 S3 6540.0
    [21, *] := S1 4740.0 S2 5520.0 S3 6600.0
    [22, *] := S1 4920.0 S2 5640.0 S3 6780.0
    [23, *] := S1 4830.0 S2 5760.0 S3 6900.0
    [24, *] := S1 5160.0 S2 5880.0 S3 7020.0;

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
    [polo_norteMG, *]   := 1 12.0 2 12.0 3 12.0 4 12.0 5 12.0 6 12.0 7 12.0 8 12.0 9 12.0 10 12.0 11 12.0 12 12.0 13 12.0 14 12.0 15 12.0 16 12.0 17 12.0 18 12.0 19 12.0 20 12.0 21 12.0 22 12.0 23 12.0 24 12.0
    [polo_semiarido, *] := 1 15.0 2 15.0 3 15.0 4 15.0 5 15.0 6 15.0 7 15.0 8 15.0 9 15.0 10 15.0 11 15.0 12 15.0 13 15.0 14 15.0 15 15.0 16 15.0 17 15.0 18 15.0 19 15.0 20 15.0 21 15.0 22 15.0 23 15.0 24 15.0;

param Z_barra :=
    [polo_norteMG, Soja, *]              := 1 1500 2 1500 3 1500 4 1500 5 1500 6 1500 7 1500 8 1500 9 1500 10 1500 11 1500 12 1500 13 1500 14 1500 15 1500 16 1500 17 1500 18 1500 19 1500 20 1500 21 1500 22 1500 23 1500 24 1500
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
