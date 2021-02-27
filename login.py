# %%
import ohana.filepath as filepath
import json
from simple_salesforce import Salesforce
import os
import getpass


def InstSFDC():
    dummy_file = "filepath.py"
    creds_dir_name = "sfdc_creds"
    creds_file_name = "sfdc_creds.json"
    root = filepath.__file__.replace("/" + dummy_file, "")
    creds_dir = os.path.sep.join([root, creds_dir_name])
    creds_path = os.path.sep.join([creds_dir, creds_file_name])
    if "sfdc_creds" not in os.listdir(root):
        os.mkdir(creds_dir)

    try:
        with open(creds_path) as c:
            creds = json.load(c)

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

        with open(creds_path, "w") as outfile:
            json.dump(creds, outfile)

        sf = InstSFDC()

    return sf