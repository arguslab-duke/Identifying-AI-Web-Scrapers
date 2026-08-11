import csv
from openai import OpenAI
import os
from datetime import datetime
import data_io
import time
import sys

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_openai(prompt, model="gpt-4o-mini"):
    try:
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search"}],
            input=prompt,
            max_output_tokens=500
        )
        return response.output_text
    except Exception as e:
        return f"ERROR: {str(e)}"

def process_csv(input_csv, output_csv, model="gpt-4o-mini"):
    results = []
    with open(input_csv, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        if 'query' not in reader.fieldnames:
            raise ValueError("Input CSV needs column 'query'")
        for row in reader:
            query = row['query']
            answer = ask_openai(query, model=model)
            results.append({'query': query, 'answer': answer, 'query_time': datetime.now()})

    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=['query', 'answer', 'query_time'])
        writer.writeheader()
        writer.writerows(results)

def query(query_list):
    data = [
        {"query": queries, "response": "null", "time": "null"}
        for queries in query_list
    ]
    for idx, current_query in enumerate(data):
        question = current_query["query"]

        response = ask_openai(question)
        data[idx]["response"] = response
        data[idx]["time"] = time.time()

    return data


if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    prompts = data_io.get_prompts(input_file)
    results = query(prompts)
    data_io.output_data(results, output_file)
