import pandas as pd
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain  
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.memory import ConversationBufferMemory
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain

data=pd.read_csv('D:\Project\Survey_Bot\User_result\sample_test.csv')

masking=(data['답변']==1)
yes_data=data[masking]['질문사항'].to_list()
yes_data

loader = PyPDFLoader("https://www.kihasa.re.kr/hswr/assets/pdf/1037/journal-37-2-525.pdf")
pages = loader.load_and_split()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
splits = text_splitter.split_documents(pages)
vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings(openai_api_key='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'))

llm = ChatOpenAI(openai_api_key='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', model="gpt-4")  # Use GPT-4
retriever = vectorstore.as_retriever()


prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            "너는 암 전문의 챗봇이야. 설문 조사 응답내용을 분석하고 알려줘"
        ),
        # variable_name이 memory와 연결하는 key입니다.
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
conversation = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)

qa = ConversationalRetrievalChain.from_llm(llm, retriever=retriever, memory=memory)
qa('설문조사 결과:'+''.join(yes_data)+'이 사람은 암에 저항할 의지가 있는거야?')