<h1 align="center" style="font-weight: bold;">TCC PBio 💻</h1>

<p align="center">
  <b>Simulação e Otimização da Cadeia de Suprimentos de Biocombustíveis (PBio).</b>
</p>

Este repositório contém a modelagem computacional desenvolvida para o **Trabalho de Conclusão de Curso (TCC)** no curso de **Engenharia de Produção** da **Universidade Federal de Minas Gerais (UFMG)**.

O projeto tem como foco o planejamento e a otimização da cadeia de suprimentos da **Petrobras Biocombustível (PBio)**, integrando decisões de **S&OP (Sales and Operations Planning)** e **S&OE (Sales and Operations Execution)** para reduzir custos operacionais, avaliar o mix de matérias-primas e suportar a tomada de decisão em cenários de incerteza.

## 👥 Autoria e Orientação

* **Autoras:** Gabriela dos Santos Novaes Rocha e Maria Eduarda Mendes Sabino Alves
* **Orientador:** Prof. João Flávio de Freitas Almeida
* **Coorientador:** Prof. Braulio Frances Barcelos
* **Instituição:** Universidade Federal de Minas Gerais (UFMG) | Departamento de Engenharia de Produção (DEP)

## 🎯 Objetivo do Projeto

O objetivo principal é representar o comportamento determinístico e estocástico da cadeia de Suprimentos de Biocombustível em Minas Gerais.


A modelagem foi construída de forma **incremental (6 versões)** para testar desde a formulação matemática básica até a complexidade real.

* **Evolução do Modelo (`.mod` e `.dat`):** Transição de uma Programação Linear Mista (MILP) para um modelo estocástico incorporando restrições de multi-matéria-prima (soja, macaúba, girassol, OGR, etc.), incorporando perdas físicas (transporte, armazenagem, esmagamento), receitas de coprodutos (farelo, glicerina, CBIOs) e variáveis binárias de infraestrutura.
* **Instâncias e Simulação em Python:** As instâncias criadas em Python teve como objetivo testar os cenários.

## 📁 Estrutura do Repositório

```text
├── models/             # Arquivos de modelagem matemática (.mod em MathProg/GLPK)
├── data/               # Arquivos de dados de entrada (.dat)
├── instances/          # Instâncias e cenários para simulação em Python (.py)
└── README.md           # Documentação do repositório
