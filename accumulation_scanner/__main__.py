import uvicorn

if __name__ == "__main__":
    uvicorn.run("accumulation_scanner.api.app:app", host="0.0.0.0", port=8000, reload=False)
