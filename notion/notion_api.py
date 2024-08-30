import requests
from dotenv import load_dotenv
import os

import json

class NotionAPI:
    # --------------------------------------------------------------------------------------
    def __init__(self):
        load_dotenv()
        self.base_url = "https://api.notion.com/v1/"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_CREDENTIALS')}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    # --------------------------------------------------------------------------------------
    # USERS
    # --------------------------------------------------------------------------------------
    def get_user_id(self):
        url = f"{self.base_url}users"
        
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            users = response.json()
            for user in users['results']:
                print(f"Nome: {user['name']}, ID: {user['id']}")
        else:
            print(f"Erro: {response.status_code} - {response.text}")        

        return users

    # --------------------------------------------------------------------------------------
    # DATABASES
    # --------------------------------------------------------------------------------------
    def retrieve_database(self, database_id):
        has_more = True
        next_cursor = None
        all_results = []
        url = f"{self.base_url}databases/{database_id}/query"
        
        while has_more:
            json_data = {"start_cursor": next_cursor} if next_cursor else {}
            response = requests.post(url, headers=self.headers, json=json_data)
            if response.status_code != 200:
                raise Exception(f"Erro ao buscar dados: {response.status_code}\n{response.text}")
            data = response.json()
            all_results.extend(data["results"])
            has_more = data["has_more"]
            next_cursor = data.get("next_cursor")

        return all_results

    # --------------------------------------------------------------------------------------
    def update_database(self, database_id, json_data):
        url = f"{self.base_url}databases/{database_id}"
        response = requests.patch(url, headers=self.headers, json=json_data)
        return response.status_code, response.json()

    # --------------------------------------------------------------------------------------
    def create_database(self, json_data):
        url = f"{self.base_url}databases/"
        response = requests.post(url, headers=self.headers, json=json_data)
        return response.status_code, response.json()

    # --------------------------------------------------------------------------------------
    # PAGES
    # --------------------------------------------------------------------------------------
    def retrieve_page(self, page_id):
        url = f"{self.base_url}pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Erro ao buscar página: {response.status_code}\n{response.text}")
        all_results = []
        data = response.json()
        try:
            all_results.extend(data["results"])
        except:
            all_results.append(data)

        return all_results

    # --------------------------------------------------------------------------------------
    def delete_page(self, page_id):
        url = f"{self.base_url}pages/{page_id}"
        json_data = {"archived": True}
        response = requests.patch(url, headers=self.headers, json=json_data)
        return response.status_code, response.text

    # --------------------------------------------------------------------------------------
    def update_page(self, page_id, json_data):
        url = f"{self.base_url}pages/{page_id}"
        response = requests.patch(url, headers=self.headers, json=json_data)
        # return response.status_code, response.text
        if response.status_code != 200:
            print(response.json())
            print(json_data)
        return response.status_code, response.json()

    # --------------------------------------------------------------------------------------
    def create_page(self, json_data):
        url = f"{self.base_url}pages/"
        response = requests.post(url, headers=self.headers, json=json_data)
        # print(response.status_code, response.json())
        if response.status_code != 200:
            print(response.json())
            print(json_data)
        return response.status_code, response.json()

    # --------------------------------------------------------------------------------------
    def find_page_title(self, page_id, title):
        url = f"{self.base_url}blocks/{page_id}/children"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            blocks = response.json().get("results", [])
            for block in blocks:
                if block.get("type") == "child_page":
                    if title.lower() in block.get("child_page", {}).get("title", "").lower():
                        return True, block
            return False, None
        else:
            return False, None
    
    # --------------------------------------------------------------------------------------
    # COMMENTS
    # --------------------------------------------------------------------------------------
    def retrieve_comment(self, block_id):
        url = f"{self.base_url}comments?block_id={block_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Erro ao buscar comentários na página: {response.status_code}\n{response.text}")
        all_results = []
        data = response.json()
        all_results.extend(data["results"])

        return all_results
    
    # --------------------------------------------------------------------------------------
    def create_comment(self, json_data):
        url = f"{self.base_url}comments/"
        response = requests.post(url, headers=self.headers, json=json_data)
        if response.status_code != 200:
            raise Exception(f"Erro ao criar comentário na página: {response.status_code}\n{response.text}")

        return response.status_code, response.json()

    # --------------------------------------------------------------------------------------
    # BLOCKS
    # --------------------------------------------------------------------------------------
    def retrieve_block_children(self, block_id):
        all_results = []
        response = requests.get(f"{self.base_url}blocks/{block_id}/children", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            all_results.extend(data["results"])
        else:
            print(f"Erro ao recuperar os blocos: {response.status_code}\n{response.text}")

        return all_results

    # --------------------------------------------------------------------------------------
    def append_block_children(self, block_id, json_data):
        response = requests.patch(f"{self.base_url}blocks/{block_id}/children", headers=self.headers, json=json_data)
        return response.status_code, response.json()

# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    database_tasks = os.getenv('DATABASE_TASKS')
    database_users = os.getenv('DATABASE_USERS')
    notion_api = NotionAPI()
    # response = notion_api.retrieve_database(database_tasks)
    # response = notion_api.retrieve_comment(database_tasks)
    response = notion_api.get_user_id()
    print(json.dumps(response, indent=4, sort_keys=True, ensure_ascii=False))