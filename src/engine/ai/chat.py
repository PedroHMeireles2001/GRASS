import threading
from typing import Dict, Any

from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory

from src.constants import DEBUG
from src.engine.ai.tools import PlayerToolkit
import queue
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# Callback para capturar os tokens e jogar na Fila
class TokenQueueHandler(BaseCallbackHandler):
    def __init__(self, token_queue):
        self.token_queue = token_queue

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        # Envia o token de texto normal
        self.token_queue.put(token)

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        # Quando o agente decide usar uma ferramenta, enviamos um aviso formatado
        tool_name = serialized.get('name')
        # Você pode formatar isso como quiser, talvez entre colchetes ou itálico
        if DEBUG:
            self.token_queue.put(f"\n*[Sistema: Executando {tool_name}...]*\n")

class Chat:
    def __init__(self, api_key, system_prompt, initial_message, game):
        self.game = game
        self.player_toolkit = PlayerToolkit(game)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Note que removemos o callback fixo aqui para injetá-lo dinamicamente no submit,
        # mas mantivemos streaming=True
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=1,
            api_key=api_key,
            streaming=True
        )

        initial_history = ChatMessageHistory(
            messages=[
                HumanMessage(f"Player\n{self.game.player.to_markdown() if self.game.player else 'Default'}"),
                AIMessage(initial_message)
            ]
        )

        memory = ConversationBufferMemory(
            chat_memory=initial_history,
            memory_key="chat_history",
            return_messages=True
        )

        agent = create_openai_tools_agent(llm, self.player_toolkit.get_tools(), prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.player_toolkit.get_tools(),
            memory=memory,
            verbose=True
        )

    def submit(self, text):
        token_queue = queue.Queue()
        stream_handler = TokenQueueHandler(token_queue)

        def run_agent():
            try:
                run_config = RunnableConfig(
                    callbacks=[stream_handler]
                )
                self.agent_executor.invoke(
                    {"input": text},
                    config=run_config
                )
            except Exception as e:
                print(f"Erro na thread do agente: {e}")
                token_queue.put(f"\n[Erro: {str(e)}]")
            finally:
                token_queue.put(None)

        thread = threading.Thread(target=run_agent)
        thread.start()

        while True:
            token = token_queue.get()
            if token is None:
                break
            yield token

        thread.join()
