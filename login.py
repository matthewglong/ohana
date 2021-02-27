# %%
import ohana.filepath as filepath
import json
from simple_salesforce import Salesforce
import os


def InstSFDC():
    dummy_file = "filepath.py"
    dummy_path = filepath.__file__
    cred_dir = "sfdc_creds"
    creds_file = "sfdc_creds.json"

    creds_path = dummy_path.replace(dummy_file, cred_dir) + os.path.sep + creds_file
    try:
        with open(creds_path) as c:
            creds = json.load(c)

            sf = Salesforce(
                username=creds["username"],
                password=creds["password"],
                security_token=creds["security_token"],
            )
    except:
        print("Your login credentials are missing, incorrect, or expired.")
        creds = {}
        for key in ["username", "password", "security_token"]:
            creds[key] = input(f"Please enter your SFDC {key}: ")

        with open(creds_path, "w") as outfile:
            json.dump(creds, outfile)

        sf = InstSFDC()

    return sf


# %%
