import csv
import ast

input_file = "train.csv"
output_file = "processed.csv"

def map_urgency(urgency):
    mapping = {
        "Emergency": "Экстренное",
        "Urgent": "Срочное",
        "Routine": "Плановое",
        "Consultation": "Консультационное"
    }
    return mapping.get(urgency, "Консультационное")

def map_type(output):
    urgency = output.get("urgency_level")

    if urgency == "Emergency":
        return "Вызов врача"
    elif urgency == "Urgent":
        return "Консультация или вопрос"
    elif urgency == "Routine":
        return "Запись на прием"
    else:
        return "Наблюдение"

with open(input_file, newline='', encoding='utf-8') as f_in, \
     open(output_file, 'w', newline='', encoding='utf-8') as f_out:

    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)

    for row in reader:
        input_data = ast.literal_eval(row['input'])
        output_data = ast.literal_eval(row['output'])

        text = input_data.get("symptom_description", "")
        urgency = map_urgency(output_data.get("urgency_level"))
        req_type = map_type(output_data)

        writer.writerow([text, urgency, req_type])