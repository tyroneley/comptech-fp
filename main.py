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

        if token in ["show", "list", "display", "select"]:
            i += 1
            while i < len(tokens) and tokens[i] not in ["from", "where", "order", "in"]:
                if tokens[i] != "and":
                    parsed_query["select_columns"].append(tokens[i])
                i += 1

        elif token == "from":
            i += 1
            parsed_query["table"] = tokens[i]
            i += 1

        elif token == "in" and i + 2 < len(tokens) and tokens[i + 2] == "department":
            parsed_query["where_conditions"] = f"department = '{tokens[i + 1].lower()}'"
            i += 3

        elif token == "order" and i + 1 < len(tokens) and tokens[i + 1] == "by":
            i += 2
            while i < len(tokens) and tokens[i] not in ["ascending", "descending"]:
                parsed_query["order_by_columns"].append(tokens[i])
                i += 1

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

root = tk.Tk()
root.title("Natural Language to SQL Translator")
root.geometry("800x500")
root.config(bg="#eef2f3")

tk.Label(
    root, 
    text="Natural Language to SQL Translator", 
    font=("Helvetica", 22, "bold"), 
    fg="#1a535c", 
    bg="#eef2f3"
).pack(pady=20)

input_frame = tk.Frame(root, bg="#eef2f3")
input_frame.pack(pady=10)

tk.Label(
    input_frame, 
    text="Enter your query:", 
    font=("Helvetica", 14), 
    fg="#1a535c", 
    bg="#eef2f3"
).grid(row=0, column=0, sticky="w", padx=10)

query_input = tk.Entry(
    input_frame, 
    width=60, 
    font=("Helvetica", 14), 
    relief="solid", 
    highlightbackground="#62b3b2", 
    highlightthickness=1
)
query_input.grid(row=1, column=0, pady=10, padx=10)

def on_enter(e):
    translate_button.config(bg="#505050")

def on_leave(e):
    translate_button.config(bg="#333333") 

translate_button = tk.Button(
    root, 
    text="Translate to SQL", 
    font=("Helvetica", 14, "bold"), 
    bg="#333333", 
    fg="#292626", 
    activebackground="#1a1a1a", 
    activeforeground="white", 
    command=translate_to_sql, 
    bd=0, 
    padx=20, 
    pady=8
)
translate_button.bind("<Enter>", on_enter) 
translate_button.bind("<Leave>", on_leave)
translate_button.pack(pady=10)

output_frame = tk.Frame(root, bg="#eef2f3", padx=10, pady=10)
output_frame.pack(fill="both", expand=True)

output_label = tk.Label(
    output_frame, 
    text="Generated SQL Query will appear here", 
    font=("Helvetica", 14), 
    wraplength=750, 
    justify="left", 
    fg="#1a535c", 
    bg="#eef2f3", 
    relief="solid", 
    padx=10, 
    pady=10
)
output_label.pack(fill="both", expand=True)

root.mainloop()
