import tkinter as tk
import re

def tokenize_query(query):
    """Tokenize the input query into words and symbols."""
    return re.findall(r'\w+|\S', query.lower())

def parse_query(tokens):
    """Parse the tokens to create a SQL query."""
    parsed_query = {
        "select_columns": [],
        "table": "",
        "where_conditions": "",
        "order_by_columns": [],
        "asc_desc": "",
    }

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Handle SELECT statements
        if token in ["show", "list", "display", "select"]:
            i += 1
            while i < len(tokens) and tokens[i] not in ["from", "where", "order", "in"]:
                if tokens[i] != "and":
                    parsed_query["select_columns"].append(tokens[i])
                i += 1

        # Handle FROM statements
        elif token == "from":
            i += 1
            parsed_query["table"] = tokens[i]
            i += 1

        # Handle WHERE conditions with "in"
        elif token == "in" and i + 2 < len(tokens) and tokens[i + 2] == "department":
            # Replace 'in' with '=' for department conditions
            parsed_query["where_conditions"] = f"department = '{tokens[i + 1].lower()}'"
            i += 3

        # Handle ORDER BY statements
        elif token == "order" and i + 1 < len(tokens) and tokens[i + 1] == "by":
            i += 2
            while i < len(tokens) and tokens[i] not in ["ascending", "descending"]:
                parsed_query["order_by_columns"].append(tokens[i])
                i += 1

            # Ascending or Descending
            if i < len(tokens):
                if tokens[i] == "ascending":
                    parsed_query["asc_desc"] = "asc"
                elif tokens[i] == "descending":
                    parsed_query["asc_desc"] = "desc"
                i += 1

    return parsed_query

def generate_sql(parsed_query):
    """Generate the SQL query from the parsed data."""
    select_columns = ", ".join(parsed_query["select_columns"])
    table = parsed_query["table"]
    where_conditions = parsed_query["where_conditions"].strip()
    order_by_columns = ", ".join(parsed_query["order_by_columns"])
    asc_desc = parsed_query["asc_desc"]

    sql_query = f"SELECT {select_columns} FROM {table}"

    if where_conditions:
        sql_query += f" WHERE {where_conditions}"

    if order_by_columns:
        sql_query += f" ORDER BY {order_by_columns}"
        if asc_desc:
            sql_query += f" {asc_desc}"

    return sql_query

def translate_to_sql():
    """Translate the input natural language query to SQL and display it."""
    nl_query = query_input.get()
    tokens = tokenize_query(nl_query)
    parsed_query = parse_query(tokens)
    sql_query = generate_sql(parsed_query)
    output_label.config(text=f"Generated SQL Query:\n{sql_query}", fg="green")

# GUI Implementation
root = tk.Tk()
root.title("Natural Language to SQL Translator")
root.geometry("900x500")
root.config(bg="#f4f4f9")  # Light background color

# Title Label with improved font
tk.Label(root, text="Natural Language to SQL Translator", font=("Segoe UI", 22, "bold"), fg="#004e64", bg="#f4f4f9").pack(pady=20)

# Frame for Input Section
input_frame = tk.Frame(root, bg="#f4f4f9")
input_frame.pack(pady=20)

# Frame for Input Section
input_frame = tk.Frame(root, bg="#f4f4f9")
input_frame.pack(pady=20)

# Input Label
tk.Label(input_frame, text="Enter your query:", font=("Segoe UI", 14), fg="#004e64", bg="#f4f4f9").pack(anchor="w", padx=10)

# Input Entry (without padx, added padding in the frame)
query_input = tk.Entry(input_frame, width=80, font=("Segoe UI", 12), borderwidth=2, relief="solid")
query_input.pack(pady=10)

# Translate Button with rounded corners
translate_button = tk.Button(root, text="Translate to SQL", font=("Segoe UI", 14, "bold"), bg="#62b3b2", fg="white", command=translate_to_sql,
                             relief="solid", padx=20, pady=10, bd=0)
translate_button.pack(pady=20)

# Output Label
output_label = tk.Label(root, text="", font=("Segoe UI", 14), wraplength=850, justify="left", fg="green", bg="#f4f4f9")
output_label.pack(pady=10, padx=20)

# Run the GUI
root.mainloop()
