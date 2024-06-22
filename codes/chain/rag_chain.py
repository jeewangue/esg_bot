# Configuring
from data_handler.utils.image_base64_utils import ImageBase64Utils
from data_handler.lc_docstore_handler.in_memory_docstore_handler import InMemoryDocstoreHandler
from data_handler.lc_retrieverHandler.retriever_handler import RetrieverHandler
from data_handler.lc_vectorstore_handler.pinecone_vectorstore_handler import PineconeVectorstoreHandler

from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv
import pandas as pd
import os

# Load the .env file
load_dotenv()

report_data_dir = "./data/reports/"
report_name = "report.pdf"
file_list_df = pd.read_csv("./data/reports.csv")

target = "LG에너지솔루션"#SK텔레콤"
row = file_list_df[file_list_df.company_name == target].iloc[0]

company_name = row["company_name"]
year = row["year"]
url = f"{os.getenv('logblack_url')}{company_name}_{year}.pdf"


# TODO, LANG SMITH?
class RAGChain():
    def invoke(self, query):
        self.chain.invoke(query)


class ESGReportRAGChain(RAGChain):
    def __init__(self):
        self.vectorstore_handler = PineconeVectorstoreHandler(
            company_name=company_name, year=year, embeddingModel='text-embedding-3-large'
            ).getStore()
        self.docstore_handler = InMemoryDocstoreHandler()
        self.docstore_handler.load_from_file(report_data_dir+company_name+str(year)+"/store_data.json")
        self.lc_docstore = self.docstore_handler.getStore()j
        self.lc_retriever = RetrieverHandler(self.vectorstore_handler, self.lc_docstore)

        # 멀티모달 LLM
        model = ChatOpenAI(temperature=0, model="gpt-4o", max_tokens=2048)

        # RAG 파이프라인
        self.chain = (
            {
                "context": self.lc_retriever.retriever | RunnableLambda(ImageBase64Utils.split_image_text_types),
                "question": RunnablePassthrough(),
            }
            | RunnableLambda(self.img_prompt_func)
            | model
            | StrOutputParser()
        )

    def img_prompt_func(data_dict):
        """
        컨텍스트를 단일 문자열로 결합
        """
        formatted_texts = "\n".join(data_dict["context"]["texts"])
        messages = []
    
        # 이미지가 있으면 메시지에 추가
        if data_dict["context"]["images"]:
            for image in data_dict["context"]["images"]:
                image_message = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                }
                messages.append(image_message)
    
        # 분석을 위한 텍스트 추가
        text_message = {
            "type": "text",
            "text": (
                "You are financial analyst tasking with providing investment advice.\n"
                "You will be given a mixed of text, tables, and image(s) usually of charts or graphs.\n"
                "Use this information to provide investment advice related to the user question. Answer in Korean. Do NOT translate company names.\n"
                f"User-provided question: {data_dict['question']}\n\n"
                "Text and / or tables:\n"
                f"{formatted_texts}"
            ),
        }
        messages.append(text_message)
        return [HumanMessage(content=messages)]



#ret = chain_multimodal_rag.invoke("이사회 내에서 기후변화 및 탄소중립 안건을 보고하거나 결의하였는가?")