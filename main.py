import tkinter as tk
from tkinter import ttk, messagebox
import re
import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
db_connection = sqlite3.connect("data.db")
db_cursor = db_connection.cursor()

tables = {
    "users": ["id", "name", "followers", "email", "created_at"],
    "posts": ["id", "user_id", "content", "created_at"],
    "comments": ["id", "post_id", "user_id", "content", "created_at"]
}

synonyms = {
    "name": ["name", "username", "user name", "the name"],
    "email": ["email", "email address", "the email"],
    "content": ["content", "post content", "message", "text", "the content"],
    "created_at": ["created_at", "created on", "joined", "date joined"],
    "followers": ["followers", "follower count", "number of followers", "the followers"],
    "user_id": ["user_id", "author id", "poster id"],
    "id": ["id", "post id", "user id", "comment id"],
}

query_history = []
# Populate all tables with sample data
def initialize_database():
    # Create 'users' table
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            followers INTEGER,
            email TEXT,
            created_at TEXT
        )
    """)
    # Insert sample data for 'users'
    user_data = [
        ('Alice Smith', 200, 'alice.smith@example.com', '2024-02-01'),
        ('Bob Johnson', 350, 'bob.johnson@example.com', '2024-03-15'),
        ('Charlie Brown', 120, 'charlie.brown@example.com', '2024-04-10'),
        ('Diana Prince', 500, 'diana.prince@example.com', '2024-05-25'),
        ('Eve Adams', 90, 'eve.adams@example.com', '2024-06-18')
    ]
    db_cursor.executemany("""
        INSERT INTO users (name, followers, email, created_at)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS(SELECT 1 FROM users WHERE email = ?)
    """, [(name, followers, email, created_at, email) for name, followers, email, created_at in user_data])

    # Create 'posts' table
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    # Insert sample data for 'posts'
    post_data = [
        (1, 'Hello, this is Alice\'s first post!', '2024-02-02'),
        (2, 'Bob here, loving this platform!', '2024-03-16'),
        (3, 'Charlie posting some cool updates!', '2024-04-11'),
        (4, 'Diana sharing her thoughts.', '2024-05-26'),
        (5, 'Eve posting random stuff.', '2024-06-19')
    ]
    db_cursor.executemany("""
        INSERT INTO posts (user_id, content, created_at)
        SELECT ?, ?, ?
        WHERE NOT EXISTS(SELECT 1 FROM posts WHERE content = ?)
    """, [(user_id, content, created_at, content) for user_id, content, created_at in post_data])

    # Create 'comments' table
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    # Insert sample data for 'comments'
    comment_data = [
        (1, 2, 'Great post, Bob!', '2024-03-17'),
        (2, 3, 'Thanks for the update, Charlie!', '2024-04-12'),
        (3, 4, 'Interesting thoughts, Diana!', '2024-05-27'),
        (4, 5, 'Haha, nice one, Eve!', '2024-06-20'),
        (5, 1, 'Welcome, Alice!', '2024-02-03')
    ]
    db_cursor.executemany("""
        INSERT INTO comments (post_id, user_id, content, created_at)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS(SELECT 1 FROM comments WHERE content = ?)
    """, [(post_id, user_id, content, created_at, content) for post_id, user_id, content, created_at in comment_data])

    # Commit all changes
    db_connection.commit()

initialize_database()

def populate_schema(tree):
    for table, columns in tables.items():
        parent = tree.insert("", "end", text=table, values=(f"({len(columns)} columns)",))
        for column in columns:
            tree.insert(parent, "end", text=column)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "10", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def normalize_column(col_name): # handles the recognition of column names by normalizing variations or synonyms
    for standard_name, variations in synonyms.items():
        if col_name.lower() in variations:
            return standard_name
    return None

def preprocess_where_clause(where_clause): # removing unnecessary words like "the", "is", "are"
    unnecessary_words = ["the", "is", "are"]
    for word in unnecessary_words:
        where_clause = re.sub(rf"\b{word}\b", "", where_clause, flags=re.IGNORECASE)
    return where_clause.strip()

def extract_select_clause(query, table_in_context): # identifies the columns that the user wants to SELECT in their query
    aggregates = {
        "total number": "COUNT",
        "average": "AVG",
        "sum": "SUM",
        "maximum": "MAX",
        "minimum": "MIN"
    }
    match = re.search(r"(show me|give me|list|select) (.*?) (from|where|of|for|on|who|that)", query, re.IGNORECASE)
    if match:
        columns = match.group(2).strip()
        for phrase, agg_func in aggregates.items():
            if phrase in columns.lower():
                return [f"{agg_func}(*)"]
        if columns.lower() in ["all", "everything", "*", f"all {table_in_context}"]:
            return ["*"]
        columns = re.split(r",| and ", columns)
        normalized_columns = [normalize_column(col.strip()) for col in columns]
        if None in normalized_columns:
            return None
        return normalized_columns
    if table_in_context:
        return ["*"]
    return None

def extract_from_clause(query): # determines which table the user is referring to in their query
    normalized_query = query
    for standard_name, variations in synonyms.items():
        for variation in variations:
            normalized_query = re.sub(rf"\b{variation}\b", standard_name, normalized_query, flags=re.IGNORECASE)
    for table in tables.keys():
        if re.search(rf"\b{table}\b", normalized_query, re.IGNORECASE):
            return table
    mentioned_columns = []
    for table, columns in tables.items():
        for column in columns:
            if re.search(rf"\b{column}\b", normalized_query, re.IGNORECASE):
                mentioned_columns.append((table, column))
    if mentioned_columns:
        tables_mentioned = [table for table, column in mentioned_columns]
        if len(set(tables_mentioned)) == 1:
            return tables_mentioned[0]
    return None

def extract_where_clause(query):
    match = re.search(r"(where|who|having|with) (.+)", query, re.IGNORECASE)
    if match:
        print("DEBUG: Extracted WHERE Clause:", match.group(2).strip())  # Debugging
        return match.group(2).strip()
    fallback_match = re.search(r"users who (.+)", query, re.IGNORECASE)
    if fallback_match:
        print("DEBUG: Fallback WHERE Clause:", fallback_match.group(1).strip())  # Debugging
        return fallback_match.group(1).strip()
    return None


def extract_conditions(where_clause):
    cleaned_clause = preprocess_where_clause(where_clause)
    print("DEBUG: Cleaned WHERE Clause:", cleaned_clause)  # Debugging
    condition_parts = re.split(r"\b(and|or)\b", cleaned_clause, flags=re.IGNORECASE)
    conditions = []
    logical_operators = []
    for part in condition_parts:
        part = part.strip()
        print("DEBUG: Condition Part:", part)  # Debugging
        if part.lower() in ["and", "or"]:
            logical_operators.append(part.upper())
        else:
            condition_patterns = [
                (r"([\w\s]+)\s*(greater than|more than|over|after)\s+(\d+)", 
                 lambda col, op_text, val: f"{normalize_column(col.strip())} > {val}"),
                (r"([\w\s]+)\s*(less than|under|below)\s+(\d+)", 
                 lambda col, op_text, val: f"{normalize_column(col.strip())} < {val}"),
                (r"([\w\s]+)\s*(equals|is)\s+['\"]?(.+?)['\"]?", 
                 lambda col, is_equals, val: f"{normalize_column(col.strip())} = '{val}'" if val.isalpha() else f"{normalize_column(col.strip())} = {val}"),
                (r"([\w\s]+)\s*(contains|like)\s+['\"](.+?)['\"]", 
                 lambda col, op_text, substring: f"{normalize_column(col.strip())} LIKE '%{substring}%'"),
                (r"([\w\s]+)\s*between\s+(\d+)\s+and\s+(\d+)", 
                 lambda col, val1, val2: f"{normalize_column(col.strip())} BETWEEN {val1} AND {val2}")
            ]
            for pattern, repl in condition_patterns:
                match = re.search(pattern, part, re.IGNORECASE)
                if match:
                    print("DEBUG: Matched Pattern:", match.groups())  # Debugging
                    col = match.group(1).strip()
                    col = normalize_column(col)
                    if col:
                        condition = repl(col, *match.groups()[1:])
                        print("DEBUG: Generated Condition:", condition)  # Debugging
                        conditions.append(condition)
                        break
    combined_conditions = []
    for i, condition in enumerate(conditions):
        combined_conditions.append(condition)
        if i < len(logical_operators):
            combined_conditions.append(logical_operators[i])
    result = " ".join(combined_conditions) if conditions else None
    print("DEBUG: Combined Conditions:", result)  # Debugging
    return result


def parse_query(query):
    print("DEBUG: Input Query:", query)  # Debugging
    query = query.lower()
    from_clause = extract_from_clause(query)
    print("DEBUG: Extracted FROM Clause:", from_clause)  # Debugging
    select_clause = extract_select_clause(query, from_clause)
    print("DEBUG: Extracted SELECT Clause:", select_clause)  # Debugging
    where_clause = extract_where_clause(query)
    print("DEBUG: Extracted WHERE Clause:", where_clause)  # Debugging
    if not select_clause or None in select_clause:
        return "Error: Could not determine what to SELECT. Please check your query."
    if not from_clause:
        return "Error: Could not determine which table to SELECT FROM. Please check your query."
    sql = f"SELECT {', '.join(select_clause)} FROM {from_clause}"
    if where_clause:
        conditions = extract_conditions(where_clause)
        print("DEBUG: Final Conditions:", conditions)  # Debugging
        if conditions:
            sql += f" WHERE {conditions}"
    print("DEBUG: Final SQL Query:", sql)  # Debugging
    return sql


def parse_query(query): # combines the extracted SELECT, FROM, and WHERE clauses to generate the final SQL query
    query = query.lower()
    from_clause = extract_from_clause(query)
    select_clause = extract_select_clause(query, from_clause)
    where_clause = extract_where_clause(query)
    if not select_clause or None in select_clause:
        return "Error: Could not determine what to SELECT. Please check your query."
    if not from_clause:
        return "Error: Could not determine which table to SELECT FROM. Please check your query."
    sql = f"SELECT {', '.join(select_clause)} FROM {from_clause}"
    if where_clause:
        conditions = extract_conditions(where_clause)
        if conditions:
            sql += f" WHERE {conditions}"
    return sql


def on_generate_sql():
    user_input = query_input.get()
    if not user_input:
        messagebox.showwarning("Input Error", "Please enter a query.")
        return
    sql_query = parse_query(user_input)
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, sql_query)
    output_text.config(state=tk.DISABLED)

    # Store query in history
    if user_input not in query_history:
        query_history.append(user_input)
        update_query_history()

    # Display the results in the results table
    if not sql_query.startswith("Error"):
        display_query_results(sql_query)

def update_query_history():
    query_history_combobox['values'] = query_history
    if query_history:
        query_history_combobox.current(len(query_history) - 1)

def on_query_history_select(event):
    selected_query = query_history_combobox.get()
    query_input.delete(0, tk.END)
    query_input.insert(0, selected_query)


def display_query_results(sql_query):
    try:
        # Execute the SQL query
        db_cursor.execute(sql_query)
        rows = db_cursor.fetchall()
        columns = [description[0] for description in db_cursor.description]

        # Clear existing rows and columns in the results table (if any)
        for item in results_table.get_children():
            results_table.delete(item)
        results_table["columns"] = columns
        results_table["show"] = "headings"

        # Add columns to the results table
        for col in columns:
            results_table.heading(col, text=col)
            results_table.column(col, width=150, anchor="center")

        # Insert rows into the results table
        for row in rows:
            results_table.insert("", "end", values=row)

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")


window = tk.Tk()
window.title("Natural Language to SQL Translator")
window.geometry("800x600")

main_frame = ttk.Frame(window, padding=10)
main_frame.pack(fill="both", expand=True)

schema_frame = ttk.LabelFrame(main_frame, text="Database Schema", padding=10)
schema_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

schema_tree = ttk.Treeview(schema_frame, columns=("Columns",), show="tree")
schema_tree.heading("#0", text="Table / Column")
schema_tree.heading("Columns", text="Details")
schema_tree.column("#0", width=200, anchor="w")
schema_tree.column("Columns", width=150, anchor="center")
populate_schema(schema_tree)
schema_tree.pack(fill="both", expand=True)

query_frame = ttk.LabelFrame(main_frame, text="Query Input", padding=10)
query_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

query_label = ttk.Label(query_frame, text="Enter your Natural Language Query:")
query_label.pack(anchor="w", pady=5)

query_input = ttk.Entry(query_frame, width=80)
query_input.pack(fill="x", pady=5)
ToolTip(query_input, "Type a natural language query, e.g., 'Show me all users with followers more than 100.'")

generate_button = ttk.Button(query_frame, text="Generate SQL", command=on_generate_sql)
generate_button.pack(pady=10)
ToolTip(generate_button, "Click to translate the query into SQL.")

# Query History Dropdown
query_history_label = ttk.Label(query_frame, text="Query History:")
query_history_label.pack(anchor="w", pady=5)

query_history_combobox = ttk.Combobox(query_frame, width=80)
query_history_combobox.bind("<<ComboboxSelected>>", on_query_history_select)
query_history_combobox.pack(fill="x", pady=5)

output_frame = ttk.LabelFrame(main_frame, text="Generated SQL Query", padding=10)
output_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

output_text = tk.Text(output_frame, height=10, wrap="word", state=tk.DISABLED)
output_text.pack(fill="both", expand=True)
ToolTip(output_text, "The SQL query generated from your input will appear here.")

results_frame = ttk.LabelFrame(main_frame, text="Query Results", padding=10)
results_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

results_table = ttk.Treeview(results_frame)
results_table.pack(fill="both", expand=True)

main_frame.rowconfigure(3, weight=2)

main_frame.rowconfigure(0, weight=1)
main_frame.rowconfigure(2, weight=2)
main_frame.columnconfigure(0, weight=1)

window.mainloop()
