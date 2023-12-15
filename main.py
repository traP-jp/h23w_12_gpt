from openai import OpenAI
import time
import re
import json
import requests

def generate_recipe_and_image(client, cooking_name):
    PROMPT = """
    ###見本
        "cooking_name": "レオナルド・ダ・ウィンチ",
        "comment": ["この名前から連想されるのは、芸術性とイタリアの伝統的な味わいです。そこで、イタリアンスタイルの豪華な料理を想像しましょう。この料理は、鮮やかな色合いとモダンな味わいが特徴です。見た目にも華やかで、特別な日にぴったりの一品になるでしょう。"],
        "material": [
            "ニンニク 2片（みじん切り）",
            "新鮮なバジル 10枚",
            "プロシュート 100g（薄切り）",
            "モッツァレラチーズ 150g（スライス）",
            "ミニトマト 200g（半分に切る）",
            "ペンネパスタ 200g"]
        "seasoning":[
            "オリーブオイル 大さじ2",
            "白ワイン 100ml",
            "塩 適量",
            "黒こしょう 適量",
            "パルメザンチーズ 適量（削り）"
        ],
        "way_of_making": [
            "パスタを塩を入れたお湯でアルデンテに茹でる。",
            "フライパンにオリーブオイルを熱し、ニンニクを炒める。",
            "プロシュートを加えてさっと炒め、ミニトマトも加えて炒める。",
            "白ワインを注ぎ、少し煮詰める。",
            "茹で上がったパスタをフライパンに加え、全体をよく混ぜる。",
            "モッツァレラチーズとバジルを加え、塩と黒こしょうで味を調える。",
            "皿に盛り付け、パルメザンチーズを上から削って完成。"
        ]
        "Detailed Description": [
            "A dish inspired by Leonardo da Vinci, featuring a plate of penne pasta mixed with sautéed prosciutto, mini tomatoes, and fresh basil. Topped with slices of mozzarella cheese and a sprinkle of Parmesan, garnished elegantly on a ceramic plate. The setting is artistic and sophisticated, embodying the essence of Italian cuisine with a modern twist."
            ]
        
    "cooking_name": " ",
    "comment": [その料理の由来,雰囲気],
    "material": [ ],
    "seasoning": [ ],
    "way_of_making": [ ]
    "Detailed Description": [Only this part should be written in English.
1.Identify Detailed Visual Elements: I think of specific visual elements that will make the generated image concrete and original. For example, in the case of a dish, I imagine the ingredients, colors, shapes, and style of presentation in detail.
2.Setting the Scene: The background or context of the image is also important. I create an overall image of the scene, like what kind of plate the dish is on, what the surrounding atmosphere is like, etc.
3.Artistic and Creative Expression: To enhance the uniqueness and artistry of the image, I sometimes incorporate creative elements or distinctive styles.
4.Color Palette: Mentioning specific colors (like deep blues, purples, and shimmering silvers) could help convey the cosmic theme more vividly.]
    ###見本を参考にして与えた料理二人前のレシピを書いてjson形式で出力して
    {text}
    """.strip()

    MAX_RETRIES = 3

    def query_openai(prompt):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                print("\nTHINKING...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",###gpt-4-1106-previewgpt-3.5-turbo-1106
                    messages=[{"role": "user", "content": prompt}]
                )
                return response
            except OpenAI.error.RateLimitError:
                print(f"RateLimitError encountered. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                RETRY_DELAY *= 2
                retries += 1
            except Exception as e:
                print(e)
            break
        else:
            print("Failed to get a response after multiple retries.")
            return None

    formatted_prompt = PROMPT.format(text=cooking_name)
    
    response = query_openai(formatted_prompt)
    
    print(response)


    if response:
        json_part = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
        extracted_json = json_part.group() if json_part else "No JSON format found"

        match = re.search(r'"Detailed Description": \[([^\]]*)\]', response.choices[0].message.content)
        if match:
            detailed_description = match.group(1).strip().strip('"')
        else:
            detailed_description = "No detailed description found."

        image_response = client.images.generate(
            model="dall-e-3",
            prompt="Draw a complete dish on one plate.{}".format(detailed_description),
            size="1024x1024",
            quality="standard",
            n=1,
            style="vivid"
        )

        image_url = image_response.data[0].url if image_response else "No image generated"
        return extracted_json, image_url
    else:
        return "Failed to generate recipe", "No image generated"
    
client = OpenAI(api_key='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')


def save_json_to_file(json_data, file_name):
    try:
        data = json.loads(json_data)
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"File saved successfully as {file_name}")
        return file_name
    except json.JSONDecodeError:
        print("Failed to decode JSON data.")
    except Exception as e:
        print(f"An error occurred: {e}")

def update_json_with_image_url(file_name, image_url):
    try:
        with open(file_name, 'r+', encoding='utf-8') as file:
            data = json.load(file)
            data["Image URL"] = image_url
            file.seek(0)
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.truncate()
        print(f"Image URL added successfully to {file_name}")
    except Exception as e:
        print(f"An error occurred while updating the file: {e}")

def download_and_save_image(image_url, file_name):
    try:
        # 画像をダウンロード
        response = requests.get(image_url)
        response.raise_for_status()

        base_file_name = file_name.rsplit('.', 1)[0]

        image_file_name = f"{base_file_name}.jpg"

        with open(image_file_name, 'wb') as file:
            file.write(response.content)

        print(f"Image saved successfully as {image_file_name}")
    except requests.RequestException as e:
        print(f"An error occurred while downloading the image: {e}")


def download_and_save_image(image_url, file_name):
    try:
        # 画像をダウンロード
        response = requests.get(image_url)
        response.raise_for_status()

        base_file_name = file_name.rsplit('.', 1)[0]

        image_file_name = f"{base_file_name}.jpg"

        with open(image_file_name, 'wb') as file:
            file.write(response.content)

        print(f"Image saved successfully as {image_file_name}")
    except requests.RequestException as e:
        print(f"An error occurred while downloading the image: {e}")

# 使用例
recipe_name = ""
recipe_json, image_url = generate_recipe_and_image(client, recipe_name)

saved_file_name = save_json_to_file(recipe_json, "recipe10.json")

update_json_with_image_url(saved_file_name, image_url)

download_and_save_image(image_url, saved_file_name)
