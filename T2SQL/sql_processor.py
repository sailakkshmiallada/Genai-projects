import re 
import json
import boto3
import logging
import sqlparse
import numpy as np
import pandas as pd
from io import StringIO
from datetime import datetime, timezone
from sqlparse.tokens import Keyword, DML
from concurrent.futures import ThreadPoolExecutor
from snowflake_connector import SnowflakeConnector
from sqlparse.sql import IdentifierList, Identifier, Token
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, BotoCoreError



# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class SQLProcessor:
    def __init__(self, input_data):
        self.restricted_operations = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'REPLACE','TRUNCATE','RENAME']
        self.parsed = None
        self.DDC_CD_LMT_CLS_CDE = 'DDC_CD_LMT_CLS_CDE'
        self.claim_criteria = input_data.get('claim_criteria','')
        self.ticketId = input_data.get('ticket_id')
        self.reportType = input_data.get('report_type','line')
        self.bucket_name = input_data.get('clmBucket','')
        self.request_time = input_data.get('request_time',datetime.utcnow().isoformat())
        self.report_s3_file_path = "snowflakeReport"
        
        logger.info("SQLProcessor initialized.")

    def contains_restricted_operations(self, query: str) -> bool:
        """
        Check if the query contains any restricted operations.
        """
        self.parsed = sqlparse.parse(query)
        for statement in self.parsed:
            tokens = list(statement.flatten())
            for token in tokens:
                if token.ttype in (Keyword, Keyword.DML, Keyword.DDL) and token.value.upper() in self.restricted_operations:
                    logger.warning(f"Found restricted operation: {token.value.upper()}")
                    return True
        return False

    def is_valid_syntax(self) -> bool:
        """
        Validate the SQL syntax using sqlparse.
        """
        try:
            if not self.parsed:
                logger.error("Parsed SQL is empty.")
                return False
            return True
        except Exception as e:
            logger.error(f"Syntax validation error: {e}")
            return False

    def filter_limit_columns_by_values(self, df: pd.DataFrame, values: list) -> pd.DataFrame:
        """
        Concatenate limit columns based on pointer values and filter the DataFrame
        based on specified values present in the concatenated limits.

        :param df: Input DataFrame
        :param values: List of values to check in the concatenated_limits
        :return: Filtered DataFrame
        """

        logger.info("Starting to filter limit columns by values.")
        limit_columns = {}
        for col in df.columns:
            if col.startswith(self.DDC_CD_LMT_CLS_CDE):
                parts = col.split('_')
                if len(parts) > 1 and parts[-2].isdigit():
                    pointer_value = int(parts[-2])
                    if pointer_value not in limit_columns:
                        limit_columns[pointer_value] = []
                    limit_columns[pointer_value].append(col)

        df['concatenated_limit_clses'] = ''

        # Process each pointer value to concatenate limit classes
        for pointer_value in limit_columns.keys():
            columns = limit_columns[pointer_value]
            mask = df['DDC_DTL_ICDA_PNTR_1'] == str(pointer_value)  
            df.loc[mask, 'concatenated_limit_clses'] = df.loc[mask, columns].astype(str).agg(','.join, axis=1)

        pattern = '|'.join(map(re.escape, values))
        filtered_df = df[df['concatenated_limit_clses'].str.contains(pattern)]
        logger.info("Finished filtering limit columns.")
        return filtered_df
    
    def extract_limit_values(self, criteria: str) -> list:
        """
        Extracts limit class values from a given text string.
        """
        logger.info("Extracting limit values from criteria.")
        match = re.search(r'limit.*?:\s*([^;]+)\s*;', criteria, re.IGNORECASE)
        if match:
            limit_value = match.group(1)
            logger.info("Limit values extracted.")
            return [value.strip() for value in re.split(r'\s*(?:,|or|and)\s*', limit_value)]
        else:
            logger.debug("No limit values found in criteria.")
            return []

    def process_dataframe(self, df: pd.DataFrame, reportType, lookup_mapping='lookup_mapping.json') -> pd.DataFrame:
        """
        Processes the DataFrame by excluding specified columns and replacing values in specified columns.
        """
        logger.info("Processing DataFrame.")
        with open(lookup_mapping, 'r') as f:
            config = json.load(f)

        reportType = reportType.lower()
        exclude_columns = config['exclude_columns'][reportType]
        
        replace_mappings = config['replace_mappings']

        df = df.drop(columns=exclude_columns, errors='ignore')
        
        if reportType == 'claim':
            df = df.drop_duplicates()
        
        filtered_df = df[(df['GNCHIIOS_HCLM_ITEM_CDE'].isin(['80', '84'])) & (~df['DDC_CD_CLM_PAY_ACT_2_6'].str.startswith('DEL'))]

        # Find the minimum value for each Claim Number
        min_seq = filtered_df.groupby('GNCHIIOS_HCLM_DCN')['GNCHIIOS_HCLM_SEQ_NBR'].min()
        grouped_df = filtered_df.merge(min_seq, on=['GNCHIIOS_HCLM_DCN', 'GNCHIIOS_HCLM_SEQ_NBR'])

        grouped_df['DDC_CD_CLM_PAY_ACT'] = grouped_df['DDC_CD_CLM_PAY_ACT_1'] + grouped_df['DDC_CD_CLM_PAY_ACT_2_6']
        grouped_df['ADJUDICATE_MODE'] = 'MANUAL'
        grouped_df.loc[grouped_df['DDC_CD_HOW_ADJUD_CDE'] == 'A', 'ADJUDICATE_MODE'] = 'AUTO'

        for col, mapping_info in replace_mappings.items():
            if col in grouped_df.columns:
                new_col_name = mapping_info['new_column_name']
                value_mapping = mapping_info['mapping']
                grouped_df[new_col_name] = grouped_df[col].replace(value_mapping)

        conditions = [
            ((
                (grouped_df['DDC_CD_ITS_HOME_IND'] == 'Y') 
                & 
                (grouped_df['DDC_CD_PRVDR_IND'].isin(['A','B','C','H','I','K','M','Y','G','O','P','Z','S','V','E','F','R','T','U','W']))
            )|
            (
                (grouped_df['DDC_CD_ITS_HOME_IND'] != 'Y') 
                & 
                (
                    (grouped_df['DDC_CD_PAR_KEYED_IND'].isin(['P','Y']))
                    |
                    (grouped_df['DDC_CD_MX_PAR_IND'].isin(['Y','E','X','T','F','U','2','1']))
                )
            )),

            ((
                (grouped_df['DDC_CD_ITS_HOME_IND'] == 'Y') 
                & 
                (grouped_df['DDC_CD_PRVDR_IND'].isin(['N','D','L']))
            )|
            (
                (grouped_df['DDC_CD_ITS_HOME_IND'] != 'Y') 
                & 
                (grouped_df['DDC_CD_PAR_KEYED_IND'].isin(['N']))

            )|
                grouped_df['DDC_CD_MX_PAR_IND'].isin(['N','D']))
            
        ]
        choices = ['PAR', 'NON-PAR']
        grouped_df['PRVDR_STATUS'] = np.select(conditions, choices, default='NON-PAR')

        logger.info("DataFrame processing completed.")
        return grouped_df

    def upload_df_to_s3(self, df: pd.DataFrame , bucket_name: str, folder_name: str, file_name: str,request_time : str,large_data_flag=False) -> bool:
        """
        Upload a Pandas DataFrame to an S3 folder without saving the file locally.
        """
        logger.info("Starting upload to S3.")

        try:
            s3 = boto3.client('s3')
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            s3.put_object(Body=csv_buffer.getvalue(), Bucket=bucket_name, Key=f"{folder_name}/{file_name}_{request_time}.csv")
            logger.info("File uploaded to S3 successfully.")
            
            status = "SUCCESS"
            comments = "File uploaded successfully - The cleaned report currently generates approximately 200,000 rows. Please refine your search criteria." if large_data_flag else "File uploaded successfully" if df.shape[0] > 0 else "No data found"
            return status,comments
        except Exception as e:
            logger.error(f"File upload failed: {e}")

        return "FAILED", f"File upload failed: {e}"
    


    def process_query(self, query: str) -> str:
        """
        Process the SQL query by first checking for restricted operations.
        If no restricted operations are found, then validate syntax and potentially execute the query.
        """
        logger.info("Processing SQL query.")
        
        status = "FAILED"
        comments = ""
        if self.contains_restricted_operations(query):
            logger.warning("Restricted operations are prohibited.")
            comments += "Restricted operations are prohibited. Please ask criteria to pull the data from the database."
            return status,comments
        
        if self.is_valid_syntax() and 'SELECT' in query:
            print("sql is valid")
            connector = SnowflakeConnector()
            try:
                logger.debug("Executing SQL query.")
                df = connector.run_sql(query)
                large_data_flag = True if df.shape[0] == 200_000 else False
                print("Count of data pulled from snowflake:",df.shape)
                if df.shape[0] > 0:
                    if "limit" in self.claim_criteria.lower():
                        limit_values = self.extract_limit_values(self.claim_criteria)
                        print("limit values :",limit_values)
                        df = self.filter_limit_columns_by_values(df, limit_values)
                        print("Count of data after limit class values extracted :",df.shape)
                    
                    df = self.process_dataframe(df, self.reportType)
                
                status,comments = self.upload_df_to_s3(df, self.bucket_name, self.report_s3_file_path, self.ticketId,self.request_time,large_data_flag)

                return status,comments
            except Exception as err:
                logger.error(f"Error while executing query: {err}")
                comments += f"Error while executing query: {err}"
                return status,comments
        else:
            logger.error("Invalid SQL syntax.")
            comments += "Invalid SQL syntax. Please provide your criteria again."
            return status,comments