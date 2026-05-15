import firebase_admin
from firebase_admin import credentials, db

SERVICE_ACCOUNT_FILE = "hybridmfa-firebase-adminsdk-fbsvc-c4bad1c186.json"

DATABASE_URL = "https://hybridmfa-default-rtdb.europe-west1.firebasedatabase.app/"

cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)

firebase_admin.initialize_app(cred, {
    "databaseURL": DATABASE_URL
})

ref = db.reference("/users/lewis")

ref.set({
    "pin": "1234",
    "enabled": True,
    "role": "admin"
})

print("User saved to Firebase.")

data = ref.get()
print("Data read from Firebase:")
print(data)
