
import os
import json
from openai import OpenAI


class Translator:
    def __init__(self, api_key=None):
        # self.client = OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1/solar")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.openai.com/v1")

    # def translate_text(self, text, model="solar-1-mini-translate-enko", chunk_size=1600):
    def translate_text(self, text, model="gpt-3.5-turbo", chunk_size=1600):
        # Split the text into chunks, making sure not to split in the middle of a sentence
        import re
        
        # Split text into chunks, trying to avoid splitting sentences
        def split_text(text, chunk_size):
            sentences = re.split(r'(?<=[.!?]) +', text)
            chunks, current_chunk = [], ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    chunks.append(current_chunk)
                    current_chunk = sentence
            if current_chunk:
                chunks.append(current_chunk)
            return chunks

        chunks = split_text(text, chunk_size)
        translated_text = ""

        for chunk in chunks:
            stream = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are to translate everything to English."},
                    {"role": "user", "content": chunk}
                ],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    translated_text += chunk.choices[0].delta.content

        return translated_text


    # def translate_and_save(self, input_file, output_file):
    #     with open(input_file, 'r', encoding='utf-8') as file:
    #         data = json.load(file)

    #     translated_data = {}
    #     for key, text in data.items():
    #         print(f"Translating {key}...")
    #         translated_text = self.translate_text(text)
    #         print(translated_text)
    #         translated_data[key] = translated_text

    #     with open(output_file, 'w', encoding='utf-8') as file:
    #         json.dump(translated_data, file, ensure_ascii=False, indent=4)

    #     return output_file
    def translate_and_save(self, input_file, output_file):
    
        def translate_nested(obj):
            if isinstance(obj, dict):
                return {k: translate_nested(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [translate_nested(item) for item in obj]
            elif isinstance(obj, str):
                print(f"Translating: {obj}")
                translated = self.translate_text(obj)
                print(translated)
                return translated
            else:
                return obj

        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        translated_data = translate_nested(data)

        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(translated_data, file, ensure_ascii=False, indent=4)

        return output_file


        