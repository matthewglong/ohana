# %%
import ohana.filepath as filepath
import json
from simple_salesforce import Salesforce
import os
import getpass
from cryptography.fernet import Fernet


def LoadSecretKey(filepath=""):
    if "secret.key" not in os.listdir(filepath):
        key = Fernet.generate_key()
        with open(f"{filepath}/secret.key", "wb") as key_file:
            key_file.write(key)
    else:
        with open(f"{filepath}/secret.key", "rb") as key_file:
            key = key_file.read()
    secret = Fernet(key)
    return secret


def EncryptText(text, secret):
    encoded_text = text.encode()
    encrypted_bits = secret.encrypt(encoded_text)
    encrypted_text = encrypted_bits.decode()
    return encrypted_text


def DecryptText(text, secret):
    encoded_text = text.encode()
    decrypted_bits = secret.decrypt(encoded_text)
    decrypted_text = decrypted_bits.decode()
    return decrypted_text


def EncryptDict(target_dict, secret_key):
    encrypted_dict = {
        EncryptText(i, secret_key): EncryptText(v, secret_key)
        for i, v in target_dict.items()
    }
    return encrypted_dict


def DecryptDict(target_dict, secret_key):
    decrypted_dict = {
        DecryptText(i, secret_key): DecryptText(v, secret_key)
        for i, v in target_dict.items()
    }
    return decrypted_dict


def InstSFDC():
    dummy_file = "filepath.py"
    creds_dir_name = "sfdc_creds"
    creds_file_name = "sfdc_creds.json"
    root = filepath.__file__.replace("/" + dummy_file, "")
    creds_dir = os.path.sep.join([root, creds_dir_name])
    creds_path = os.path.sep.join([creds_dir, creds_file_name])
    if "sfdc_creds" not in os.listdir(root):
        os.mkdir(creds_dir)

    secret_key = LoadSecretKey(creds_dir)

    try:
        with open(creds_path) as c:
            encrypted_creds = json.load(c)
            creds = DecryptDict(encrypted_creds, secret_key)
            sf = Salesforce(
                username=creds["username"],
                password=creds["password"],
                security_token=creds["security_token"],
            )
    except:
        attempt_login = input(
            "Your login credentials are missing, incorrect, or expired. Would you like to add new credentials to the Ohana package? [y/n] "
        )
        if attempt_login != "y":
            raise ValueError(
                "Could not instantiate SFDC as a proper username, password, or security token were not provided."
            )
        creds = {}
        for key in ["username", "password", "security_token"]:
            help_text = f"Please enter your SFDC {key}: "
            if key in ["password", "security_token"]:
                creds[key] = getpass.getpass(help_text)
            else:
                creds[key] = input(help_text)

        encrypted_creds = EncryptDict(creds, secret_key)

        with open(creds_path, "w") as outfile:
            json.dump(encrypted_creds, outfile)

        sf = InstSFDC()

    return sf