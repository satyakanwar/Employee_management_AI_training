def login(username, password):

    if username == "admin" and password == "1234":
        print("Login Successful")
    else:
        print("Invalid Username or Password")


login("admin", "1234")