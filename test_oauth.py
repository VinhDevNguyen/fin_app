from infrastructure.gdrive.google_drive_gateway import GoogleDriveGateway

if __name__ == "__main__":
    # This will open a browser window for you to authenticate
    gw = GoogleDriveGateway.from_oauth("credentials.json", "token.json")
    print("OAuth flow completed. Token saved to token.json.")