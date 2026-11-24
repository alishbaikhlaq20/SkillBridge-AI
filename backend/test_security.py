from security import hash_password, verify_password

password = "mySecret123"

hashed = hash_password(password)

print("Original password:", password)
print("Hashed password:", hashed)

print("Correct password:", verify_password("mySecret123", hashed))
print("Wrong password:", verify_password("wrongPassword", hashed))