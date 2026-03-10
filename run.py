import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("Starting ERP Purchase Order System...")
    print("Access the application at: http://127.0.0.1:8000")
    print("API Documentation at: http://127.0.0.1:8000/api/docs")
    print("Press CTRL+C to stop the server\n")
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["backend"]
    )
