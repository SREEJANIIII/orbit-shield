Quick start (backend)
---------------------

- Create and activate the venv, then install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

- Run the app from the project root using the package name:

```powershell
.\.venv\Scripts\uvicorn.exe backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Notes:
- The app will try to fetch TLE data from CelesTrak. If the server blocks the request,
  the application falls back to built-in sample TLEs so startup succeeds.
- If you want to run from inside the `backend` folder, you can instead run `uvicorn app:app --reload`.
