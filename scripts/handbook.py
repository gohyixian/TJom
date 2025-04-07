from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOpenAI

# Step 1: Load all generated text
text_files = [
    "scripts/outputs/jubensha/background_setting.txt",
    "scripts/outputs/jubensha/character.txt",
    "scripts/outputs/jubensha/character_event_log.txt",
    "scripts/outputs/jubensha/player_instructions.txt",
    "scripts/outputs/jubensha/player_clues.txt",
    "scripts/outputs/jubensha/title.txt",
    "scripts/outputs/jubensha/time_taken.txt"
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

# Step 4: Define the sections to be generated
sections = [
    "游戏简介",
    "角色介绍与分配建议",
    "游戏流程与时间安排",
    "每轮讨论的建议指引",
    "如何发放线索",
    "投票与结局说明",
    "主持小贴士"
]

# Initialize the content for the handbook
handbook = {}

# Generate each section one by one
for section in sections:
    prompt = f"""
    你是一名主持人，需要组织一场沉浸式角色扮演推理游戏。请根据参考资料，生成以下内容：
    
    {section}
    
    请用中文撰写，语言专业，格式清晰，适合主持人直接使用。
    """
    
    # Running the QA chain with the section-specific prompt
    response = qa_chain.run(prompt)
    
    # Store the generated section
    handbook[section] = response

# Step 5: Write the complete handbook to a text file
with open("host_instructions_handbook.txt", "w", encoding="utf-8") as f:
    for section, content in handbook.items():
        f.write(f"{section}:\n{content}\n\n")
        
print("Handbook has been saved to 'host_instructions_handbook.txt'")
