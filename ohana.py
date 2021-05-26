from simple_salesforce import Salesforce
import pandas as pd
import json
from collections import MutableMapping
from ohana.login import InstSFDC

# SFDC Credentials
sf = InstSFDC()

# Loop through an OrderedDict of depth n and return flat dict
def FlattenRow(record, sep="__", parent_key=""):
    items = []
    for key, value in record.items():
        if key == "attributes":
            continue
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(FlattenRow(value, sep, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


# Convert a list of OrderedDicts (n deep) into a DataFrame
def sfdc_to_df(result, clean_cols=False):
    list_of_rows = [FlattenRow(term) for term in result["records"]]
    df = pd.DataFrame(list_of_rows)
    if clean_cols:
        df.columns = (
            df.columns.str.replace("__c", "")
            .str.replace("__r", "")
            .str.replace("_", "")
        )
    return df


# Print SOQL Statement
def printSOQL(statement):
    keywords = [
        " FROM ",
        " WHERE ",
        " AND ",
        " GROUP BY ",
        " HAVING ",
        " ORDER BY ",
        " LIMIT ",
    ]
    for keyword in keywords:
        statement = statement.replace(keyword, "\n" + keyword[1:])
    statement = statement.replace(", ", ",\n\t")
    print(statement)


# Run Flow from Query to DataFrame
def soql_to_df(soql_query, print_result=False):
    if print_result:
        print("QUERY\n------------")
        printSOQL(soql_query)
    result = sf.query_all(soql_query)
    if result["totalSize"] != 0:
        df = sfdc_to_df(result)
        if print_result:
            print("\n\nFIRST RECORD\n------------")
            print(df.iloc[0])
            print(f"\n------------\n{len(df)} records found.")
        return df
    elif print_result:
        print(f"\n------------\n0 records found.")


# List an object's field Lables and Names
def ListObjectFields(sfdc_object, attributes=["label", "name", "type"]):
    describe = eval(f"sf.{sfdc_object}.describe()")
    extract = [[field[att] for att in attributes] for field in describe["fields"]]
    key = pd.DataFrame(extract, columns=attributes)
    key.sort_values(key.columns[0], ignore_index=True, inplace=True)
    return key


# Create Select * equivalent query text
def SelectStar(sfdc_object):
    df = ListObjectFields(sfdc_object)
    fields = df["name"].to_list()
    fields_string = ", ".join(fields)
    soql_query = f"SELECT {fields_string} FROM {sfdc_object} "
    return soql_query


def InsertRecords(df, sfdc_object, csv=True):
    cols = df.columns
    if "Id" in cols:
        raise ValueError("DataFrame cannot have an Id column for upload.")
    available_fields = ListObjectFields(sfdc_object, ["name"]).values
    erroneous_fields = [f for f in cols if f not in available_fields]
    if len(erroneous_fields) > 0:
        raise ValueError(
            f"One or more fields are not a part of the {sfdc_object} object.\n\nPlease revise: {erroneous_fields}"
        )
    upload_dict = [dict(i[1]) for i in df.iterrows()]
    result = eval(f"sf.bulk.{sfdc_object}.insert(upload_dict)")
    post_mortem = pd.DataFrame(result)
    post_mortem = pd.concat([post_mortem, df], axis=1)
    if csv:
        now = pd.to_datetime("today").strftime("%m-%d-%Y_%H%M%S")
        post_mortem.to_csv(f"{sfdc_object}_insert_post_mortem_{now}.csv", index=False)
    return post_mortem


# Update Records Using a DataFrame
def UpdateRecords(df, sfdc_object, csv=True):
    cols = df.columns
    if "Id" not in cols:
        raise ValueError("DataFrame requires an 'Id' column for upload.")
    available_fields = ListObjectFields(sfdc_object, ["name"]).values
    erroneous_fields = [f for f in cols if f not in available_fields]
    if len(erroneous_fields) > 0:
        raise ValueError(
            f"One or more fields are not a part of the {sfdc_object} object.\n\nPlease revise: {erroneous_fields}"
        )
    upload_dict = [dict(i[1]) for i in df.iterrows()]
    result = eval(f"sf.bulk.{sfdc_object}.update(upload_dict)")
    post_mortem = pd.DataFrame(result).drop("created", axis=1)
    post_mortem = pd.concat([post_mortem, df], axis=1).drop("Id", axis=1)
    if csv:
        now = pd.to_datetime("today").strftime("%m-%d-%Y_%H%M%S")
        post_mortem.to_csv(f"{sfdc_object}_update_post_mortem_{now}.csv", index=False)
    return post_mortem


"""
# Return SFDC Contact/Lead data based on Email
def contactFromEmail(
    email, fields=[], sfdc_object="Contact", multiple_results=False, remove_pi=True
):
    fields += ["Id, Email", "pi__pardot_hard_bounced__c", "pi__score__c"]
    flat_fields = ", ".join(set(fields))
    if sfdc_object == "Contact":
        soql_query = f"SELECT {flat_fields} FROM Contact WHERE Email = '{email}' OR Email2__c = '{email}' ORDER BY pi__score__c DESC"
    elif sfdc_object == "Lead":
        soql_query = f"SELECT {flat_fields} FROM Lead WHERE Email = '{email}' ORDER BY pi__score__c DESC"
    else:
        print("Object must be either 'Contact' or a 'Lead'")

    result = sf.query(soql_query)
    size = result["totalSize"]

    if size == 0:
        info_dict = {f"{sfdc_object}_Email": email, "Results": 0}

    else:
        df = sfdc_to_df(result)
        junk = [
            f"{sfdc_object}_pipardothardbounced",
            f"{sfdc_object}_piscore",
        ]  # possible junk

        if not multiple_results:
            non_bounces = sum(df[f"{sfdc_object}_pipardothardbounced"] == False) > 0
            if non_bounces:
                df = df.loc[~df[f"{sfdc_object}_pipardothardbounced"]].reset_index(
                    drop=True
                )
            info_dict = df.loc[0].to_dict()
            info_dict["Results"] = size
            if remove_pi:
                for key in junk:
                    try:
                        info_dict.pop(key)
                    except:
                        next
        else:
            if remove_pi:
                df.drop(columns=junk, inplace=True)
            info_dict = list(df.transpose().to_dict().values())

    return info_dict


# Return SFDC Contact/Lead data based on Name
def contactFromName(
    name, fields=[], sfdc_object="Contact", multiple_results=False, remove_pi=True
):
    fields += ["Id", "Name", "pi__pardot_hard_bounced__c", "pi__score__c"]
    flat_fields = ", ".join(set(fields))
    if sfdc_object == "Contact":
        soql_query = f"SELECT {flat_fields} FROM Contact WHERE Name = '{name}' ORDER BY pi__score__c DESC"
    elif sfdc_object == "Lead":
        soql_query = f"SELECT {flat_fields} FROM Lead WHERE Name = '{name}' ORDER BY pi__score__c DESC"
    else:
        print("Object must be either 'Contact' or a 'Lead'")

    result = sf.query(soql_query)
    size = result["totalSize"]

    if size == 0:
        info_dict = {f"{sfdc_object}_Name": name, "Results": 0}

    else:
        df = sfdc_to_df(result)
        junk = [
            f"{sfdc_object}_pipardothardbounced",
            f"{sfdc_object}_piscore",
        ]  # possible junk

        if not multiple_results:
            non_bounces = sum(df[f"{sfdc_object}_pipardothardbounced"] == False) > 0
            if non_bounces:
                df = df.loc[~df[f"{sfdc_object}_pipardothardbounced"]].reset_index(
                    drop=True
                )
            info_dict = df.loc[0].to_dict()
            info_dict["Results"] = size
            if remove_pi:
                for key in junk:
                    try:
                        info_dict.pop(key)
                    except:
                        next
        else:
            if remove_pi:
                df.drop(columns=junk, inplace=True)
            info_dict = list(df.transpose().to_dict().values())

    return info_dict
"""
