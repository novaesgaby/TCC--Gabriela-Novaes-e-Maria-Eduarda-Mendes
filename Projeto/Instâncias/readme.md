<h1 align="center" style="font-weight: bold;">TCC PBio 💻</h1>

<p align="center">
  <b>Simulação e Otimização da Cadeia de Suprimentos de Biocombustíveis (PBio).</b>
</p>

## 📝Construção - Instâncias

A partir de estudos e pesquisas sobre métodos de geração de instâncias, foi desenvolvido um script integrado em **Python** capaz gerar dinamicamente arquivos de dados e acionar o resolvedor de código aberto **GLPK (GNU Linear Programming Kit)** de forma automatizada, foram gerados 20 instâncias para cada modelo.

O script está dividido em duas etapas principais:
1. **Definição do Modelo Matemático (`.mod`)**: É definido o modelo .mod que será gerado as 20 instâncias. 
2. **Geração Automatizada de Cenários e Otimización (`.dat`)**: Script em Python que instancia 20 cenários variando o porte da usina em (Pequeno, Médio e Grande) e executa o solver iterativamente.

---

## ⚙️ Bibliotecas e Funções Utilizadas

O script faz uso de módulos do Python para gerenciar o sistema de arquivos.

* **`random` (Geração de Números Pseudo-Aleatórios):** Utilizada para simular a variabilidade de mercado (como oscilações na demanda dos anos de 2024 e 2025 e flutuações no preço do biodiesel). 
  * *Reprodutibilidade:* A função `random.seed(42)` foi usada para fixar a semente aleatória, garantindo que as mesmas instâncias possam ser replicadas.
* **`round` (Arredondamento Numérico):** Aplicada para formatar os valores gerados aleatoriamente com precisão decimal adequada, evitando inconsistências de ponto flutuante na formatação da sintaxe do AMPL.
* **`subprocess` (Automação de Processos do Sistema):** Utilizada para interagir diretamente com o sistema operacional e executar o solver externo GLPK (`glpsol`) em segundo plano, enviando os arquivos de modelo e dados e recuperando os relatórios de saída de forma programática.
* **`os` (Gerenciamento de Diretórios e Arquivos):** Responsável por manipular a escrita, salvamento e leitura local dos arquivos de modelo (`.mod`), de dados (`.dat`) e os relatórios de resultados textuais (`.txt`).

---

## ⚙️ Estrutura do Código e Fluxo de Execução

### Passo 1: Definição do Modelo Matemático
O script escreve localmente o arquivo de exemplo `pbio_versao6.mod`, contendo:
* **Conjuntos** 
* **Variáveis de Decisão**
* **Função Objetivo** 
* **Restrições** 

### Passo 2: Geração de Instâncias por Portes e Otimização Automatizada
O script dimensiona **20 instâncias** distintas divididas em três categorias de capacidade industrial (Porte):
* **Pequeno Porte (Instâncias 1 a 6):** Fator de escala de 0.6, reduzindo proporcionalmente as demandas e capacidades da rede.
* **Médio Porte (Instâncias 7 a 14):** Fator de escala de 1.0 (configuração padrão de referência).
* **Grande Porte (Instâncias 15 a 20):** Fator de escala de 1.4, ampliando as capacidades operacionais e de mercado.

Para cada iteração, o script:
1. Calcula os parâmetros dimensionados pelo fator de escala.
2. Escreve um arquivo de dados dedicado (`instancia_i.dat`).
3. Chama o GLPK via `subprocess` utilizando a linha de comando:
   ```bash
   glpsol -m pbio_versao6.mod -d instancia_i.dat -o resultado_i.txt
