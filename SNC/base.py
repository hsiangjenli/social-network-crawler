from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Union
from datetime import datetime

class Discussion(BaseModel):
    title: str
    datetime: datetime
    link: HttpUrl
    article_id: str
    content: str
    comments: List[Union[str, int, float]]

    @field_validator('datetime', mode='before')
    def parse_datetime(cls, v):
        try:
            return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Incorrect datetime format, should be YYYY-MM-DD HH:MM:SS")

    @field_validator('comments', mode='before')
    def validate_each_comment(cls, v):
        if v in [None, '', []]:
            raise ValueError("Comment cannot be empty")
        return v


if __name__ == '__main__':

    # Correct Input Data
    article = Discussion(
        title="1 Hello World",
        datetime="2021-01-01 00:00:00",
        link="https://example.com",
        article_id="123456",
        content="This is a test article",
        comments=["Comment 1", "Comment 2", "Comment 3"]
    )
    print(article)

    # Incorrect Input Data
    article = Discussion(
        title="2 Hello World",
        datetime="11111111111",
        link="https://example.com",
        article_id="123456",
        content="This is a test article",
        comments=["Comment 1", "Comment 2", 3]
    )
    print(article)