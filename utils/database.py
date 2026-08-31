import psycopg2


class DatabaseUtil:
    def __init__(self, db_config):
        self.db_config = db_config

        try:
            self.connection = psycopg2.connect(**db_config)
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            self.connection = None

    def schema_details(self, schema_name):
        schema_info_context = ""
        connection = self.connection
        cursor = None

        try:
            if connection is None:
                return "Database connection unavailable."

            cursor = connection.cursor()
            schema_info_context = f"Database Schema: {schema_name}\n\n"

            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                (schema_name,),
            )
            tables_list = cursor.fetchall()
            for table in tables_list:
                table_name = table[0]
                schema_info_context = f"{schema_info_context}\nTable: {table_name}\n"

                cursor.execute(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s",
                    (table_name,),
                )
                columns_list = cursor.fetchall()

                for column in columns_list:
                    column_name = column[0]
                    data_type = column[1]
                    schema_info_context = f"{schema_info_context}  {column_name}: {data_type}\n"

                cursor.execute(f"Select * from {table_name} limit 5;")
                sample_data = cursor.fetchall()
                schema_info_context = f"{schema_info_context}\nSample Data:\n"
                for row in sample_data:
                    schema_info_context = f"{schema_info_context}  {row}\n"

        except Exception as e:
            print(f"Error occurred while fetching schema details: {e}")
            schema_info_context = f"Error occurred while fetching schema details: {e}"
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

        return schema_info_context


if __name__ == "__main__":
    db = DatabaseUtil({
        "database": "postgres",
        "user": "postgres",
        "password": "123",
        "host": "localhost",
        "port": 5432,
    })

    result = db.schema_details("public")

    with open("test_schema_details.txt", "w") as f:
        f.write(result)

