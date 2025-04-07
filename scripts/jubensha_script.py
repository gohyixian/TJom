from collections import OrderedDict
import os
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import PDFSearchTool
from openai import OpenAI
import gradio as gr
import re
import json
from fpdf import FPDF
from docx import Document
import gradio as gr
from docx.shared import Pt
from langchain_huggingface import HuggingFaceEmbeddings
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

OUTPUT_DIR = "scripts/outputs/jubensha"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class ScriptGenerator:
    def __init__(self, user_prompt,characters_num):
        self.user_prompt = user_prompt
        self.character_name = ''  # Initialize as empty string
        self.characters_num=characters_num
        self.llm = ChatOpenAI(model='gpt-3.5-turbo')
        self.rag_tool = PDFSearchTool(
            pdf='scripts/RAG/RAG.pdf',
            config=dict(
                llm=dict(
                    provider="openai",
                    config=dict(
                        model="gpt-3.5-turbo",
                    ),
                ),
                embedder=dict(
                    provider="huggingface",
                    config=dict(
                        model="BAAI/bge-small-en-v1.5",
                    ),
                ),
            )
        )

        # Initialize all agents
        self.script_planner = Agent(
            role="剧本策划",
            goal=f"设计一个复杂且引人入胜的角色剧情，灵感来源于台湾的神话、传说、文化和历史，提升玩家的挑战性和沉浸感。设计根据 {self.user_prompt}",
            backstory="""你是一位经验丰富的故事讲述者，擅长描绘人性和戏剧冲突。你擅长构建引人入胜、剧情紧凑的故事，让玩家沉浸其中。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        self.titler = Agent(
            role="标题设计师",
            goal="为剧本杀游戏设计一个标题",
            backstory="你是一位经验丰富的故事讲述者，擅长提炼故事精髓，为其命名。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        self.timer = Agent(
            role="时长编写者",
            goal="编写该剧本杀游戏的时长。",
            backstory="你是一位经验丰富的故事讲述者，善于为剧本制定合理的游戏时间。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.character_designer = Agent(
            role="角色设计师",
            goal="为每个角色创建独特而详细的背景故事、动机和秘密，让角色更加鲜活。",
            backstory="你是角色设计专家，擅长打造复杂且可信的角色形象，为故事注入灵魂。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.script_writer_agent = Agent(
            role="剧本编剧",
            goal="为每位角色撰写完整的剧本，讲述其人生经历以及导致案件发生的事件。",
            backstory="你是一名剧作家，对角色在谋杀剧本中的作用有深刻理解。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.player_writer_agent = Agent(
            role="玩家扮演指引者",
            goal="为每个角色创建详细且具有代入感的角色扮演说明，涵盖五轮讨论的具体指引。",
            backstory="你曾是一名著名剧作家，擅长创作悬疑剧与角色张力，后来投身于数字剧本杀创作，将叙事技巧用于构建沉浸式角色扮演体验。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.clue_generator = Agent(
            role="线索设计师",
            goal="设计具有挑战性和误导性的线索，引导玩家一步步破解谜题。",
            backstory="你是一位谜题爱好者，擅长设计复杂且具有迷惑性的线索，增加游戏难度与趣味性。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.character_handbook_character = Agent(
            role="沉浸式剧本杀角色剧本编写者",
            goal="为玩家设计一个具有丰富背景、深刻情感动机和复杂人际关系的角色剧本，推动剧情发展。每个角色的剧本需要通过多个'幕'来构建，展现角色的成长、冲突与转折，使其与其他角色互动并影响整体故事走向。",
            backstory="你是一名经验丰富的剧本杀编剧，专注于为每个玩家设计独特且富有沉浸感的角色剧本。你的任务是为每个玩家创造一个立体、深刻且充满情感冲突的角色，通过剧本中的每一幕展示角色的背景、动机、情感波动以及与其他角色的关系。每个角色的故事需要有足够的张力和转折，以便玩家能够通过角色的互动推动剧情，最终面临关键的选择或结局。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # Initialize tasks that don't depend on character_name
        self.background_setting_task = Task(
            description=f"设定谋杀剧本的背景设定，灵感来源于台湾岛的传说、神话、历史与文化。故事不一定要发生在台湾岛，但必须体现其文化氛围。故事围绕四位关键角色展开，每位角色都与这些文化历史元素有所联系。设计根据 {self.user_prompt}",
            expected_output="一段详细的背景故事，包括案件发生场景、案件经过、关键事件描述，内容需受到台湾岛文化历史的启发。所有内容必须为中文。",
            agent=self.script_planner,
            output_file=os.path.join(OUTPUT_DIR, "Script Planner.txt")
        )

        self.character_creation_task = Task(
            description="为每一位角色创建完整的角色档案，包括背景故事、动机、秘密以及与其他角色之间的关系。确保每个角色都具备独特个性和立体形象。",
            expected_output="所有角色的完整档案，包括背景、动机、秘密和人际关系。所有内容必须为中文。",
            agent=self.character_designer,
            output_file=os.path.join(OUTPUT_DIR, "Character Designer.txt")
        )

        self.script_writing_task = Task(
            description=f"""为所有{self.characters_num}位角色分别撰写完整的案发前四天事件记录。包括具体日期、关键事件、角色内心想法、计划、互动等内容，体现角色的动机与行为逻辑。每篇记录需完整，不能留有未完句式，结尾需包含总结或反思性陈述。""",
            expected_output=f"每位{self.characters_num}角色一份完整的四天事件记录，总共份。所有内容必须为中文。",
            agent=self.script_writer_agent,
            output_file=os.path.join(OUTPUT_DIR, "Script Writer.txt")
        )

        self.player_writing_instruction_task = Task(
            description="""剧本中将进行五轮讨论。第一轮为角色自我介绍和案件初步讨论；第二轮用于收集其他玩家提供的线索；第三轮开放性讨论；第四轮再次收集线索；第五轮投票选出凶手。为每一位角色创建针对这五轮的详细扮演说明。请以角色名称作为标题，按轮次列出该角色在每轮应扮演的行为与思考方式，不要泄露凶手身份。每位角色的说明需集中在一起，格式清晰有序，内容应贴合角色性格与故事背景。""",
            expected_output="每位角色的五轮扮演指引，包含角色名作为标题，并列出五轮详细内容，具有个性化特色。所有内容必须为中文。",
            agent=self.player_writer_agent,
            output_file=os.path.join(OUTPUT_DIR, "Player Instruction Writer.txt")
        )

        self.clue_design_task = Task(
            description="""为游戏设计总共4条线索。每位角色需拥有2条关键线索与2条误导性线索。线索应贴合剧情逻辑，并提升解谜体验。请以角色名称为标题，清晰标明关键线索与误导线索，并附上解释说明。""",
            expected_output="每位角色4条线索（2条关键线索+2条误导线索），附说明，并以角色名为标题分类。所有内容必须为中文。",
            agent=self.clue_generator,
            output_file=os.path.join(OUTPUT_DIR, "Clue Generator.txt")
        )

        self.title = Task(
            description="为生成的剧本命名。",
            expected_output="一个合适的剧本标题, 所有内容必须为中文。",
            agent=self.titler,
            output_file=os.path.join(OUTPUT_DIR, "Title.txt")
        )

        self.time = Task(
            description="编写游戏所需时长。",
            expected_output="直接输出时长，例如 '2-3小时'，无需完整句子。",
            agent=self.timer,
            output_file=os.path.join(OUTPUT_DIR, "Duration.txt")
        )
        # Add new agents
        self.host_guide_creator = Agent(
            role="主持人手册编写专家",
            goal="创建专业、完整的主持人指南，确保游戏流程顺畅",
            backstory="""你是一位经验丰富的剧本杀主持人，熟悉各种游戏流程和主持技巧。
            擅长编写清晰明确的主持指引，帮助其他主持人顺利开展游戏。""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # Add new tasks
        self.game_intro_task = Task(
            description="编写游戏简介，概述故事背景和基本设定",
            expected_output="""一段吸引人的游戏简介，包含：
            1. 故事发生的时代背景
            2. 主要矛盾冲突
            3. 游戏的基本设定
            4. 适合的玩家群体
            格式清晰，语言生动""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_intro.txt")
        )

        self.character_allocation_task = Task(
            description="编写角色介绍与分配建议",
            expected_output="""包含：
            1. 所有角色的简要介绍(不剧透关键信息)
            2. 每个角色适合的玩家性格类型
            3. 角色分配的建议策略
            4. 特殊角色注意事项""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_character_allocation.txt")
        )

        self.game_flow_task = Task(
            description="设计游戏流程与时间安排",
            expected_output="""详细的游戏流程表，包含：
            1. 各阶段时间分配(如自我介绍30分钟等)
            2. 每个环节的具体内容
            3. 可能的时间调整方案
            4. 关键时间节点提醒""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_flow.txt")
        )

        self.discussion_guide_task = Task(
            description="编写每轮讨论的建议指引",
            expected_output="""五轮讨论的详细指引：
            1. 每轮讨论的预期目标
            2. 主持人应引导的方向
            3. 可能出现的问题及应对方案
            4. 时间控制技巧""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_discussion.txt")
        )

        self.clue_distribution_task = Task(
            description="设计如何发放线索的方案",
            expected_output="""线索发放指南，包含：
            1. 线索发放的时机和顺序
            2. 不同线索的发放方式
            3. 如何控制信息揭露节奏
            4. 特殊线索的处理方法""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_clues.txt")
        )

        self.voting_guide_task = Task(
            description="编写投票与结局说明",
            expected_output="""投票环节指南，包含：
            1. 投票规则说明
            2. 如何引导玩家做出选择
            3. 不同结局的触发条件
            4. 结局揭晓的戏剧化呈现方式""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_voting.txt")
        )

        self.host_tips_task = Task(
            description="编写主持小贴士",
            expected_output="""实用主持技巧，包含：
            1. 氛围营造方法
            2. 玩家冲突处理
            3. 节奏控制技巧
            4. 应急情况处理
            5. 提升沉浸感的技巧""",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.host_guide_creator,
            output_file=os.path.join(OUTPUT_DIR, "host_guide_tips.txt")
        )

    

    def create_character_handbook_tasks(self):
        """Create the character handbook tasks now that we know the character name"""
        self.第一幕 = Task(
            description=f"设定{self.character_name}的登场与背景，揭示其内心深处的情感冲突和心理状态。详细描述角色的外部表现与内心的差距，例如他/她的表面冷静与内心的焦虑或隐藏的恐惧。此时，角色可能会知道一些与案件相关的线索，但这些线索还不完全明确，角色的判断和行动可能受到过去经历或潜在恐惧的影响。描述角色与其他关键人物的关系，特别是这些关系如何影响角色当前的情绪。此阶段应展现角色的目标、内心的秘密以及他/她对案件的态度——是冷静分析，还是掩藏某些真相。",
            expected_output=f"一段详细的剧情描述，展示{self.character_name}的登场，内外冲突的表现，以及与其他角色的复杂互动。通过细腻的心理描写展现角色的情感波动、动机及背景。",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.character_handbook_character,
            output_file=os.path.join(OUTPUT_DIR, f"{self.character_name}_act_1.txt")
        )

        self.第二幕 = Task(
            description=f"在这一幕中，{self.character_name}逐渐面对越来越严重的冲突，案件的复杂性开始显现。新线索的出现，尤其是与案件相关的关键情报，推动剧情走向高潮。角色开始意识到自己之前的判断可能是错误的，或许自己的行为也与案件有更深的联系。描述角色在此阶段的情感波动，是否选择主动揭示自己知道的线索，还是继续保持沉默。在这一过程中，{self.character_name}与其他人物的冲突愈发激烈，可能存在合作，也可能有对抗。角色的决定将极大影响剧情的走向——是维持现状，还是揭开隐藏的秘密？此时角色的心理变化尤为关键，是否暴露脆弱，还是继续伪装成冷静理智的外表？",
            expected_output=f"一段剧情激化的详细描述，展现{self.character_name}如何面对新的挑战，如何与他人产生冲突或合作，并推动故事发展。深入描写角色的心理挣扎与决策。",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.character_handbook_character,
            output_file=os.path.join(OUTPUT_DIR, f"{self.character_name}_act_2.txt")
        )

        self.第三幕 = Task(
            description=f"这一幕展示{self.character_name}如何逐渐揭开案件的真相，面对自己内心深处的恐惧或罪恶感。角色的情绪达到了高潮，可能会出现愤怒、悔恼、恐慌等多种情感交织的状态。此时，角色面临重大的心理抉择——是继续隐藏自己曾经的过错，还是勇敢地揭露所有的真相？在揭露过程中，{self.character_name}可能会与其他角色发生冲突，尤其是与他们的矛盾将进一步加剧。角色的转变非常关键，是否会做出悔改，还是继续执迷不悟？此时角色的情感波动应当被充分展现，尤其是在关键对抗时刻，展现角色的极限反应。",
            expected_output=f"一段情节高潮的详细描述，展现{self.character_name}如何面对真相，是否会选择揭露或隐瞒自己所知的线索，最终导致剧情转折。深入描写角色的情绪变化和心理转折。",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.character_handbook_character,
            output_file=os.path.join(OUTPUT_DIR, f"{self.character_name}_act_3.txt")
        )

        self.最终幕 = Task(
            description=f"结局部分，{self.character_name}面临最终的审判或重大决策，所有秘密和真相将彻底揭开。此时，角色必须做出关键的选择——是承认自己的罪行，接受惩罚，还是继续坚持自己的无辜身份，逃避责任？无论角色是被认定为凶手还是无辜者，这一选择将深刻影响他的命运。此时角色的情感和心理状态达到高潮，可能会充满悔恼、愤怒、解脱、恐惧等复杂情绪。结局应根据角色的选择和行为，展现他/她的内心世界的最终归宿，是否能够获得自我救赎，或者继续被过去的罪责与恐惧困扰。",
            expected_output=f"一段情感冲击力强的结局描述，展示{self.character_name}在面对审判时的心理波动，如何为自己辩解或承认罪行，及其最终的决策。根据角色的行为和选择，展现不同的结局。确保结局有强烈的情感张力，并反映出角色的内心转变。",
            context=[self.background_setting_task, self.character_creation_task,self.clue_design_task,self.player_writing_instruction_task,self.script_writing_task],
            agent=self.character_handbook_character,
            output_file=os.path.join(OUTPUT_DIR, f"{self.character_name}_act_4.txt")
        )

    def run_tasks(self):
        crew = Crew(
            agents=[self.script_planner, self.character_designer, self.script_writer_agent, 
                   self.clue_generator, self.player_writer_agent, self.titler, self.timer],
            tasks=[self.background_setting_task, self.character_creation_task, 
                  self.script_writing_task, self.clue_design_task, 
                  self.player_writing_instruction_task, self.title, self.time],
            verbose=True,
            process=Process.sequential
        )
        crew.kickoff()
    
    def run_host_handbook_tasks(self):
        host_crew = Crew(
            agents=[self.host_guide_creator],
            tasks=[
                self.game_intro_task,
                self.character_allocation_task,
                self.game_flow_task,
                self.discussion_guide_task,
                self.clue_distribution_task,
                self.voting_guide_task,
                self.host_tips_task
            ],
            verbose=True,
            process=Process.sequential
        )
        host_crew.kickoff()
    

    def run_character_handbook_tasks(self, character_name):
        self.character_name = character_name
        print(f"Running handbook tasks for character: {self.character_name}")
        
        # Now that we have the character name, create the tasks
        self.create_character_handbook_tasks()
        
        crew = Crew(
            agents=[self.character_handbook_character],
            tasks=[self.第一幕, self.第二幕, self.第三幕, self.最终幕],
            verbose=True,
            process=Process.sequential
        )
        crew.kickoff()


# def generate_scripts(characters_num, cafe_name, user_prompt):
#     script_generator = ScriptGenerator(characters_num, cafe_name, user_prompt)
#     script_generator.run_tasks()

    
#     # Step 1: Load character file
#     character = []
#     with open(os.path.join(OUTPUT_DIR, "background_setting.txt"), 'r') as f: 
#         character_file = f.read()
#         character.append(character_file)

#     # Initialize the LLM model with the correct version
#     llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

#     # Prepare the prompt template
#     prompt_template = PromptTemplate(
#         input_variables=["text"], 
#         template="Given the following text, extract the names of all characters:\n{text}. For example: ['Character Name 1', 'Character Name 2', 'Character Name 3']  "
#     )

#     # Initialize the chain
#     llm_chain = LLMChain(llm=llm, prompt=prompt_template)

#     # Run the chain with the text input
#     response = llm_chain.run(character)

#     script_generator.run_host_handbook_tasks()

#     # Convert the string to a list
#     try:
#         character_list = ast.literal_eval(response)
#         print(f"Character names are: {character_list}")
        
#         # Run handbook tasks for each character
#         for character_name in character_list:
#             script_generator.run_character_handbook_tasks(character_name)
            
#     except (ValueError, SyntaxError) as e:
#         print(f"Error parsing character names: {e}")
#         print(f"Raw response was: {response}")

#     return None


# if __name__ == "__main__":
#     generate_scripts(3, 'cafe_name', '生成一个包含3个角色的剧本。')