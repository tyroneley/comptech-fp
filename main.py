import tkinter as tk
from pyparsing import Word, alphas, alphanums, oneOf, delimitedList, Optional, Group, CaselessKeyword

DATABASE_SCHEMA = {
    "employees": ["id", "name", "age", "department", "salary"],
    "departments": ["id", "name", "location"]
}

SELECT = oneOf("show list display select", caseless=True)
FROM = CaselessKeyword("from")
WHERE = CaselessKeyword("where")
HAVING = CaselessKeyword("having")
GROUP_BY = CaselessKeyword("group by")
ORDER_BY = CaselessKeyword("order by")
ASC_DESC = oneOf("asc desc", caseless=True)
AND_OR = oneOf("and or", caseless=True)

COLUMN = Word(alphas + "_")
TABLE = Word(alphas + "_")
NATURAL_OPERATOR = oneOf("more_than less_than at_least at_most", caseless=True)
SQL_OPERATOR = oneOf("= > < >= <= !=", caseless=True)
OPERATOR = NATURAL_OPERATOR | SQL_OPERATOR
VALUE = Word(alphanums + "_'")

columns = delimitedList(COLUMN)("columns")
all_columns = CaselessKeyword("all").setParseAction(lambda: "*")
select_clause = SELECT + (all_columns | delimitedList(COLUMN))("select_columns")
from_clause = FROM + TABLE("table")

condition = Group(COLUMN + OPERATOR + VALUE)("condition")
conditions = condition + Optional(AND_OR + condition)("conditions")
where_clause = Optional(WHERE + conditions("where_conditions"))

group_by_clause = Optional(GROUP_BY + delimitedList(COLUMN)("group_by_columns"))
having_clause = Optional(HAVING + conditions("having_conditions"))
order_by_clause = Optional(ORDER_BY + delimitedList(COLUMN)("order_by_columns") + Optional(ASC_DESC)("asc_desc"))

query = select_clause("select_clause") + from_clause("from_clause") + where_clause + group_by_clause + having_clause + order_by_clause

def map_operator(operator):
    operator_mapping = {
        "more_than": ">",
        "less_than": "<",
        "at_least": ">=",
        "at_most": "<=",
        "=": "=",
        ">": ">",
        "<": "<",
        ">=": ">=",
        "<=": "<=",
        "!=": "!="
    }
    return operator_mapping.get(operator.lower())

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
    else:
        select_columns = ", ".join(select_columns) if isinstance(select_columns, list) else select_columns

    where_conditions = ""
    if "where_conditions" in parsed_query:
        where_conditions = " WHERE " + " ".join(
            [
                f"{cond[0]} {map_operator(cond[1])} {cond[2]}"
                if isinstance(cond, list)
                else cond
                for cond in parsed_query.where_conditions.asList()
            ]
        )

    group_by_columns = ""
    if "group_by_columns" in parsed_query:
        group_by_columns = " GROUP BY " + ", ".join(parsed_query.group_by_columns.asList())

    having_conditions = ""
    if "having_conditions" in parsed_query:
        having_conditions = " HAVING " + " ".join(
            [
                f"{cond[0]} {map_operator(cond[1])} {cond[2]}"
                if isinstance(cond, list)
                else cond
                for cond in parsed_query.having_conditions.asList()
            ]
        )

    order_by_columns = ""
    if "order_by_columns" in parsed_query:
        order_by_columns = " ORDER BY " + ", ".join(parsed_query.order_by_columns.asList())
        if "asc_desc" in parsed_query:
            order_by_columns += " " + parsed_query.asc_desc

    return f"SELECT {select_columns} FROM {table}{where_conditions}{group_by_columns}{having_conditions}{order_by_columns};"

# GUI
def on_query_submit():
    nl_query = query_entry.get()
    if nl_query.lower() == "exit":
        root.quit()
    else:
        try:
            parsed_query = query.parseString(nl_query, parseAll=False)
            schema_error = validate_schema(parsed_query)

            if schema_error:
                result_text.set(f"Error: {schema_error}")
            else:
                sql_query = generate_sql(parsed_query)
                result_text.set(f"Generated SQL Query: {sql_query}")

        except Exception as e:
            result_text.set(f"Error: Unable to parse the query.\nDetails: {str(e)}")

root = tk.Tk()
root.title("Natural Language to SQL Translator")

root.geometry("600x400")

title_label = tk.Label(root, text="Natural Language to SQL Translator", font=("Helvetica", 16))
title_label.pack(pady=(25, 10))

schema_label = tk.Label(root, text="Database Schema:\n\n" +
                    f"Employees Table: {DATABASE_SCHEMA['employees']}\n" +
                    f"Departments Table: {DATABASE_SCHEMA['departments']}\n",
                    justify=tk.LEFT, font=("Arial", 12))
schema_label.pack(pady=10)

query_label = tk.Label(root, text="Enter your natural language query:")
query_label.pack(pady=5)

explanation_text = tk.Label(root, text="More than: more_than, Less than: less_than, at least: at_least, at most: at_most", font=("Helvetica", 10), justify="left")
explanation_text.pack(pady=10)

query_entry = tk.Entry(root, width=50)
query_entry.pack(pady=5)

submit_button = tk.Button(root, text="Submit", command=on_query_submit)
submit_button.pack(pady=5)

result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, font=("Helvetica", 12), justify="left")
result_label.pack(pady=10)

root.mainloop()
