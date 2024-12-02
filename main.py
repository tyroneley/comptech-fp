from pyparsing import Word, alphas, alphanums, oneOf, delimitedList, Optional, Group, CaselessKeyword

DATABASE_SCHEMA = {
    "employees": ["id", "name", "age", "department", "salary"],
    "departments": ["id", "name", "location"]
}

SELECT = oneOf("show list display", caseless=True)
FROM = CaselessKeyword("from")
WHERE = CaselessKeyword("where")
AND_OR = oneOf("and or", caseless=True)

COLUMN = Word(alphas + "_")
TABLE = Word(alphas + "_")
OPERATOR = oneOf("= > < >= <= !=")
VALUE = Word(alphanums + "_'")

columns = delimitedList(COLUMN)("columns")
all_columns = CaselessKeyword("all").setParseAction(lambda: "*")
select_clause = SELECT + (all_columns | columns)("select_columns")
from_clause = FROM + TABLE("table")
condition = Group(COLUMN + OPERATOR + VALUE)("condition")
conditions = condition + Optional(AND_OR + condition)("conditions")
where_clause = WHERE + conditions("where_conditions")

query = select_clause("select_clause") + from_clause("from_clause") + Optional(where_clause("where_conditions"))

def validate_schema(parsed_query):
    table = parsed_query.table
    if table not in DATABASE_SCHEMA:
        return f"Error: Table '{table}' not found in the database schema."

    select_columns = parsed_query.select_columns
    if select_columns == "*":
        return None 
    if isinstance(select_columns, list):
        for column in select_columns:
            if column not in DATABASE_SCHEMA[table]:
                return f"Error: Column '{column}' not found in the table '{table}'."

    return None

def generate_sql(parsed_query):
    table = parsed_query.table
    select_columns = parsed_query.select_columns

    if select_columns == "*":
        select_columns = "*"
    elif isinstance(select_columns, list):
        select_columns = ", ".join(select_columns)

    where_conditions = ""
    if "where_conditions" in parsed_query:
        where_conditions = " WHERE " + " ".join(
            [" ".join(condition) if isinstance(condition, list) else condition for condition in parsed_query.where_conditions.asList()]
        )

    return f"SELECT {select_columns} FROM {table}{where_conditions};"

if __name__ == "__main__":
    print("Welcome to the Natural Language to SQL Translator!")
    print("Database Schema: ", DATABASE_SCHEMA)

    while True:
        nl_query = input("\nEnter your natural language query (or type 'exit' to quit): ")
        if nl_query.lower() == "exit":
            break

        try:
            parsed_query = query.parseString(nl_query)
            schema_error = validate_schema(parsed_query)

            if schema_error:
                print("\nError:", schema_error)
            else:
                sql_query = generate_sql(parsed_query)
                print("\nGenerated SQL Query:")
                print(sql_query)

        except Exception as e:
            print("\nError: Unable to parse the query.")
            print("Details:", str(e))
