import boto3
import json
import os

class SecretManager:
    def __init__(self, env_file_path: str = ".env"):
        """
        Initialize the SecretManager.

        :param env_file_path: The path where the .env file will be created.
        """
        # Fetch the secret name directly from an environment variable
        self.secret_name = os.getenv("SECRET_NAME")  # Environment variable containing the secret name
        self.env_file_path = env_file_path

    def fetch_secrets_and_create_env(self):
        """
        Fetch secrets from AWS Secrets Manager based on the secret name and create a .env file.
        """
        if not self.secret_name:
            raise ValueError("Environment variable 'SECRET_NAME' is not set or has no value.")

        # Create a Secrets Manager client
        client = boto3.client('secretsmanager')

        try:
            # Retrieve the secret value
            secret_value = client.get_secret_value(SecretId=self.secret_name)
            secret = secret_value['SecretString']
            
            # Convert the JSON string to a dictionary
            secret_dict = json.loads(secret)

            # Create an .env file and write the secrets to it
            with open(self.env_file_path, 'w') as env_file:
                for key, value in secret_dict.items():
                    env_file.write(f"{key}={value}\n")
            
            print(f"Secrets from '{self.secret_name}' have been written to '{self.env_file_path}'.")

        except Exception as e:
            print(f"Error fetching secrets: {e}")

# Usage example
def create_dotenv():
    secret_manager = SecretManager()
    secret_manager.fetch_secrets_and_create_env()

