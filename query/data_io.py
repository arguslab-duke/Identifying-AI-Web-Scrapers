import csv
def output_data(data, filename):
    flat_data = []

    for i in data:
        flat_data.append(i["query"])
        flat_data.append(i["response"])
        flat_data.append(i["time"])

    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        print(flat_data)
        writer.writerow(flat_data)

def get_prompts(filename):
    output = []
    with open(filename, 'r') as file:
        for line in file:
            current_query = line.strip()
            print(current_query)
            output.append(current_query)
    return output