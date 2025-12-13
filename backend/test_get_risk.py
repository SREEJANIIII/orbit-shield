from backend import app

print("Imported backend.app")
res = app.get_risk()
print(res)
