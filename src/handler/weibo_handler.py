from bs4 import BeautifulSoup
from notion_client import Client


import requests
import re
import json


from src.utils.error.weibo_error import *
from src.handler.base_handler import BaseHandler

from loguru import logger


class WeiboHandler(BaseHandler):
    
    def __init__(self, url: str):
        super().__init__(url)
        self.prompt = f"""
            I will show you a Weibo, but it is shown as a html element. 
            Your task is parsing the full content of the weibo and then
            giving me summary and a title of the Weibo
            
            
            If there is a ## tag in the conent, ignore the tag
            e.g. #用户称地震时7部苹果手机均无预警# 
            
            If there are links in the content, show me the actual links as list too.
            The rule for actual link:
            fake link:`https://weibo.cn/sinaurl?u=https%3A%2F%2Fgithub.com%2Falesaccoia%2FVoiceStreamAI` 
            actual link: `https://github.com/Falesaccoia/VoiceStreamAI`
            
            Ignore the link start with https://m.weibo.cn/search?containerid= 
            
            The explaination for each key in the json: 
            - title: you summary from the content with Chinese
            - summary: you summary from the content with Chinese
            - content: render the result to MarkDown format with the origin language
        """

    def convert_url(self, url):
        # Check if the url is already in the desired format
        if re.match(r'http://m\.weibo\.cn/status/[A-Za-z0-9]+\?', url):
            return url
        # Check if the url is in the second format and convert it if it is
        elif re.match(r'https://weibo\.com/\d+/[A-Za-z0-9]+', url):
            id = re.search(r'([A-Za-z0-9]+)$', url).group()
            return 'http://m.weibo.cn/status/' + id + '?'
        # If the url is in neither format, raise an error
        else:
            logger.error(f"convert target url error", uuid=self._uuid)
            raise FormatError('wrong format')

    def download_weibo(self) -> dict:
        logger.debug("request weibo", extra={"uuid": "request_weibo"}, uuid=self._uuid)
        weibo_url = self.convert_url(self.baseUrl)
        try:
            response = requests.get(weibo_url)
        except Exception as e:
            logger.error(f"request weibo error: {e}", uuid=self._uuid)
            raise RequestWeiBoError(e)

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            post_text = soup.find_all('script')
            post = post_text[2].string
            match = re.search(r'var \$render_data = (\[{.*?}\])', post, re.DOTALL)
            js_object_str = match.group(1)
            js_object = json.loads(js_object_str)
            return js_object[0]
        except Exception as e:
            raise ParseWeiboError(e)

    def check_retweet(self, raw: dict):
        retweet = raw.get(f"{raw} \n retweeted_status")
        if not retweet:
            logger.debug("is not retweet", uuid=self._uuid)
            return raw, False
        logger.debug(f"{raw} \n is retweet", uuid=self._uuid)
        return retweet, True

    def check_long_text(self, raw: dict):

        isLongText = raw.get("isLongText")
        if not isLongText:
            return raw.get("text") 
        return raw.get("longText",{}).get("longTextContent")
    
    def download(self) -> dict:
        logger.debug("start download", uuid=self._uuid)
        raw = self.download_weibo()
        logger.debug("end download", uuid=self._uuid)
        return raw
    
    def parse(self, raw: dict) -> dict:
        status, is_retweet = self.check_retweet(raw.get('status',{}))
        if is_retweet:
            text = self.check_long_text(status)
        else:
            text = status.get("text")
        
        user = status.get("user",{})
        user_id = user.get("id")
        profile_url = user.get('profile_url')
        screen_name = user.get("screen_name")

        return {
            "text": text,
            "user_id": user_id,
            "profile_url": profile_url,
            "screen_name": screen_name
        } 
