from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import time
import argparse
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from image_generator import add_images_to_script, get_place_img
from scripts.old_script import ScriptGenerator, Translator
from scripts.translator import Translator as TranslatorV2
from scripts.main import generate_scripts, combine_txt_to_json, OUTPUT_DIR
from utils import extract_photo_reference, read_file


parser = argparse.ArgumentParser(description='Backend Server Deployment')
parser.add_argument('-a', '--server_address', type=str, default='127.0.0.1' ,help='Server address')
parser.add_argument('-p', '--server_port', type=int, default=5000 ,help='Server port')
args = parser.parse_args()


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [f"http://10.168.105.128:{args.server_port}", "*"]}})

load_dotenv()
Settings.llm=OpenAI(model='gpt-3.5-turbo', temperature=0.0)
Settings.embed_model=OpenAIEmbedding(model='text-embedding-3-small')

# FIREBASE_CRED_FILE = "google-services.json"
FIREBASE_CRED_FILE = "jejom-d5d61-firebase-adminsdk-hxhng-6f02508a1f.json"
cred = credentials.Certificate(FIREBASE_CRED_FILE)
firebase_admin.initialize_app(cred)
db = firestore.client()


from pipelinev2 import PipelineV2
pipeline = PipelineV2(
    embed_model_size         = 1536, # text-embedding-3-small
    accomodations_sim_top_k  = 500,
    restaurants_sim_top_k    = 500,
    tourist_spots_sim_top_k  = 500,
    accomodations_vec_db_uri = os.path.join('locations', 'descriptions_vector_store', 'hotels.db'),
    restaurants_vec_db_uri   = os.path.join('locations', 'descriptions_vector_store', 'restaurants.db'),
    tourist_spots_vec_db_uri = os.path.join('locations', 'descriptions_vector_store', 'tourist_spots.db'),
    accomodations_json       = os.path.join('locations', 'detailed', 'hotels_detailed.json'),
    restaurants_json         = os.path.join('locations', 'detailed', 'restaurants_detailed.json'),
    tourist_spots_json       = os.path.join('locations', 'detailed', 'tourist_spots_detailed.json'),
    firestore_db             = db,
    firestore_db_path        = 'script_restaurant'
)

@app.route('/')
def home():
    return 'Hello World'


@app.route('/check_init_input', methods=['POST'])
def check_init_input():
    query = request.form.get('query')
    print("check_init_input: ", query)
    check_result_dict = pipeline.check_query_detail(query=str(query))
    return jsonify(check_result_dict)


@app.route('/generate_trip', methods=['POST'])
def generate_trip():
    user_query = request.form.get('query')
    user_properties = request.form.get('user_props')
    mode = request.form.get('mode')  # test
    
    print("generate_trip: ", user_query, user_properties)
    print(str(mode).lower().strip())
    
    if "test" in str(mode).lower().strip():
        with open('sample_usages/generate_trip.json', 'r') as file:
            trip_dict = json.load(file)
            trip_dict = trip_dict["data"]
    else:
        start_time = time.time()
        trip_dict = pipeline.generate_trip(
            end_user_specs=str(user_properties), 
            end_user_query=str(user_query)
        )
        trip_dict['thumbnail'] = get_place_img(trip_dict['title'])
        print(f"[Generate Trip took {time.time() - start_time} secs]")
    flattened_trip_dict = extract_photo_reference(trip_dict)
    return jsonify({'data': flattened_trip_dict})


@app.route('/generate_script_legacy', methods=['POST'])
def generate_script_legacy():
    try:
        start_time = time.time()
        # Get the JSON data from the request
        
        # test mode
        mode = request.form.get('mode')  # test
        
        if "test" not in str(mode).lower().strip():
            # Extract the required fields from the JSON body
            characters_num = request.form.get('characters_num')
            cafe_name = request.form.get('cafe_name')
            cafe_environment = request.form.get('cafe_environment')

            # check for missing fields
            if not characters_num or not cafe_name or not cafe_environment:
                return jsonify({"error": "Missing required fields"}), 400

            # init script generator
            script_generator = ScriptGenerator(
                characters_num=characters_num,
                cafe_name=cafe_name,
                cafe_environment=cafe_environment
            )

            # run tasks and generate script
            output_json_path, cafe_name = script_generator.run_tasks()


            input_directory = "output_folder"
            input_file_path = os.path.join(input_directory, "script.json")
            output_file_path = os.path.join(input_directory, "translated_output.json")

            # translation
            translator = Translator()
            translator.translate_and_save(input_file_path, output_file_path)
            print(f"[Generate Script took {time.time() - start_time} secs]")

            return jsonify({
                "eng_script": add_images_to_script(read_file(output_json_path, "json")),
                "cn_script": add_images_to_script(read_file(output_file_path, "json")),
            })

        else:
            return jsonify({
                "eng_script": read_file("sample_usages/script.json", "json"),
                "cn_script": read_file("sample_usages/translated_output.json", "json"),
            })
    except Exception as e:
        return jsonify({"error": f"Error generating script: {e}"})


@app.route('/generate_script', methods=['POST'])
def generate_script():
    try:
        start_time = time.time()
        # Get the JSON data from the request
        
        # test mode
        mode = request.form.get('mode')  # test
        
        if "test" not in str(mode).lower().strip():
            # Extract the required fields from the JSON body
            characters_num = request.form.get('characters_num')
            cafe_name = request.form.get('cafe_name')
            cafe_environment = request.form.get('cafe_environment')

            # check for missing fields
            if not characters_num or not cafe_name or not cafe_environment:
                return jsonify({"error": "Missing required fields"}), 400

            # init script generator
            generate_scripts(f"为咖啡馆：{cafe_name}（环境：{cafe_environment}）生成一个包含 {characters_num} 个角色的剧本", characters_num)
            mandarin_json_path=combine_txt_to_json(OUTPUT_DIR)
            translator = TranslatorV2()
            english_json_path = os.path.join(OUTPUT_DIR, "english_script.json")
            translator.translate_and_save(input_file=mandarin_json_path, output_file=english_json_path)

            print(f"[Generate Script took {time.time() - start_time} secs]")

            return jsonify({
                "eng_script": add_images_to_script(read_file(english_json_path, "json")),
                "cn_script": add_images_to_script(read_file(mandarin_json_path, "json")),
            })

        else:
            return jsonify({
                "eng_script": read_file("sample_usages/english_script.json", "json"),
                "cn_script": read_file("sample_usages/mandarin_script.json", "json"),
            })
    except Exception as e:
        return jsonify({"error": f"Error generating script: {e}"})



if __name__ == '__main__':
    app.run(debug=True, host=args.server_address, use_reloader=False)
    # app.run(debug=True, host='0.0.0.0', use_reloader=False)
