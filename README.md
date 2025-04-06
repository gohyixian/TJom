# Running the backend with Docker
1. Build Docker image
    ```bash
    cd to this directory
    docker build --no-cache -t taiwan-jom-app .
    ```
2. Create a new container based on built image and run. If you wish to directly start the inferencing server, run:
    ```bash
    docker run -it --rm -p 5000:5000 taiwan-jom-app /bin/bash -c "python server.py -a 0.0.0.0 -p 5000"
    ```

</br>

# Pushing the built image to DockerHub
```bash
docker login

docker tag taiwan-jom-app yixian02/taiwan-jom-app:python-3.10-slim

docker push yixian02/taiwan-jom-app:python-3.10-slim
```
Verify your push <a href='https://hub.docker.com/u/yixian02'>here</a>.

</br>

# Pulling and Running the built image from DockerHub
```bash
docker pull yixian02/taiwan-jom-app:python-3.10-slim

docker run -it --rm -p 5000:5000 yixian02/taiwan-jom-app:python-3.10-slim /bin/bash -c "python server.py -a 0.0.0.0 -p 5000"
```

<br/>

## API Keys
Create a file named <code>.env</code> at the same directory level as this <code>README.md</code>, and define the below:
- <code>OPENAI_API_KEY = "<a href='https://platform.openai.com/api-keys'>get_your_upstage_api_key_here</a>"</code>
- <code>SERPAPI_API_KEY = "<a href='https://serpapi.com/integrations/python'>get_your_serp_api_key_here</a>"</code>
- <code>PEXELS_API_KEY = "<a href='https://www.pexels.com/api/'>get_your_pexel_api_key_here</a>"</code>
- <code>GOOGLE_MAPS_API_KEY = "<a href='https://console.cloud.google.com/google/maps-apis/credentials?invt=AbuCaw&project=tough-volt-335906'>get_your_google_maps_api_key_here</a>"</code>


## Firebase Credentials
Place the firebase credential <code>json</code> file at the same directory level as this <code>README.md</code> file.
- <a href='https://drive.google.com/file/d/1Cc_XER8t4uXXumXbkow6Z0Y92F5SbWUs/view?usp=sharing'>jejom-d5d61-firebase-adminsdk-hxhng-6f02508a1f.json</a>

<br/>

## Python: Conda ENV Setup
- <code>conda env create -n tjom-llama --file environment.yml</code>



<br/>

## Running the Backend
- <code>conda activate tjom-llama</code>
- <code>python server.py</code>


<br/>


## Setting Up the Knowledge Base
We have run the scripts necessary to create the knowledge base where the pipeline retrieves information about the amazing tourist sites, cafes, restaurants and hotels in Taiwan. The knowledge base is created by scraping locations from Taiwan using the Google Places API. If you wish to update the knowledge base to include more of the latest locations available, the steps are simple! You may follow the below:

1. Scraping locations from the Places API. Go to the <a href='https://console.cloud.google.com/google/maps-apis/quotas?project=tough-volt-335906'>Places API Console</a>, create your project and obtain your Google Maps API key. Place the API key in <code>build_locations_collection.py</code> or <code>.env</code>. Inside the code, make sure that all three <code>REFRESH_GMAPS</code>, <code>FILTER_RAW</code> and <code>GET_DETAILED</code> are set to <code>True</code>. Then run the below:
    - <code>python build_locations_collection.py</code>

<br/>

2. Indexing the filtered locations. In <code>build_locations_index.py</code>, set all three <code>GENERATE_DESC</code>, <code>GENERATE_SUITABLE_TIMES</code>, <code>GENERATE_VECTOR_INDEX</code>, and <code>TEST_VECTOR_INDEX</code> to <code>True</code>. Then run the below:
    - <code>python build_locations_index.py</code>

<br/>

Both these script will take quite some time to run as the first one involves scraping the Places API, filtering the data and further scraping the details about the filtered locations, and the second script will utilise an LLM and an Embedding Model to Index the refined locations. However, please note that although they are time-consuming processes, they are not resource intensive. The first script will ustilize barely 0.5% of your free Google Cloud Project quota and the second script will consume only about USD 0.50 worth of credits for the OpenAI <code>gpt-3.5-turbo</code> LLM and <code>text-embedding-3-small</code> Embedding Model.
