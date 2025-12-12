# 🚁 SGSV - Sistema de Gestão de Solicitações de Voo
**Status Python Estrutura**

## 📖 Sobre o Projeto
O **SGSV** é uma solução Web desenvolvida para centralizar, padronizar e gerenciar as rotas de voo de drones das 27 Unidades de Vigilância em Saúde (UVIS).

**Problema Resolvido:** Substituição do fluxo descentralizado (envio de planilhas via e-mail/WhatsApp), eliminando redundância, insegurança de dados e falta de rastreabilidade.

🎯 Objetivo

Criar um painel unificado onde:

As UVIS possam emitir solicitações de voo

O setor técnico faça análise, gere coordenadas e protocolos DECEA

Haja isolamento de dados (RLS) entre unidades

Haja rastreamento completo do ciclo da solicitação

## ⚙️ Funcionalidades e Requisitos

### Canais de Segurança
- **[RF01] Autenticação Inteligente:** Login único que identifica automaticamente a Região (CRS), UVIS e Código do Setor do usuário.
- **[RF02] Isolamento de Dados (RLS):** Garantia de que usuários de uma unidade não visualizem interferências de outras unidades.

### Unidade (Solicitante)
- **[RF03] Solicitação de Voo:** Formulário simplificado onde a unidade informa apenas os dados variáveis (Data Prevista, Endereço, Foco da Ação).
- **[RF04] Feedback Visual:** Acompanhamento em tempo real do status da solicitação (🟡 Em Análise, 🟢 Aprovado, 🔴 Negado).

### Módulo Administrativo (Gestão)
- **[RF05] Painel de Controle:** Visão global de todas as propostas pendentes com filtros por região.
- **[RF06] Exportação SARPAS:** Geração automática de arquivos (.csv / .xlsx) formatados para importação em massa em sistemas de controle de espaço aéreo.
- **[RF07] Tratamento Técnico:** Inserção de Coordenadas Geográficas e Protocolos DECEA para aprovação do voo.

## 🔄 Fluxo de Status

| Status         | Quando ocorre         | Responsável      |
| -------------- | --------------------- | ---------------- |
| **PENDENTE**   | Solicitação criada    | UVIS             |
| **EM ANÁLISE** | Enviado ao DECEA      | Operador / Admin |
| **APROVADO**   | Autorização concedida | Operador / Admin |
| **NEGADO**     | Autorização recusada  | Operador / Admin |


## 🏗️ Arquitetura e Modelagem

### Modelo de Entidade e Relacionamento (MER)
Uma estrutura de dados foi projetada para garantir a integridade referencial entre as unidades e seus pedidos.

```mermaid
erDiagram
    USUARIO ||--o{ SOLICITACAO : "registro"
    
    USUARIO {
        int id PK
        string nome_uvis
        string regiao
        string login
        string senha_hash
        string nivel_acesso
    }

    SOLICITACAO {
        int id PK
        int usuario_id FK
        datetime data_criacao
        date data_voo_prevista
        time hora_voo_prevista
        string logradouro
        string bairro
        string cidade
        string uf
        string numero
        string complemento
        string cep
        string latitude
        string longitude
        string tipo_visita
        string altura_voo
        boolean criadouro
        boolean apoio_cet
        string observacao
        string foco_acao
        string status_voo
        string protocolo_decea
        string motivo_recusa
    }
```

## ⚙️ Fluxo de Uso

Diagrama de fluxo do sistema:

```mermaid
graph TD

    %% --- SUBGRAFO 1: SOLICITAÇÃO ---
    subgraph Fluxo_de_Solicitacao
        UVIS((UVIS)) --> BD_PENDENTE["BD_PENDENTE (Status: PENDENTE)"]
    end

    %% --- SUBGRAFO 2: GESTÃO E VISUALIZAÇÃO ---
    subgraph Fluxo_de_Gestao_Visualizacao
        BD_PENDENTE --> Analise["Tratamento Técnico / Operador"]
        
        Analise --> BD_ANALISE["BD_ANALISE (Status: EM ANÁLISE)"]
        
        BD_ANALISE --> Decisao{"Decisão DECEA"}
        
        Decisao -- "Aprovado" --> BD_APROVADO["BD_APROVADO (Status: APROVADO)"]
        Decisao -- "Negado" --> BD_NEGADO["BD_NEGADO (Status: NEGADO)"]

        Admin["Admin"] --> Relatorio["Relatório de Controle"]
        COVISA((COVISA)) --> Visualizacao["Painel Global de Leitura"]

        BD_APROVADO --> UVIS
        BD_NEGADO --> UVIS
    end

```

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Framework Web:** Flask (Microframework ágil)
- **Banco de Dados:** SQL (SQLite para Dev / PostgreSQL para Produção)
- **ORM:** SQLAlchemy
- **Frontend:** HTML5, CSS3, Bootstrap 5 (Responsivo para dispositivos móveis/desktop)
- **Controle de versão:** Git e GitHub

## 📦 Como rodar o projeto localmente

### Pré-requisitos

- Python instalado
- Git instalado

### Passo a passo

1. **Clonar o repositório**
    ```bash
    git clone https://github.com/seu-usuario/sgsv-sistema.git
    cd sgsv-sistema
    ```

2. **Criar um ambiente virtual**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3. **Instalar as dependências**
    ```bash
    pip install -r requirements.txt
    ```

4. **Inicializar o Banco de Dados**
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

5. **Executar a aplicação**
    ```bash
    python run.py
    ```

O sistema estará acessível em: [http://localhost:5000](http://localhost:5000)

## 📂 Estrutura de Pastas
```plaintext
sgsv-sistema/
├── app/
│   ├── __init__.py
│   ├── models.py  # Classes do Banco de Dados (ORM)
│   ├── routes.py  # Lógica das rotas (Login, Dash, Admin)
│   ├── static/    # CSS, JS, Imagens
│   └── templates/ # Arquivos HTML (Jinja2)
│       ├── login.html
│       ├── dashboard.html
│       └── admin.html
├── config.py      # Configurações de Ambiente
├── requirements.txt # Dependências do Python
├── run.py         # Arquivo de execução
└── README.md      # Documentação
```
## 🤝 Contribuição

1. **Faça um Fork do projeto.**
2. **Crie um Branch para sua Feature:**
    ```bash
    git checkout -b feature/NovaFeature
    ```
3. **Faça o Commit:**
    ```bash
    git commit -m 'Adicionando novo recurso'
    ```
4. **Faça o Push:**
    ```bash
    git push origin feature/NovaFeature
    ```
5. **Abra um Pull Request.**

## 📄 Licença

© 2025 Oceano Azul | IJA Drones.
Todos os direitos reservados.
**Desenvolvido para otimização de processos das UVIS.**
