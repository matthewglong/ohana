# %%
import json
from simple_salesforce import Salesforce
import os
import getpass
from cryptography.fernet import Fernet


def LoadSecretKey(filepath=""):
    if "secret.key" not in os.listdir(filepath):
        key = Fernet.generate_key()
        with open(f"{filepath}{os.path.sep}secret.key", "wb") as key_file:
            key_file.write(key)
    else:
        with open(f"{filepath}{os.path.sep}secret.key", "rb") as key_file:
            key = key_file.read()
    secret = Fernet(key)
    print('we did it!')
    return secret


def TransCryptText(text, func):
    encoded_text = text.encode()
    crypt_bits = func(encoded_text)
    crypt_text = crypt_bits.decode()
    return crypt_text


def TransCryptDict(target_dict, func):
    tct = TransCryptText
    crypt_dict = {tct(k, func): tct(v, func) for k, v in target_dict.items()}
    return crypt_dict


def InstSFDC():
    dummy_file = "login.py"
    creds_dir_name = "sfdc_creds"
    creds_file_name = "sfdc_creds.json"
    slash = os.path.sep
    root = __file__.replace(slash + dummy_file, "")
    creds_dir = slash.join([root, creds_dir_name])
    creds_path = slash.join([creds_dir, creds_file_name])
    if "sfdc_creds" not in os.listdir(root):
        os.mkdir(creds_dir)

    secret_key = LoadSecretKey(creds_dir)

    try:
        with open(creds_path) as c:
            encrypted_creds = json.load(c)
            creds = TransCryptDict(encrypted_creds, secret_key.decrypt)
            for k, v in creds.items():
                print(k, v)
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

        encrypted_creds = TransCryptDict(creds, secret_key.encrypt)

        with open(creds_path, "w") as outfile:
            json.dump(encrypted_creds, outfile)

        sf = InstSFDC()

    return sf
