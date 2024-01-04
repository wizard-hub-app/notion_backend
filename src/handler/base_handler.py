from notion_client import Client
from openai import OpenAI

import json
import os

from loguru import logger


class BaseHandler:
    
    def __init__(self, url: str):
        self._uuid=""
        self.baseUrl = url
        self.notion = Client(auth=os.environ["NOTION_TOKEN"])
        self.openai_client = OpenAI()
        self.prompt = ""
    
    def download(self) -> dict:
        pass
    
    def parse(self, raw: dict) -> dict:
        pass
        
    def set_uuid(self, uuid: str):
        self._uuid = uuid 
    
    def query_gpt(self, blog: str):
        custom_format = """{title: title, summary: summary, content: content, links: links}"""
        logger.debug("start query GPT", uuid=self._uuid)
        prompt = f"{self.prompt} \n Output the result as json format:{custom_format}"
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": blog},
            ],
            response_format={"type": "json_object"}
            )

        result = response.choices[0].message.content
        dic_result = json.loads(result)
        return dic_result
    
    def update_to_notion(self, origin_data: dict, dic_result: dict):
        logger.debug("start update notion", uuid=self._uuid)
        
        title = dic_result.get("title")
        summary = dic_result.get("summary")
        links = dic_result.get("links")

        screen_name = origin_data.get("screen_name")
        profile_url = origin_data.get("profile_url")
        
        create_page = self.notion.pages.create(
            **{
                "parent": { "database_id": "fbf06abf278947e89f0514515d6f911f" },
                "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "description": {
                    "rich_text": [
                        {
                            "text": {
                                "content": summary
                            }
                        }
                    ]
                },
                "Github link": {
                    "rich_text": [{'type': 'text',
            'text': {'content': link + '\n',
                'link': {'url': link}}} for link in links]
                } if links else {'content': ""},
                "Refer": {
                    "url": self.baseUrl
                },
                "Author":{
                    "rich_text":[
                        {
                            "type": 'text',
                            "text": {
                                "content": screen_name,
                                "link":{
                                    "url": profile_url
                                }
                            }
                        }
                    ]
                }
            },
            }
        )
        page_id = create_page.get("id")
        logger.debug(page_id, uuid=self._uuid)
        return page_id
    
    def set_origin_content(self, page_id: str, content: str):
        logger.debug("Update Page", uuid=self._uuid)
        self.notion.blocks.children.append(**{
            "block_id": page_id,
            "children": [
                {
                    "paragraph": {
                    "rich_text": [
                        {
                        "text": {
                            "content": content,
                        }
                        }
                    ]
                    }
                }
            ]
        })
        
    def run(self):
        try:
            raw = self.download()

            parsed_data = self.parse(raw)

            gpt_answer = self.query_gpt(parsed_data.get("text"))
            
            page_id = self.update_to_notion(parsed_data, gpt_answer)
            self.set_origin_content(page_id, gpt_answer.get("content"))
        except Exception as e:
            logger.error(f"{e}", uuid=self._uuid)
            raise e