#!/usr/bin/env python
try:
    import json
    import time
    from datetime import datetime
    from threading import Thread
    import requests
    from common import get_logger
    from telegram import Bot, ParseMode
except ImportError as e:
    print(f'Error occured during import: {e}')
    print('Please install all necessary libraries and try again')
    exit(1)


class UnsplashClient():
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            try:
                configs = json.load(f)
            except json.decoder.JSONDecodeError as e:
                print(f"Failed to parse configs: {e}")
                exit(1)
            except FileNotFoundError as e:
                print(f"Failed to open the file: {e}")
                exit(1)
        self._from_config_dict(configs)
    def _from_config_dict(self, config_dict):
        self._configs = config_dict
        self._logger = get_logger(
                logger_name="UNSPLASH", 
                file_name=f'logs/unsplash_{datetime.today().date()}.log',
                )
        self.requests_left = self._configs['request_limit']
        self._logger.info("Unsplash client created")

    def _make_request_return_response(self, request_url, *, resp_type='json'):
        """
        Given request_url, make a request and return json response if resp_type
        is 'json' or plain text otherwise

        Arguemnts:
            request_url: the url to request
            resp_type: in which format to return the response: json or text

        Returns:
            result: json or plain text response
        """
        # Check if we still have available resources to API
        #if self.requests_left <= 0:
        #    self._logger.warning("Request limit reached")
        #    raise RuntimeError("Requests limit reached, please wait an hour")
        # The above method is not good because once the limit reaches 0, 
        #it will never make new requests to get a new value
        # Make the request
        self._logger.info(f"Making a request to: {request_url}")
        try:
            resp = requests.get(request_url)
        except Exception as e:
            self._logger.error(f'Error occured during the response')
            raise RuntimeError("Error occured during the response")
        # Update the limitation count
        self.requests_left = int(resp.headers['X-Ratelimit-Remaining'])
        print(resp.text)
        if resp.ok:
            if resp_type == 'json':
                result = json.loads(resp.text)
            else:
                result = resp
        else:
            raise RuntimeError(f"Response not okay: {resp.status_code}, {resp.text}")
        self._logger.info("All done, returning response")
        return result
    
    def _get_n_random_images(self, n=3):
        """
        Get n random images from unsplash API.
        In this case even if n=1, the result is a list.
        Arguments:
            n: number of images to request, default: 30, max: 30
        Return:
            response: a list of n random images
        """
        # Maximum is 30
        n = max(1, min(n, 30));
        # Create the request URL
        self._logger.info("Creating request url")
        request_url = self._configs['base_url'] + '/photos/random/'
        request_url += f"?client_id={self._configs['access_key']}"
        request_url += f"&count={n}"
        # Make the request and process the response
        self._logger.info("Request url ready")
        try:
            images = self._make_request_return_response(request_url)
        except RuntimeError as e:
            self._logger.exception("Error occured during the request")
            raise e
        self._logger.info(f"Received {len(images)} images from API.")
        return images
    

class UnsplashThread(Thread):
    def __init__(
            self,
            unsplash_client: UnsplashClient,
            bot: Bot,
            chat_id: int,
            num_of_images: int):

        super().__init__()
        self._unsplash_client = unsplash_client
        self._bot = bot
        self._chat_id = chat_id
        self._num_of_images = num_of_images

    def run(self):
        try:
            self._images = self._unsplash_client._get_n_random_images(self._num_of_images)
        except RuntimeError:
            self._bot.send_message(
                    chat_id=self._chat_id,
                    text="Unfortunately the limit to Unsplash API has been exhausted :/\
                            \nPlease come back in about an hour or so.",
                            )
            return
  
        for img in self._images:
            reply_text = self.create_reply(img)
            self._bot.send_message(
                    chat_id=self._chat_id,
                    text=reply_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False)
            time.sleep(1.4)

    def create_reply(self, img):
        if img["description"] is not None:
            description = img["description"]
        elif img["alt_description"] is not None:
            description = img["alt_description"]

        num_views = img['views']
        num_of_likes = img['likes']
        num_of_downloads = img['downloads']
        user_name = img['user']['name']
        user_url = img['user']['links']['html']

        preview_url = img['urls']['regular']
        url = img['links']['html']
        download_link = img['urls']['full']

        reply_text = ""
        reply_text += f'<a href="{preview_url}">&#8205</a>'
        reply_text += f'An <a href="{url}"><b>amazing photo</b></a> '

        if description is not None:
            reply_text += f'called <i>"{description}"</i> '

        reply_text += f'from <a href="{user_url}"><b>{user_name}</></a>.'
        reply_text += f'\nIt was liked by <b>{num_of_likes}</b> users,'
        reply_text += f' downloaded <b>{num_of_downloads}</b> times'
        reply_text += f' and viewed <b>{num_views}</b> times.'
        reply_text += f' <a href="{download_link}">Click to download</a>.'

        return reply_text
