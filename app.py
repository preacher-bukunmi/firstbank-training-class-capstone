from dash import Dash, html, dcc, callback, Output, Input, State
import requests
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import time

app = Dash(__name__)

def generate_images_from_prompt(prompt, num_images=2):
    image_urls = []
    loading_times = []

    for _ in range(num_images):
        try:
            # Record start time
            start_time = time.time()

            # Get Azure OpenAI Service settings
            load_dotenv()
            api_base = os.getenv("AZURE_OAI_ENDPOINT")
            api_key = os.getenv("AZURE_OAI_KEY")
            api_version = '2023-06-01-preview'

            # Make the initial call to start the job
            url = "{}openai/images/generations:submit?api-version={}".format(api_base, api_version)
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            body = {
                "prompt": prompt,
                "n": 1,
                "size": "512x512"
            }
            submission = requests.post(url, headers=headers, json=body)

            # Get the operation-location URL for the callback
            operation_location = submission.headers['Operation-Location']

            # Poll the callback URL until the job has succeeded
            status = ""
            while (status != "succeeded"):
                time.sleep(3)  # wait 3 seconds to avoid rate limit
                response = requests.get(operation_location, headers=headers)
                status = response.json()['status']

            # Get the results
            image_url = response.json()['result']['data'][0]['url']
            image_urls.append(image_url)

            # Record end time
            end_time = time.time()

            # Calculate loading time
            loading_time = end_time - start_time
            loading_times.append(loading_time)

        except Exception as ex:
            print(ex)

    # Return the URLs for the generated images and loading times
    return image_urls, loading_times

def generate_prompt(value):
    load_dotenv()
    azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
    azure_oai_key = os.getenv("AZURE_OAI_KEY")
    azure_oai_model = os.getenv("AZURE_OAI_MODEL")

    client = AzureOpenAI(
        azure_endpoint=azure_oai_endpoint,
        api_key=azure_oai_key,
        api_version="2023-05-15"
    )

    response = client.chat.completions.create(
        model=azure_oai_model,
        temperature=0.2,
        max_tokens=120,
        messages=[
            {"role": "system", "content": "You give exact responses with a maximum of two outputs."},
            {"role": "user", "content": value}
        ]
    )

    prompt = response.choices[0].message.content

    image_urls, loading_times = generate_images_from_prompt(prompt, num_images=2)

    return image_urls, loading_times, prompt

# ... (existing imports)

app = Dash(__name__)

# ... (existing functions)

app.layout = html.Div([
    html.Div(style={'background-color': 'grey', 'background-image': 'url(assets/images/backround.jpg)',
                    'background-repeat': 'no-repeat', 'background-size': 'cover', 'background-position': 'center',
                    'textAlign': 'center', 'width': '100%', 'height': '100vh', 'margin': '0', 'backgroundColor': 'none',
                    'padding': '0px', 'position': 'fixed'}, children=[
        html.H1(children='The Acers Image Generating App', style={'color': '#126DBD', 'fontSize': 40}),
        dcc.Input(
            id="basic-prompt-input",
            type="text",
            placeholder="Create any image of your choice using just your Imagination",
            size="60",
            style={'width': '50%', 'padding': '10px', 'margin': 'auto', 'display': 'block', 'border-radius': '20px'}
        ),
        html.Button('Generate Image',
                    id='submit-button',
                    n_clicks=0,
                    style={'background-color': '#126DBD', 'color': 'white', 'padding': '10px 20px', 'border': 'none',
                           'cursor': 'pointer', 'margin': '10px auto', 'display': 'block', 'border-radius': '12px'}
                    ),

        dcc.Loading(
            id="loading-container",
            type="default",
            children=[
                html.Div(id='image-generation-output', children=[
                    html.P(id='generated-prompt'),
                    html.Img(id="generated-image1", style={'width': '20%', 'margin': '10px 30px 10px 0'}),
                    html.Img(id="generated-image2", style={'width': '20%', 'margin': '10px 30px 10px 0'}),
                    html.P(id='loading-time-output')
                ]),
            ]
        )
    ])
],
    style={'width': '100%', 'margin': '0!important', 'overflowX': 'hidden', 'overflowY': 'hidden'}, )


@callback(
    [Output('generated-image1', 'src'),
     Output('generated-image2', 'src'),
     Output('loading-time-output', 'children'),
     Output('generated-prompt', 'children')],
    Input('submit-button', 'n_clicks'),
    State('basic-prompt-input', 'value'),
    prevent_initial_call=True
)
def generate_images(n_clicks, value):
    image_urls, loading_times, prompt = generate_prompt(value)

    # Display loading times, generated prompt, and images on the HTML page
    loading_time_texts = [f"Image {i + 1} loaded in {loading_time:.2f} seconds " for i, loading_time in
                          enumerate(loading_times)]

    return image_urls[0], image_urls[1], loading_time_texts, f"Generated Prompts: {prompt}"


if __name__ == '__main__':
    app.run(debug=True, port=6744)