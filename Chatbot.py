import os
import sys
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, trim_messages
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str
    word_information: dict

class chatbot:
    def __init__(self):
        dotenv_path = resource_path(".env")
        load_dotenv(dotenv_path)
        self.__api_key = os.environ.get("OPENAI_API_KEY")
        if not self.__api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.model = ChatOpenAI(model="gpt-4o-mini")
        self.workflow = StateGraph(state_schema=State)
        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                ###Role:
                You talk like a teacher. Answer all questions to the best of your ability. 
                
                ###Instruction:
                You are the teacher in our dictionary, 
                this application aims to make users memorize vocabulary more easily by letting students practice, 
                and memorize tricks, examples and images related to the vocabulary(Association).                
                
                ###Constraint
                1.If the question related to this vocabulary, you should answer the question according the information provided and you should not use your own knowledge to answer about the question. 
                Here is the information of the vocabulary that the student searched : {word_information} 
                2.You should answer in {language}. 
                3.You should not answer the question that not related to the techniques or tricks to memorize the word, the checking grammar, 
                verifying the understanding about the vocabulary, giving examples to the vocabulary, """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.messages = []
        self.trimmer = trim_messages(
            max_tokens=2000,
            strategy="last",
            token_counter=self.model,
            include_system=True,
            allow_partial=False,
            start_on="human",
        )
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", self.call_model)
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)
        self.config = {"configurable": {"thread_id": "abc789"}}
        self.language = "English"

    def call_model(self, state):
        trimmed_messages = self.trimmer.invoke(state["messages"])
        prompt = self.prompt_template.invoke({"messages": trimmed_messages, "language": state["language"], "word_information": state['word_information']})
        response = self.model.invoke(prompt)
        return {"messages": [response]}

    def chat(self, query, word_information, chat_state): # chat_state: boolean (True: use this function for chat, False: use this function for tips)
        self.messages.append(HumanMessage(content=query))
        input_messages = self.messages + [HumanMessage(query)]
        
        if chat_state:
            full_response = ""

            # Use app.stream() to get partial chunks of AIMessage
            for chunk, metadata in self.app.stream(
                    {"messages": input_messages, "language": self.language, "word_information": word_information},
                    self.config,
                    stream_mode="messages",
                ):
                if isinstance(chunk, AIMessage):
                    # Accumulate partial response
                    full_response += chunk.content 
                    # Optionally, here you could update a UI text widget in real-time

            # After streaming completes, store the final AI message into the history
            self.messages.append(AIMessage(content=full_response))
            return full_response
        
        else:
            output = self.app.invoke({"messages": input_messages, "language": self.language, "word_information": word_information}, self.config)
            self.messages.append(AIMessage(content=output["messages"][-1].content))
            return output["messages"][-1].content

    def generate_notes(self, word_information):
        self.config = {"configurable": {"thread_id": "abc123"}}
        
        self.notes_prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """###Role: You talk like a teacher. The lesson was end now. 
                #Instruction: You need to generate a summary by the information retrieve from the chat history between the student and you.

                ###Objetive of the summary: 
                1. review the words that the students learn, such as the definitons and the examples. 
                2. Revise the wrong reason if the student was verify the grammar with you.
            
                ###Constraint:
                You should not answer the the definitons and the examples by your own knowledge,
                you should ansewe by the information provided, here are the definitons and the examples: {word_information}
                If student ask you the word that the information didn't provided, you should tell him to "use the dictionary above before you ask the question.
                If the student was verify the grammar, you should tell the reason why they got wrong in the notes.
                The language of the summary should write in {language}.
                
                
                Notes format: 
                Vocabulary you learnt: [vocab_1, vocab_2 etc]
                Techniques or tricks to memorise this word:
                Wrong place: It can be grammar, wrong use case and etc.
                Summary:
                """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        input_prompt = self.messages
        output = self.app.invoke({"messages": input_prompt, "language": self.language, "word_information": word_information}, self.config)
        return output["messages"][-1].content