# GRASS - RPG de Texto Potenciado por IA 🐉🤖

O **GRASS** é um jogo de RPG de texto inovador construído em Python. Utiliza a biblioteca **Pygame** para a interface gráfica e integra Inteligência Artificial (Modelos de Linguagem - LLMs) para gerar dinamicamente a narrativa, interagir com o jogador e gerir os eventos do mundo.

## ✨ Funcionalidades

* **Narrativa Dinâmica:** O mundo reage às suas ações com textos gerados por IA em tempo real.
* **Criação de Personagens:** Escolha atributos, classes e raças para moldar a sua jornada (`CharacterCreator.py`).
* **Sistema de Combate:** Lute contra entidades e monstros num sistema que mistura mecânicas clássicas de RPG com consequências narrativas (`CombatScene.py`, `combat.py`).
* **Interface Gráfica Personalizada:** Elementos de UI construídos de raiz sobre o Pygame, incluindo botões, barras de vida, caixas de texto e imagens estáticas.
* **Gestão de Inventário:** Colete, utilize e venda itens (`Item.py`, `player.py`).

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Motor Gráfico/UI:** Pygame
* **Integração IA:** OpenAI API (ou compatível, dependendo da configuração no motor de IA)

## 📁 Estrutura do Projeto

A arquitetura do projeto está dividida entre o Motor do Jogo (Engine) e o Modelo de Domínio (Model), garantindo uma boa organização:

```text
GRASS/
├── assets/                 # Imagens, sons e tipos de letra (fonts)
├── src/
│   ├── engine/             # Lógica de interface, cenas, loop principal e integração com IA
│   │   ├── ai/             # Scripts para comunicação e gestão de streaming de tokens da IA
│   │   ├── scene/          # Gestor de Cenas (Menu, Combate, Chat, etc.)
│   │   └── ui/             # Componentes de interface (Botões, Textos, Barras)
│   ├── model/              # Regras de negócio e domínio do RPG (Player, Monsters, Itens, Classes)
│   ├── main.py             # Ponto de entrada da aplicação
│   └── constants.py        # Variáveis e configurações globais
├── build_windows.sh        # Script de compilação/empacotamento para Windows
└── requirements.txt        # Dependências do projeto

```

## 🚀 Como Executar Localmente

### Pré-requisitos

1. Ter o **Python 3.10 ou superior** instalado.
2. Uma chave de API válida para o modelo de linguagem (ex: OpenAI API Key).

### Instalação

1. Clone este repositório:

```bash
git clone https://github.com/pedrohmeireles2001/grass.git
cd grass

```

2. Crie e ative um ambiente virtual (recomendado):

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

```

3. Instale as dependências listadas no ficheiro `requirements.txt`:

```bash
pip install -r requirements.txt

```

### Configuração da API Key

O jogo necessita de uma variável de ambiente configurada para autenticar os pedidos à IA. Defina a sua chave antes de iniciar o jogo:

**No Windows (PowerShell):**

```powershell
$env:debug_api_key="SUA_CHAVE_API_AQUI"

```

**No Linux/macOS:**

```bash
export debug_api_key="SUA_CHAVE_API_AQUI"

```

*(Nota: Pode também adicionar a chave diretamente num ficheiro `.env` caso tenha implementado o `python-dotenv` no código, ou atualizar o ficheiro `options.json` de acordo com a lógica do seu motor de configurações).*

### Iniciar o Jogo

Com as dependências instaladas e a chave configurada, execute o script principal:

```bash
python src/main.py

```

## 🎮 Contribuição e Expansão

Sendo o código modular, é fácil adicionar novos conteúdos:

* Adicione novos monstros em `src/model/monster.py`.
* Crie novas raças ou classes explorando `src/model/race.py` e `classes.py`.
* Expanda os utilitários de interface dentro de `src/engine/ui/`.
