import csv
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='en', target='ru')

with open('processed.csv', 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    rows = list(reader)

translated_rows = []
for i, row in enumerate(rows):
    if len(row) >= 3:
        try:
            translated_text = translator.translate(row[0])
            translated_rows.append([translated_text, row[1], row[2]])
            print(f"Переведена строка {i+1}")
        except Exception as e:
            print(f"Ошибка перевода строки {i+1}: {e}")
            translated_rows.append(row)
    else:
        translated_rows.append(row)

with open('processed_ru.csv', 'w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerows(translated_rows)

print("Перевод завершен. Файл processed_ru.csv создан.")