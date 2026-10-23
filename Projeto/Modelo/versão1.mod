
# MODELO DE OTIMIZAÇÃO DA CADEIA DE SUPRIMENTOS - PBIO (MONTES CLAROS)
# ==============================================================================

# CONJUNTOS (Índices)
set T; # Períodos de tempo (ex: Semestres ou Meses de 2024/2025)
set P; # Zonas produtoras de oleaginosas (Agricultura Familiar / Semiárido)
set R; # Cooperativas/Fontes de Óleos e Gorduras Residuais (OGR)

# PARAMETROS
param alfa;                           # Rendimento de óleo na semente (Soja ~ 0.18 a 0.20)
param gama{P, T};                     # Produtividade agrícola na zona p no período t
param AZ{P, T};                       # Tamanho médio dos lotes das famílias na zona p
param Z_barra{P, T};                  # Área máxima disponível para cultivo na zona p
param D{T};                           # Demanda total de biodiesel/óleo em Montes Claros no período t
param TF{T};                          # Número mínimo de famílias do Selo Social exigido no período t

# PARÂMETROS DE CUSTO (Componentes da DRE)
param PC{P};                          # Custo unitário de produção agrícola na zona p
param GTC{P};                         # Custo de transporte de sementes da zona p até a usina
param CC;                             # Custo unitário de esmagamento/processamento na usina
param C_OGR{R};                       # Custo unitário de aquisição de OGR da fonte r
param v_cost{T};                      # Custo de oportunidade para comprar óleo vegetal bruto do mercado

# VARIÁVEIS DE DECISÃO
var z{P, T} >= 0;                     # Área de terra alocada para agricultura familiar
var gx{P, T} >= 0;                    # Volume de sementes transportadas das zonas agrícolas
var ogr_x{R, T} >= 0;                 # Volume de OGR adquirido de cooperativas de catadores
var w{T} >= 0;                        # Total de sementes trituradas na planta
var v{T} >= 0;                        # Óleo complementar adquirido diretamente do mercado regulado

# FUNÇÃO OBJETIVO: Minimizar o Custo Total de Produção e Logística
minimize Custo_Total:
    sum{p in P, t in T} (PC[p] * z[p,t]) +      # Custos de fomento agrícola
    sum{p in P, t in T} (GTC[p] * gx[p,t]) +    # Custos de logística de suprimentos (Inbound)
    sum{t in T} (CC * w[t]) +                  # Custos industriais de processamento
    sum{r in R, t in T} (C_OGR[r] * ogr_x[r,t]) + # Custos com a cadeia de reciclagem (OGR)
    sum{t in T} (v_cost[t] * v[t]);            # Custo de compra direta de óleo de terceiros

# RESTRIÇÕES DO SISTEMA

s.t. Atendimento_Demanda{t in T}:
    (alfa * w[t]) + sum{r in R} ogr_x[r,t] + v[t] >= D[t];

s.t. Limite_Area_Disponivel{p in P, t in T}:
    z[p,t] <= Z_barra[p,t];

s.t. Cumprimento_Selo_Social{t in T}:
    sum{p in P} (z[p,t] / AZ[p,t]) >= TF[t];

s.t. Balanco_Massa_Agricola{p in P, t in T}:
    gx[p,t] = gama[p,t] * z[p,t];

s.t. Capacidade_Trituracao{t in T}:
    w[t] = sum{p in P} gx[p,t];

s.t. Percentual_Minimo_OGR{t in T}:
    sum{r in R} ogr_x[r,t] >= 0.14 * D[t]; 
    # Restrição orientada ao cenário real de 2025: 14% de OGR em Montes Claros
data;
