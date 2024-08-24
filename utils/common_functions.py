from datetime import datetime
from aiogram.types import (
    Message, ContentType, InputMediaPhoto, InputMediaVideo,
    InputMediaDocument, InputMediaAnimation, InputMediaAudio)
import pytz

async def get_id(message_text: str):
    return message_text.split('\n')[:-1]


def is_file_typed(message: Message):
    message.html_text
    if message.content_type in [ContentType.DOCUMENT, ContentType.AUDIO]:
        return True
    return False


def input_media_by_type(media: Message):
    if media.content_type == ContentType.PHOTO:
        return InputMediaPhoto
    if media.content_type == ContentType.VIDEO:
        return InputMediaVideo
    if media.content_type == ContentType.DOCUMENT:
        return InputMediaDocument
    if media.content_type == ContentType.ANIMATION:
        return InputMediaAnimation
    if media.content_type == ContentType.AUDIO:
        return InputMediaAudio


def get_media_file(media: Message):
    if media.content_type == ContentType.PHOTO:
        return media.photo[-1].file_id
    if media.content_type == ContentType.VIDEO:
        return media.video.file_id
    if media.content_type == ContentType.DOCUMENT:
        return media.document.file_id
    if media.content_type == ContentType.ANIMATION:
        return media.animation.file_id
    if media.content_type == ContentType.AUDIO:
        return media.audio.file_id



def get_caption(message: Message):
    caption = message.parse_entities(message.caption) if message.caption is not None else str()
    id = message.from_user.full_name
    # if message.from_user.username != None:
    #     id = f'@{message.from_user.username}'
    # else:
    #     id = f'<a href="{message.from_user.url}">{message.from_user.first_name}</a>'
    return f'{caption}\n\n<b>{id}</b>'


def convert_date(date_str, format: str = '%m-%d-%Y %I:%M %p'): # Default format is for SWIFTELD format
    date = datetime.strptime(date_str, format)
    return date.strftime('%d-%b %H:%M')


def split_message(message):
    max_length = 4094
    lines = message.split("\n")
    result = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 <= max_length:
            current += line + "\n"
        else:
            result.append(current)
            current = line + "\n"
    result.append(current)
    return result


async def binarySearch(lists, x):
    low = 0
    high = len(lists) - 1
    while low <= high:
        mid = (high + low) // 2
        if lists[mid] < x:
            low = mid + 1
        elif lists[mid] > x:
            high = mid - 1
        else:
            return mid
    return -1


async def get_current_time(time_in_utc = None, timezone: str = 'US/Eastern'):
    if time_in_utc:
        time_in_utc = datetime.strptime(time_in_utc, '%Y-%m-%d %H:%M:%S')
    else: # equals to if time_in_utc = None
        time_in_utc = datetime.utcnow()
    timezone = pytz.timezone(timezone)
    current_time = time_in_utc.replace(tzinfo=pytz.utc).astimezone(timezone)
    return datetime.strftime(current_time, '%m-%d-%Y %H:%M:%S')


async def get_converted_date(date_string):
    format = "%m-%d-%Y %H:%M:%S"
    return datetime.strptime(date_string, format)
