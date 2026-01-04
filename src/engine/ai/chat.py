import random
import threading
from typing import Dict, Any
from uuid import UUID

import numpy as np
import pygame
from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.outputs import LLMResult

from src.constants import DEBUG
from src.engine.ai.tools import PlayerToolkit
import queue
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from src.utils import typewriter_sound


# Callback para capturar os tokens e jogar na Fila
class TokenQueueHandler(BaseCallbackHandler):
    def __init__(self, chat):
        self.chat = chat

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.chat.token_queue.put(token)

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        if DEBUG:
            tool_name = serialized.get('name')
            self.chat.token_queue.put(f"\n*[Sistema: Executando {tool_name}...]*\n")

class Chat:


    def __init__(self, gpt_model,api_key, system_prompt, initial_message, game):
        self.game = game
        self.player_toolkit = PlayerToolkit(game)
        self.token_queue = queue.Queue()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Note que removemos o callback fixo aqui para injetá-lo dinamicamente no submit,
        # mas mantivemos streaming=True
        llm = ChatOpenAI(
            model=gpt_model,
            temperature=1,
            api_key=api_key,
            streaming=True
        )

        initial_history = ChatMessageHistory(
            messages=[
                HumanMessage(f"Player\n{self.game.player.to_text() if self.game.player else 'Default'}"),
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

    def is_generating(self):
        return not self.token_queue.empty()

    def submit(self, text):
        if self.is_generating():
            return

        stream_handler = TokenQueueHandler(self)

        def run_agent():
            try:
                config = RunnableConfig(callbacks=[stream_handler])
                self.agent_executor.invoke({"input": text}, config=config)

            except Exception as e:
                self.token_queue.put(f"[Erro: {e}]")

        threading.Thread(target=run_agent, daemon=True).start()




