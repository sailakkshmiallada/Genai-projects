import os
import re
from openai import OpenAI
import json

class SQLGenerator:
    def __init__(self, base_url: str,api_key: str):
        """
        Initialize the SQLGenerator with the provided OpenAI API key.

        :param api_key: The OpenAI API key.
        """
        self.client = OpenAI(base_url=base_url,api_key=api_key)

    def generate_response(self, prompt: str, model: str = "gpt-4o-0513", temperature: float = 0.0, max_tokens: int = 4096,seed: int =42) -> str:
        """
        Generate a response from the LLM based on the prompt and extract the SQL query.

        :param prompt: The prompt to generate a response for.
        :param model: The model to use for generating the response.
        :param temperature: The temperature to use for generating the response.
        :param max_tokens: The maximum number of tokens to generate.
        :return: The extracted SQL query.
        """
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert SQL generator for Snowflake. Your task is to create efficient and optimized SQL queries based on the table and column information provided. Your responses should adhere to Snowflake SQL syntax and best practices. When generating SQL queries, consider the following guidelines:
                        1. Use the most appropriate SQL functions and operators for the operations required.
                        2. Ensure that the queries are optimized for performance, especially when dealing with large datasets.
                        3. If necessary, suggest the creation of indexes or other performance enhancements.
                        4. Provide clear and concise comments within the SQL queries to explain the purpose and logic of each part.
                        5. Ensure that the SQL queries are secure and follow Snowflake's security best practices."""
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            seed = seed
                )
        reponse  = json.loads(chat_completion)
        llm_response = reponse['choices'][0]['message']['content']
        print(llm_response)
        sql_query =  self._process_llm_response(llm_response)
        
        input_tokens = reponse['usage']['prompt_tokens']
        output_tokens = reponse['usage']['completion_tokens']
        return {
            "sql_query": sql_query,
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
        }

    def _process_llm_response(self, llm_response: str) -> str:
        """
        Process the LLM response to extract SQL query or content within <response> tags.

        :param llm_response: The response from the LLM.
        :return: The extracted SQL query, content within <response> tags, or a static error message.
        """
        # Check if the response contains an SQL query
        if '```sql' in llm_response or '<generated_query>' in llm_response:
            sql_query = self._extract_sql(llm_response)
            if sql_query:
                sql_query = self._modify_query(sql_query)
                return sql_query
        
        # Alternatively, check for <response> tags
        if '<response>' in llm_response:
            response_content = self._extract_response_content(llm_response)
            if response_content:
                return response_content
        
        # If no conditions are met, return a static error message
        return "Something went wrong. Please try again."

    @staticmethod
    def _extract_sql(llm_response: str) -> str:
        """
        Extract the SQL query from the LLM response.

        :param llm_response: The response from the LLM.
        :return: The extracted SQL query.
        """
        patterns = [
            r"```sql\n(.*?)```",
            r"```sql\n(.*?)</generated_query>",
            r"```(.*?)```",
            r"```(.*)</generated_query>",
            r"<generated_query>(.*?)</generated_query>"
        ]

        for pattern in patterns:
            sql = re.search(pattern, llm_response, re.DOTALL)
            if sql:
                return re.sub(r"<generated_query>|</generated_query>|```|```sql", "", sql.group(1)).strip()

        # If no pattern matches, still perform re.sub on the entire response
        return re.sub(r"<generated_query>|</generated_query>|```|```sql", "", llm_response).strip()

    @staticmethod
    def _extract_response_content(llm_response: str) -> str:
        """
        Extract content within <response> tags from the LLM response.

        :param llm_response: The response from the LLM.
        :return: The extracted content within <response> tags or empty string if not found.
        """
        match = re.search(r"<response>(.*?)</response>", llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return ""
    @staticmethod
    def _modify_query(query: str, config_file: str = 'config.json') -> str:
        """
        Modify the SQL query by updating the SELECT clause with aliased columns from the config
        and tracking index changes.

        :param query: Original SQL query string
        :param config_file: Path to the JSON configuration file
        :return: Modified SQL query
        """
        # Load configuration from JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Define the table and alias mapping
        table_alias_mapping = {
            "CLM_WGS_GNCCLMP_CMPCT": "CLM",
            "CLM_WGS_GNCDTLP_CMPCT": "DTL",
            "CLM_WGS_GNCNATP_E00_CMPCT": "E00",
            "CLM_WGS_GNCNATP_EA1_CMPCT": "EA1",
            "CLM_WGS_GNCNATP_EA2_CMPCT": "EA2",
            "CLM_WGS_GNCNATP_EA3_CMPCT": "EA3",
            "CLM_WGS_GNCEOBP_CMPCT": "EOB"
        }

        # Generate a combined list of aliased columns
        combined_columns = []
        # Loop through the config and generate aliased columns
        for table_name, table_config in config.items():
            alias = table_alias_mapping.get(table_name)
            select_columns = table_config.get("select_columns", [])

            # Create aliased columns for the current table
            aliased_columns = [f"{alias}.{col}" if "DDC_CD_HCID" not in col else col for col in select_columns]

            # Append the aliased columns to the combined list
            combined_columns.extend(aliased_columns)

        columns = ",\n".join(combined_columns)

        # Define the pattern to find the FROM clause with the specific table and alias
        from_pattern = re.compile(r"\bFROM\s+CLM_WGS_GNCCLMP_CMPCT\s+CLM\b", re.IGNORECASE)

        # Replace the SELECT clause with new aliased columns
        match = from_pattern.search(query)
        if match:
            start_index = match.start()

            # Create the new SELECT clause using the aliased columns
            new_select_clause = f"SELECT\n{columns}\n"

            # Replace everything before FROM clause with the new SELECT clause
            new_query = (
                new_select_clause +
                query[start_index:].strip()
            )

            # Find the end index in the updated query
            match_new = from_pattern.search(new_query)
            if match_new:
                end_index = match_new.end()

                # Define the subquery to be added
                subquery = """
                INNER JOIN ( 
                    SELECT GNCHIIOS_HCLM_DCN, MIN(GNCHIIOS_HCLM_SEQ_NBR) AS min_seq
                    FROM CLM_WGS_GNCCLMP_CMPCT 
                    GROUP BY GNCHIIOS_HCLM_DCN
                    ) AS ms ON CLM.GNCHIIOS_HCLM_DCN = ms.GNCHIIOS_HCLM_DCN AND CLM.GNCHIIOS_HCLM_SEQ_NBR = ms.min_seq
                """

                # Insert the subquery at the new end index
                modified_query = (
                    new_query[:end_index] + "\n" +
                    subquery.strip() + "\n" +
                    new_query[end_index:]
                )

                return modified_query
            return new_query
        return query

