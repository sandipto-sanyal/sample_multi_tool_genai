# Load MySQL with Sample Data
- Go to https://github.com/datacharmer/test_db and download the project as a ZIP
- Extract the zip folder
- Check whether the `C:\Program Files\MySQL\MySQL Server 8.0\bin` is added to path. If not then add it.
- Open mysql workbench then run the following commands:
    - Create a non-root user
    ```sql
    CREATE USER 'python_user'@'localhost' IDENTIFIED BY 'password';
    ```
    - Grant all accesses to Database employees
    ```sql
    GRANT ALL PRIVILEGES ON employees.* TO 'python_user'@'localhost';
    FLUSH PRIVILEGES;
        
    GRANT RELOAD ON *.* TO 'python_user'@'localhost';
    FLUSH PRIVILEGES;
    ```
- Open a command prompt from test_db-master
- Run the following command that creates employees database with necessary schemas and data
```bash
mysql -t -u python_user -p < employees.sql
```
- Wait for some time and see the final following Output
```plaintext
+---------------------+
| data_load_time_diff |
+---------------------+
| 00:01:09            |
+---------------------+
```
- Note: At any step MySQL gives errors, paste the error and upload your `test_db-master\employees.sql` to ChatGPT/Gemini/Claude to understand and take actions accordingly from workbench.

# .env Contents
```
# azure secrets
# AZURE_OPENAI_API_TYPE=azure
# AZURE_OPENAI_API_KEY=azure_api_key
# AZURE_OPENAI_ENDPOINT=

OPENAI_API_KEY=
OPENAI_API_VERSION=2024-05-01-preview


ORCHESTRATOR_MODEL=gpt-4o-mini
SUBAGENT_MODEL=gpt-4o-mini

# MYSQL Secrets
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=
```