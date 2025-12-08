import os
import openai

# Set your API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_activity_description(activity_name, activity_type=None):
    prompt = f"Write a short, engaging description of the outdoor activity '{activity_name}'."
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Description unavailable: {str(e)}"
