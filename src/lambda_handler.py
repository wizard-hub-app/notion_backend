from src.handler.weibo_handler import WeiboHandler
import json
from loguru import logger
from src.utils.log.custom_logger import set_logger

def lambda_handler(event, context):
    set_logger()
    logger.debug("event")

    body = json.loads(event["body"])
    
    
    try:
        url = body.get("url")
        if not url:
            logger.error("url is empty")
        weibo_handler = WeiboHandler(url)
        weibo_handler.run()
        return {
            "statusCode": 200,
            "body": "success",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
        }
    except Exception as e:
        logger.exception(e)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"error: {e}"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
        }
        
if __name__ == "__main__":
    lambda_handler({"body": '{"url": "http://m.weibo.cn/status/4983816600683065?"}'}, None)