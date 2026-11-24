from auth import create_access_token


token = create_access_token(1)

print("Generated JWT:")
print(token)