from collections import OrderedDict
import os
import json
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import ast
from scripts.jubensha_script import ScriptGenerator
from scripts.translator import Translator



OUTPUT_DIR = "scripts/outputs/jubensha"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def generate_scripts(user_prompt, characters_num=3):
    script_generator = ScriptGenerator(user_prompt, characters_num)
    script_generator.run_tasks()

    
    # Step 1: Load character file
    character = []
    with open(os.path.join(OUTPUT_DIR, "Character Designer.txt"), 'r') as f: 
        character_file = f.read()
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

    script_generator.run_host_handbook_tasks()

    # Convert the string to a list
    try:
        character_list = ast.literal_eval(response)
        print(f"Character names are: {character_list}")
        
        # Run handbook tasks for each character
        for character_name in character_list:
            script_generator.run_character_handbook_tasks(character_name)
            
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing character names: {e}")
        print(f"Raw response was: {response}")

    return None



# def combine_txt_to_json(output_dir):
#     """
#     Combine all .txt files in the directory into a single JSON file.
    
#     Args:
#         output_dir (str): Path to the directory containing .txt files
#     """
#     combined_data = {}
    
#     # Create the output JSON file path
#     json_file = os.path.join(output_dir, "mandarin_script.json")

    
    
#     # Iterate through all files in the directory
#     for filename in os.listdir(output_dir):
#         if filename.endswith(".txt"):
#             file_path = os.path.join(output_dir, filename)
            
#             # Read the content of each .txt file
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     content = f.read()
                
#                 # Use the filename (without extension) as the key
#                 key = os.path.splitext(filename)[0]
#                 combined_data[key] = content
                
#             except Exception as e:
#                 print(f"Error reading {filename}: {str(e)}")
    
#     # Write the combined data to a JSON file
#     try:
#         with open(json_file, 'w', encoding='utf-8') as f:
#             json.dump(combined_data, f, ensure_ascii=False, indent=2)
#         print(f"Successfully created {json_file}")

#         return json_file
#     except Exception as e:
#         print(f"Error writing JSON file: {str(e)}")

def combine_txt_to_json(output_dir):
    """
    Combine all .txt files in the directory into a single JSON file.
    
    Args:
        output_dir (str): Path to the directory containing .txt files
    """
    characters_data = {}
    host_data = {}
    misc_data = {}

    json_file = os.path.join(output_dir, "mandarin_script.json")

    for filename in os.listdir(output_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(output_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                name = os.path.splitext(filename)[0]

                # Host files
                if "host" in filename.lower():
                    host_data[name] = content

                # Character files (format: <character>_act_<part>.txt)
                elif "_act_" in name:
                    try:
                        name_part, act_part = name.split('_act_')
                        act_key = f"act_{act_part}"

                        if name_part not in characters_data:
                            characters_data[name_part] = {}
                        characters_data[name_part][act_key] = content
                    except ValueError:
                        misc_data[name] = content  # fallback if format isn't clean
                else:
                    misc_data[name] = content

            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")

    final_data = {
        # "characters": [
        #     {"name": name, **acts} for name, acts in characters_data.items()
        # ],
        # "characters": [
        #     {
        #         "name": name,
        #         **{k: acts[k] for k in sorted(acts, key=lambda x: int(x.split('_')[1]))}
        #     }
        #     for name, acts in characters_data.items()
        # ],
        "characters": [
            OrderedDict(
                [("name", name)] +
                sorted(acts.items(), key=lambda x: int(x[0].split('_')[1]))
            )
            for name, acts in characters_data.items()
        ],
        "host": host_data,
        **misc_data
    }

    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully created {json_file}")
        return json_file
    except Exception as e:
        print(f" Error writing JSON: {e}")

    


if __name__ == "__main__":
    generate_scripts('生成一个包含3个角色的剧本。', 3)
    mandarin_json_path=combine_txt_to_json(OUTPUT_DIR)
    # mandarin_json_path='scripts/outputs/jubensha_1/combined_output.json'
    translator = Translator()
    english_json_path = os.path.join(OUTPUT_DIR, "english_script.json")
    translator_json_path = translator.translate_and_save(input_file=mandarin_json_path, output_file=english_json_path)


