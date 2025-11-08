#!/bin/bash
cd backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload
