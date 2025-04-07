from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import ast
import os 


# Step 1: Load character file
text_file = "scripts/outputs/jubensha/character.txt"

character=[]
with open(text_file,'r') as f: 
    character_file=f.read()
    character.append(character_file)


# Initialize the LLM model with the correct version
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

# Prepare the prompt template
prompt_template = PromptTemplate(
    input_variables=["text"], 
    template="Given the following text, extract the names of all characters:\n{text}. For example: ['Character Name 1', 'Character Name 2', 'Character Name 3']  "
)

# Initialize the chain
llm_chain = LLMChain(llm=llm, prompt=prompt_template)

# Run the chain with the text input
response = llm_chain.run(character)

# Convert the string to a list
character_list = ast.literal_eval(response)

# Step 1: Load all generated text
text_files = [
    "scripts/outputs/jubensha/background_setting.txt",
    "scripts/outputs/jubensha/character.txt",
    "scripts/outputs/jubensha/character_event_log.txt",
    "scripts/outputs/jubensha/player_instructions.txt",
    "scripts/outputs/jubensha/player_clues.txt",
    "scripts/outputs/jubensha/title.txt",
    "scripts/outputs/jubensha/time_taken.txt",
    "scripts/outputs/host_instructions_handbook.txt"
]

documents = []
for file_path in text_files:
    with open(file_path, 'r') as f:
        content = f.read()
        documents.append(content)

# Step 2: Split and embed
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.create_documents(documents)

embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
db = FAISS.from_documents(docs, embedder)

retriever = db.as_retriever()

# Step 3: Setup the RetrievalQA Chain
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7),
    retriever=retriever,
    return_source_documents=False
)


sections = [
    "第一幕",
    "第二幕",
    "第三幕",
    "最终幕"
]


# Use a for loop generate character handbooks for all characters 
for character in character_list:
    # Initialize the content for the handbook
    handbook = {}

    # Generate each section one by one
    for section in sections:
        prompt = f"""
        你是一名专业的《剧本杀》编剧。请为一个沉浸式剧本杀游戏中的角色生成完整的角色剧本。

        剧本应具有完整的人物背景、情感动机、与他人的关系，并以“幕”作为结构，推动剧情发展和玩家互动。

        ##角色剧本格式##


        🧍‍♂️ 角色名称
        🎭 性格特点（例如：冲动、冷静、多疑、圆滑等）
        🧳 背景故事（角色的身份、经历、与案件或其他角色的过往纠葛等）

        然后，将剧本分为以下几幕：

        📖 第一幕：人物登场与关系建立
        - 角色当前的状态与心情
        - 他知道的信息
        - 与其他角色的关系与看法
        - 此阶段的目标和隐藏的秘密

        🕵️ 第二幕：剧情推进与矛盾激化
        - 得到的新线索或情报
        - 与其他人的冲突或合作
        - 行动计划或应对方式

        🎭 第三幕：真相浮现与角色转折
        - 真相的揭露或部分线索的拼凑
        - 情绪变化，关键对抗
        - 他选择揭露或隐瞒的信息

        🧩 最终幕：推理投票与命运结局
        - 最终表态与辩解

        请按照以上格式创作{character}的角色剧本的{section}
        
        请用中文撰写，语言专业，格式清晰，适合主持人直接使用。
        """
        
        # Running the QA chain with the section-specific prompt
        response = qa_chain.run(prompt)
        
        # Store the generated section
        handbook[section] = response
    
    # 构建目标文件夹路径
    output_dir = f"scripts/outputs/characters"
    os.makedirs(output_dir, exist_ok=True)  # 确保目录存在

    # 构建完整文件路径
    file_path = os.path.join(output_dir, f"{character}_handbook.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        for section, content in handbook.items():
            f.write(f"{section}:\n{content}\n\n")
    
    print(f"Handbook has been saved to 'outputs/characters/{character}_handbook.txt'")

    


        








