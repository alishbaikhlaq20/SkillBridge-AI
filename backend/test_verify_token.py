from auth import create_access_token, verify_access_token


token = create_access_token(4)

print("Token:")
print(token)

user_id = verify_access_token(token)

print("Recovered user ID:")
print(user_id)