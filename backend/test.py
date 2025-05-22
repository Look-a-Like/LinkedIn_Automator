import google.generativeai as genai

# Configure the API with your API key
genai.configure(api_key='AIzaSyAfAZy6iQYSoTnUNegAfIGY2ZekI5K3x20')  # Replace 'YOUR_API_KEY' with your actual key

# List all available models
models = genai.list_models()

# Print model names and supported methods
for model in models:
    print(f"Model Name: {model.name}")
    print(f"Supported Methods: {model.supported_generation_methods}")
    print("---")