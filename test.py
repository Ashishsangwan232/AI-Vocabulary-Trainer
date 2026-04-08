from app import create_app


def run_smoke_test():
    app = create_app()
    client = app.test_client()

    word_response = client.post("/get_word", json={"user_id": "test_user"})
    print("POST /get_word status:", word_response.status_code)
    print("POST /get_word body:", word_response.get_json())

    progress_response = client.get("/progress", query_string={"user_id": "test_user"})
    print("GET /progress status:", progress_response.status_code)
    print("GET /progress body:", progress_response.get_json())


if __name__ == "__main__":
    run_smoke_test()
