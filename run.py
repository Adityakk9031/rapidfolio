"""Entry point to run the Rapidfolio SOP Pre-Flight Linter & Compiler server."""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"[*] Starting Rapidfolio SOP Pre-Flight Linter & DAG Compiler at http://{host}:{port}")
    uvicorn.run("src.api.app:app", host=host, port=port, reload=True)
