from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from hybridRecommend.recommend import recommend_for_user
from hybridRecommend.content_base import content_based_recommend
from hybridRecommend.update_data import write_books_csv, write_users_csv, write_ratings_csv, SyncData
from gradio_client import Client, handle_file
import requests
import sseclient
import uuid
from tts.model import AudioRequest

app = FastAPI()

# Allow requests from specific ports
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],    
    allow_headers=["*"],    
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/recommend/{user_id}")
def get_recommendations(user_id: str):
    recommendations = recommend_for_user(user_id, 10)

    # Convert recommendations (tuples) to a list of dictionaries
    recommendations_dict = [
        {"book_id": str(rec[0]), "predicted_rating": float(rec[1])}
        for rec in recommendations
    ]
    
    return {"user_id": user_id, "recommendations": recommendations_dict}

@app.get("/recommend/book/{book_id}")
def get_book_recommendations(book_id: str):
    recommendations = content_based_recommend(book_id, 6)
    return {"book_id": book_id, "recommendations": recommendations}

@app.post("/update-daily-data")
async def update_data(sync_data: SyncData):
    books = sync_data.books
    users = sync_data.users
    ratings = sync_data.ratings

    if books:
        write_books_csv(books)
    if users:
        write_users_csv(users)
    if ratings:
        write_ratings_csv(ratings)

    return {"message": "Data updated successfully"}

@app.post("/synthesize")
def synthesize_text(prompt: str = Body(...), language: str = Body(...), audio_file_pth: str = Body(...)):
    client = Client("thinhlpg/vixtts-demo")
    result = client.predict(
        prompt=prompt,
        language=language,
        audio_file_pth=handle_file(audio_file_pth),
        normalize_text=True,
        api_name="/predict"
    )
    return result

@app.post("/process_audio")
def process_audio(request: AudioRequest):
    # Step 1: Make the POST request
    post_url = "https://thinhlpg-vixtts-demo.hf.space/queue/join?__theme=system"
    session_hash = str(uuid.uuid4())  # Generate a unique session hash
    post_data = {
        "data": [
            request.prompt,
            request.language,
            {
                "path": request.user_record.path,
                "url": request.user_record.recordUrl,
                "orig_name": request.user_record.originalName,
                "size": request.user_record.size,
                "is_stream": False,
                "mime_type": None,
                "meta": {"_type": "gradio.FileData"}
            },
            request.normalize_vi_text
        ],
        "event_data": None,
        "fn_index": 0,
        "trigger_id": 11,
        "session_hash": session_hash
    }

    headers = {"Content-Type": "application/json"}
    post_response = requests.post(post_url, headers=headers, json=post_data)

    if post_response.status_code != 200:
        return {"error": "Failed to initiate processing", "details": post_response.text}

    # Step 2: Listen to the SSE stream
    get_url = f"https://thinhlpg-vixtts-demo.hf.space/queue/data?session_hash={session_hash}"
    client = sseclient.SSEClient(get_url)

    # Listen for messages
    for msg in client:
        print("Received message:", msg.data)

        # Check if the message is "process_completed"
        if '"msg":"process_completed"' in msg.data:
            # Extract the URL directly from the message string
            start_index = msg.data.find('"url":"') + len('"url":"')
            end_index = msg.data.find('"', start_index)
            output_url = msg.data[start_index:end_index]

            print("Process completed. File URL:", output_url)
            # Stop the SSE stream
            break  # Exit the loop after receiving the "process_completed" message
        
    return output_url