from pydantic import BaseModel
from typing import List
import pandas as pd
import os

class Book(BaseModel):
    id: str
    title: str
    author: str
    genre: str
    description: str

class User(BaseModel):
    id: str
    name: str 

class Rating(BaseModel):
    user_id: str
    book_id: str
    rating: float

class SyncData(BaseModel):
    books: List[Book]
    users: List[User]  
    ratings: List[Rating]

def write_books_csv(book_list):
    file_path = "dataset/book.csv"
    df_new = pd.DataFrame([{
        "BookID": b.id,
        "Title": b.title,
        "Author": b.author,
        "Genre": b.category,
        "Description": b.description
    } for b in book_list])

    if os.path.exists(file_path):
        df_old = pd.read_csv(file_path)
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["BookID"])
    else:
        df = df_new

    df.to_csv(file_path, index=False)

def write_users_csv(user_list):
    file_path = "dataset/user.csv"
    df_new = pd.DataFrame([{
        "UserID": u.id,
        "Name": u.name
    } for u in user_list])

    if os.path.exists(file_path):
        df_old = pd.read_csv(file_path)
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["UserID"])
    else:
        df = df_new

    df.to_csv(file_path, index=False)

def write_ratings_csv(rating_list):
    file_path = "dataset/rating.csv"
    df_new = pd.DataFrame([{
        "UserID": r.user_id,
        "BookID": r.book_id,
        "Rating": r.rating
    } for r in rating_list])

    if os.path.exists(file_path):
        df_old = pd.read_csv(file_path)
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["UserID", "BookID"])
    else:
        df = df_new

    df.to_csv(file_path, index=False)
