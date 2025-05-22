from .content_base import content_based_recommend
from .collaborative_filter import cf_model, ratings, reverse_book_mapping, book_mapping

def recommend_for_user(user_id, top_k):
    # Get all books rated by User with ID is user_id
    rated_books = ratings[ratings['UserID'] == user_id]['book_id'].tolist()

    # Get all book ids in the dataset
    all_books = ratings['book_id'].unique().tolist()

    # Find books that the user has not rated
    unrated_books = [book for book in all_books if book not in rated_books]
    
    # Get similar books using content-based filtering
    recommended_books = set()
    for book in unrated_books:
        bookId = reverse_book_mapping.get(book)
        similar_books_id = content_based_recommend(bookId, 2)
        similar_books = [book_mapping.get(similar_book_id) for similar_book_id in similar_books_id]
        recommended_books.update(similar_books)

    # Remove books already rated by User 
    recommended_books = [b for b in recommended_books if b not in rated_books]

    # Predict ratings for each recommended book
    predicted_ratings = [(book, cf_model.pred(1, book, normalized=0)) for book in recommended_books]
    
    # Sort books by predicted rating in descending order
    sorted_books = sorted(predicted_ratings, key=lambda x: x[1], reverse=True)

    sorted_books_id = [(reverse_book_mapping[idx], rating) for idx, rating in sorted_books][:top_k]

    return sorted_books_id