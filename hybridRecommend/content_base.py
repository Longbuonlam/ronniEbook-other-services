import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_matrix(books):
    """
        Dùng hàm "TfidfVectorizer" để chuẩn hóa "Genre" với:
        + analyzer='word': chọn đơn vị trích xuất là word
        + ngram_range=(1, 1): mỗi lần trích xuất 1 word
        + min_df=0: tỉ lệ word không đọc được là 0
        Lúc này ma trận trả về với số dòng tương ứng với số lượng film và số cột tương ứng với số từ được tách ra từ "Genre"
    """
    # Combine multiple fields into one text string per book
    books['combined'] = books['Genre'] + ' ' + books['Title'] + ' ' + books['Author'] + ' ' + books['Description']

    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 1), min_df=1)
    new_tfidf_matrix = tf.fit_transform(books['combined'])
    return new_tfidf_matrix

import os
# Use path relative to the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
books = pd.read_csv(os.path.join(current_dir, "dataset/book.csv"))
matrix = tfidf_matrix(books)
cosine_sim = cosine_similarity(matrix)

def content_based_recommend(book_id, top_x):
    idx = books[books['BookID'] == book_id].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:top_x + 1]
    return [books.iloc[i[0]]['BookID'] for i in sim_scores]

