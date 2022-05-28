from pydrive2.auth import GoogleAuth

if __name__ == "__main__":
    try:
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("credentials.json")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
            gauth.SaveCredentialsFile("credentials.json")
            print("Credentials.json has been created")
        else:
            print("A valid credentials.json already exists")
    except:
        print("\nPlease make sure to run this file close to settings.yaml")