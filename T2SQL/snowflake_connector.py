import os
from typing import Union
import pandas as pd
from snowflake.connector import connect, ProgrammingError,DatabaseError,InterfaceError
from dotenv import load_dotenv
import time
from tqdm import tqdm
load_dotenv()

class DependencyError(Exception):
    """Custom exception for missing dependencies."""
    pass

class ImproperlyConfigured(Exception):
    """Custom exception for improper configuration."""
    pass

class SnowflakeConnector:
    def __init__(self, role: Union[str, None] = None, warehouse: Union[str, None] = None):
        """
        Initialize the SnowflakeConnector with the given parameters.

        :param role: Snowflake role (optional)
        :param warehouse: Snowflake warehouse (optional)
        """
        self.account = self._get_env_variable("SNOWFLAKE_ACCOUNT")
        self.username = self._get_env_variable("SNOWFLAKE_USERNAME")
        self.password = self._get_env_variable("SNOWFLAKE_PASSWORD")
        self.database = self._get_env_variable("SNOWFLAKE_DATABASE")
        self.warehouse = self._get_env_variable("SNOWFLAKE_WAREHOUSE")
        self.schema = self._get_env_variable("SNOWFLAKE_SCHEMA")
        self.role = role 
        
        self.conn = self._connect_to_snowflake()
        self.dialect = "Snowflake SQL"

    def _get_env_variable(self, env_var: str) -> str:
        """
        Retrieve the value from environment variable.

        :param env_var: The environment variable name
        :return: The actual value to use
        """
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value
        else:
            raise ImproperlyConfigured(f"Please set your Snowflake {env_var.lower().replace('_', ' ')}.")

    def _connect_to_snowflake(self):
        """
        Establish a connection to Snowflake.

        :return: Snowflake connection object
        """
        try:
            conn = connect(
                user=self.username,
                password=self.password,
                account=self.account,
                database=self.database,
                schema = self.schema,
                warehouse=self.warehouse,
                client_session_keep_alive=True
            )
            return conn
        except ProgrammingError as e:
            raise DependencyError(f"Failed to connect to Snowflake: {e}")
        except DatabaseError as e:
            raise DependencyError(f"Database error occurred: {e}")
        except InterfaceError as e:
            raise DependencyError(f"Interface error occurred: {e}")

    def run_sql(self, sql: str) -> pd.DataFrame:
        try:
            # Start the query execution asynchronously
            cursor = self.conn.cursor()
            cursor.execute_async(sql)
            query_id = cursor.sfqid
            
            # Poll for query completion
            progress_bar = tqdm(total=100, desc="Executing Query", unit="%")
            while True:
                # Get the current query status
                status = self.conn.get_query_status(query_id)
                status = str(status).split(".")[-1]

                if status == 'RUNNING':
                    # Simulate progress increment (you can adjust this logic)
                    time.sleep(10)  # Poll every 5 seconds
                    progress_bar.update(1) # Update progress by 1 step
                elif status == 'FAILED_WITH_ERROR':
                    progress_bar.close()
                    raise Exception(f"Query {query_id} failed.")
                elif status == 'SUCCESS':
                    progress_bar.n = 100  # Set the progress bar to 100%
                    progress_bar.close()
                    break

            # Fetch the results
            cursor.get_results_from_sfqid(query_id)
            result = cursor.fetchmany(200_000)
            df = pd.DataFrame(result, columns=[desc[0] for desc in cursor.description])
            return df

        except ProgrammingError as e:
            raise RuntimeError(f"Failed to execute SQL query: {e}")
        except DatabaseError as e:
            raise RuntimeError(f"Database error occurred during query execution: {e}")
        except InterfaceError as e:
            raise RuntimeError(f"Interface error occurred during query execution: {e}")
