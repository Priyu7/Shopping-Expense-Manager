import csv
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from pathlib import Path


# ============================================================
# APPLICATION SETTINGS
# ============================================================

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "shopping_expense_manager.db"

CATEGORIES = [
    "Groceries",
    "Clothes",
    "Electronics",
    "Food",
    "Travel",
    "Medicine",
    "Home",
    "Education",
    "Entertainment",
    "Other"
]

PAYMENT_METHODS = [
    "UPI",
    "Cash",
    "Debit Card",
    "Credit Card",
    "Net Banking"
]


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            item_name TEXT NOT NULL,

            category TEXT NOT NULL,

            price REAL NOT NULL,

            quantity INTEGER NOT NULL DEFAULT 1,

            payment_method TEXT NOT NULL,

            purchase_date TEXT NOT NULL,

            notes TEXT DEFAULT '',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            setting_name TEXT PRIMARY KEY,

            setting_value TEXT NOT NULL
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO settings
        (setting_name, setting_value)

        VALUES
        ('monthly_budget', '10000')
    """)

    connection.commit()
    connection.close()


# ============================================================
# EXPENSE CRUD OPERATIONS
# ============================================================

def add_expense(
    item_name,
    category,
    price,
    quantity,
    payment_method,
    purchase_date,
    notes
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (
            item_name,
            category,
            price,
            quantity,
            payment_method,
            purchase_date,
            notes
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        item_name,
        category,
        price,
        quantity,
        payment_method,
        purchase_date,
        notes
    ))

    connection.commit()

    connection.close()


def update_expense(
    expense_id,
    item_name,
    category,
    price,
    quantity,
    payment_method,
    purchase_date,
    notes
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE expenses

        SET
            item_name = ?,
            category = ?,
            price = ?,
            quantity = ?,
            payment_method = ?,
            purchase_date = ?,
            notes = ?

        WHERE id = ?
    """, (
        item_name,
        category,
        price,
        quantity,
        payment_method,
        purchase_date,
        notes,
        expense_id
    ))

    connection.commit()

    connection.close()


def delete_expense(expense_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    connection.commit()

    connection.close()


def get_expense(expense_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            price,
            quantity,
            payment_method,
            purchase_date,
            notes

        FROM expenses

        WHERE id = ?
    """, (expense_id,))

    result = cursor.fetchone()

    connection.close()

    return result


def get_expenses(
    search="",
    category="All",
    month="All"
):

    connection = get_connection()

    cursor = connection.cursor()

    query = """
        SELECT
            id,
            item_name,
            category,
            price,
            quantity,
            payment_method,
            purchase_date,
            notes

        FROM expenses

        WHERE 1 = 1
    """

    parameters = []

    # Search
    if search:

        query += """
            AND (
                LOWER(item_name) LIKE ?
                OR LOWER(notes) LIKE ?
            )
        """

        keyword = f"%{search.lower()}%"

        parameters.append(keyword)
        parameters.append(keyword)

    # Category filter
    if category != "All":

        query += """
            AND category = ?
        """

        parameters.append(category)

    # Month filter
    if month != "All":

        query += """
            AND substr(purchase_date, 1, 7) = ?
        """

        parameters.append(month)

    query += """
        ORDER BY
            purchase_date DESC,
            id DESC
    """

    cursor.execute(
        query,
        parameters
    )

    results = cursor.fetchall()

    connection.close()

    return results


# ============================================================
# DASHBOARD DATA
# ============================================================

def get_total_spending(month=None):

    connection = get_connection()

    cursor = connection.cursor()

    if month:

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(price * quantity),
                    0
                )

            FROM expenses

            WHERE substr(
                purchase_date,
                1,
                7
            ) = ?
        """, (month,))

    else:

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(price * quantity),
                    0
                )

            FROM expenses
        """)

    result = cursor.fetchone()[0]

    connection.close()

    return float(result)


def get_total_items(month=None):

    connection = get_connection()

    cursor = connection.cursor()

    if month:

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(quantity),
                    0
                )

            FROM expenses

            WHERE substr(
                purchase_date,
                1,
                7
            ) = ?
        """, (month,))

    else:

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(quantity),
                    0
                )

            FROM expenses
        """)

    result = cursor.fetchone()[0]

    connection.close()

    return int(result)


def get_category_summary(month=None):

    connection = get_connection()

    cursor = connection.cursor()

    if month:

        cursor.execute("""
            SELECT
                category,
                SUM(price * quantity)

            FROM expenses

            WHERE substr(
                purchase_date,
                1,
                7
            ) = ?

            GROUP BY category

            ORDER BY
                SUM(price * quantity) DESC
        """, (month,))

    else:

        cursor.execute("""
            SELECT
                category,
                SUM(price * quantity)

            FROM expenses

            GROUP BY category

            ORDER BY
                SUM(price * quantity) DESC
        """)

    results = cursor.fetchall()

    connection.close()

    return results


def get_monthly_summary():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            substr(purchase_date, 1, 7),
            SUM(price * quantity)

        FROM expenses

        GROUP BY
            substr(purchase_date, 1, 7)

        ORDER BY
            substr(purchase_date, 1, 7) DESC
    """)

    results = cursor.fetchall()

    connection.close()

    return results


# ============================================================
# BUDGET
# ============================================================

def get_budget():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT setting_value

        FROM settings

        WHERE setting_name = 'monthly_budget'
    """)

    result = cursor.fetchone()

    connection.close()

    if result:
        return float(result[0])

    return 10000


def save_budget(value):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE settings

        SET setting_value = ?

        WHERE setting_name = 'monthly_budget'
    """, (str(value),))

    connection.commit()

    connection.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_money(amount):

    return f"₹{amount:,.2f}"


def current_month():

    return date.today().strftime("%Y-%m")


def format_month(month):

    try:

        return datetime.strptime(
            month,
            "%Y-%m"
        ).strftime("%B %Y")

    except:

        return month


def valid_date(value):

    try:

        datetime.strptime(
            value,
            "%Y-%m-%d"
        )

        return True

    except:

        return False


# ============================================================
# MAIN APPLICATION
# ============================================================

class ShoppingExpenseManager(tk.Tk):

    BACKGROUND = "#f3f6fb"

    CARD = "#ffffff"

    SIDEBAR = "#111827"

    SIDEBAR_ACTIVE = "#2563eb"

    TEXT = "#172033"

    MUTED = "#6b7280"

    BORDER = "#e5e7eb"

    BLUE = "#2563eb"

    GREEN = "#059669"

    RED = "#dc2626"

    ORANGE = "#d97706"


    def __init__(self):

        super().__init__()

        self.title(
            "Shopping Expense Manager"
        )

        self.geometry(
            "1250x760"
        )

        self.minsize(
            1000,
            650
        )

        self.configure(
            bg=self.BACKGROUND
        )

        self.current_page = "dashboard"

        self.setup_styles()

        self.create_layout()

        self.show_dashboard()


    # ========================================================
    # STYLE
    # ========================================================

    def setup_styles(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except:
            pass

        style.configure(
            "TButton",

            font=(
                "Segoe UI",
                10,
                "bold"
            ),

            padding=(
                12,
                8
            )
        )

        style.configure(
            "TEntry",

            padding=8
        )

        style.configure(
            "TCombobox",

            padding=7
        )

        style.configure(
            "Treeview",

            rowheight=34,

            font=(
                "Segoe UI",
                10
            )
        )

        style.configure(
            "Treeview.Heading",

            font=(
                "Segoe UI",
                10,
                "bold"
            ),

            padding=8
        )


    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    def create_layout(self):

        # Sidebar
        self.sidebar = tk.Frame(

            self,

            bg=self.SIDEBAR,

            width=235
        )

        self.sidebar.pack(

            side="left",

            fill="y"
        )

        self.sidebar.pack_propagate(
            False
        )


        # Logo
        tk.Label(

            self.sidebar,

            text="SHOPPING",

            bg=self.SIDEBAR,

            fg="white",

            font=(
                "Segoe UI",
                21,
                "bold"
            )

        ).pack(

            anchor="w",

            padx=25,

            pady=(30, 0)
        )


        tk.Label(

            self.sidebar,

            text="EXPENSE MANAGER",

            bg=self.SIDEBAR,

            fg="#9ca3af",

            font=(
                "Segoe UI",
                9,
                "bold"
            )

        ).pack(

            anchor="w",

            padx=25,

            pady=(2, 30)
        )


        # Navigation buttons
        self.dashboard_button = self.create_nav_button(
            "⌂   Dashboard",
            self.show_dashboard
        )

        self.expenses_button = self.create_nav_button(
            "▣   Expenses",
            self.show_expenses
        )

        self.add_button = self.create_nav_button(
            "＋   Add Expense",
            self.open_add_expense
        )

        self.reports_button = self.create_nav_button(
            "▥   Reports",
            self.show_reports
        )


        # Spacer
        tk.Frame(

            self.sidebar,

            bg=self.SIDEBAR

        ).pack(

            fill="both",

            expand=True
        )


        # Budget
        self.create_nav_button(
            "⚙   Monthly Budget",
            self.open_budget
        )


        tk.Label(

            self.sidebar,

            text="Shopping Expense Manager\nVersion 1.0",

            bg=self.SIDEBAR,

            fg="#6b7280",

            font=(
                "Segoe UI",
                9
            )

        ).pack(

            pady=20
        )


        # Main Content
        self.content = tk.Frame(

            self,

            bg=self.BACKGROUND
        )

        self.content.pack(

            side="right",

            fill="both",

            expand=True
        )


    # ========================================================
    # NAVIGATION BUTTON
    # ========================================================

    def create_nav_button(
        self,
        text,
        command
    ):

        button = tk.Button(

            self.sidebar,

            text=text,

            command=command,

            anchor="w",

            padx=22,

            pady=14,

            relief="flat",

            borderwidth=0,

            bg=self.SIDEBAR,

            fg="#d1d5db",

            activebackground="#1f2937",

            activeforeground="white",

            font=(
                "Segoe UI",
                11,
                "bold"
            ),

            cursor="hand2"
        )

        button.pack(

            fill="x",

            padx=10,

            pady=2
        )

        return button


    def set_active(
        self,
        active_button
    ):

        buttons = [
            self.dashboard_button,
            self.expenses_button,
            self.add_button,
            self.reports_button
        ]

        for button in buttons:

            button.configure(

                bg=(
                    self.SIDEBAR_ACTIVE

                    if button == active_button

                    else self.SIDEBAR
                ),

                fg=(
                    "white"

                    if button == active_button

                    else "#d1d5db"
                )
            )


    # ========================================================
    # CLEAR PAGE
    # ========================================================

    def clear_content(self):

        for widget in self.content.winfo_children():

            widget.destroy()


    # ========================================================
    # PAGE TITLE
    # ========================================================

    def page_title(
        self,
        title,
        subtitle=""
    ):

        frame = tk.Frame(

            self.content,

            bg=self.BACKGROUND
        )

        frame.pack(

            fill="x",

            padx=30,

            pady=(25, 15)
        )


        tk.Label(

            frame,

            text=title,

            bg=self.BACKGROUND,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                25,
                "bold"
            )

        ).pack(

            anchor="w"
        )


        if subtitle:

            tk.Label(

                frame,

                text=subtitle,

                bg=self.BACKGROUND,

                fg=self.MUTED,

                font=(
                    "Segoe UI",
                    10
                )

            ).pack(

                anchor="w",

                pady=(4, 0)
            )


    # ========================================================
    # DASHBOARD
    # ========================================================

    def show_dashboard(self):

        self.current_page = "dashboard"

        self.set_active(
            self.dashboard_button
        )

        self.clear_content()

        self.page_title(

            "Dashboard",

            f"Overview for {format_month(current_month())}"
        )


        month = current_month()

        spending = get_total_spending(
            month
        )

        items = get_total_items(
            month
        )

        budget = get_budget()

        remaining = budget - spending


        # Cards
        cards = tk.Frame(

            self.content,

            bg=self.BACKGROUND
        )

        cards.pack(

            fill="x",

            padx=24
        )


        self.create_card(

            cards,

            "MONTHLY SPENDING",

            format_money(spending),

            self.BLUE
        )


        self.create_card(

            cards,

            "ITEMS PURCHASED",

            str(items),

            self.GREEN
        )


        self.create_card(

            cards,

            "MONTHLY BUDGET",

            format_money(budget),

            self.ORANGE
        )


        self.create_card(

            cards,

            "REMAINING",

            format_money(
                max(remaining, 0)
            ),

            self.GREEN

            if remaining >= 0

            else self.RED
        )


        # Lower section
        lower = tk.Frame(

            self.content,

            bg=self.BACKGROUND
        )

        lower.pack(

            fill="both",

            expand=True,

            padx=30,

            pady=22
        )


        # Category section
        category_card = tk.Frame(

            lower,

            bg=self.CARD,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )

        category_card.pack(

            side="left",

            fill="both",

            expand=True,

            padx=(0, 10)
        )


        tk.Label(

            category_card,

            text="Category-wise Spending",

            bg=self.CARD,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                15,
                "bold"
            )

        ).pack(

            anchor="w",

            padx=20,

            pady=18
        )


        chart = tk.Canvas(

            category_card,

            bg=self.CARD,

            highlightthickness=0
        )

        chart.pack(

            fill="both",

            expand=True,

            padx=15,

            pady=5
        )


        self.draw_chart(

            chart,

            get_category_summary(month)
        )


        # Recent expenses
        recent_card = tk.Frame(

            lower,

            bg=self.CARD,

            width=370,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )

        recent_card.pack(

            side="right",

            fill="y",

            padx=(10, 0)
        )

        recent_card.pack_propagate(
            False
        )


        tk.Label(

            recent_card,

            text="Recent Expenses",

            bg=self.CARD,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                15,
                "bold"
            )

        ).pack(

            anchor="w",

            padx=20,

            pady=18
        )


        rows = get_expenses(
            month=month
        )[:7]


        if not rows:

            tk.Label(

                recent_card,

                text="No expenses this month.\n\nClick '+ Add Expense'\nto add your first purchase.",

                bg=self.CARD,

                fg=self.MUTED,

                font=(
                    "Segoe UI",
                    10
                ),

                justify="left"
            ).pack(

                anchor="w",

                padx=20
            )

        else:

            for row in rows:

                item_frame = tk.Frame(

                    recent_card,

                    bg=self.CARD
                )

                item_frame.pack(

                    fill="x",

                    padx=20,

                    pady=7
                )


                tk.Label(

                    item_frame,

                    text=row[1],

                    bg=self.CARD,

                    fg=self.TEXT,

                    font=(
                        "Segoe UI",
                        10,
                        "bold"
                    )

                ).pack(

                    side="left"
                )


                tk.Label(

                    item_frame,

                    text=format_money(
                        row[3] * row[4]
                    ),

                    bg=self.CARD,

                    fg=self.TEXT,

                    font=(
                        "Segoe UI",
                        10,
                        "bold"
                    )

                ).pack(

                    side="right"
                )


                tk.Label(

                    item_frame,

                    text=row[2],

                    bg=self.CARD,

                    fg=self.MUTED,

                    font=(
                        "Segoe UI",
                        8
                    )

                ).pack(

                    side="left",

                    padx=8
                )


        # Budget warning
        if spending > budget:

            tk.Label(

                self.content,

                text=(
                    f"⚠ Budget exceeded by "
                    f"{format_money(spending - budget)}"
                ),

                bg="#fee2e2",

                fg=self.RED,

                font=(
                    "Segoe UI",
                    10,
                    "bold"
                ),

                pady=8
            ).pack(

                fill="x",

                padx=30,

                pady=(0, 15)
            )


    # ========================================================
    # DASHBOARD CARD
    # ========================================================

    def create_card(

        self,
        parent,
        title,
        value,
        accent
    ):

        card = tk.Frame(

            parent,

            bg=self.CARD,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )

        card.pack(

            side="left",

            fill="both",

            expand=True,

            padx=6
        )


        tk.Frame(

            card,

            bg=accent,

            width=5
        ).pack(

            side="left",

            fill="y"
        )


        body = tk.Frame(

            card,

            bg=self.CARD
        )

        body.pack(

            side="left",

            fill="both",

            expand=True,

            padx=17,

            pady=16
        )


        tk.Label(

            body,

            text=title,

            bg=self.CARD,

            fg=self.MUTED,

            font=(
                "Segoe UI",
                10,
                "bold"
            )

        ).pack(

            anchor="w"
        )


        tk.Label(

            body,

            text=value,

            bg=self.CARD,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                20,
                "bold"
            )

        ).pack(

            anchor="w",

            pady=(6, 0)
        )


    # ========================================================
    # CHART
    # ========================================================

    def draw_chart(

        self,
        canvas,
        data
    ):

        canvas.delete(
            "all"
        )


        if not data:

            canvas.create_text(

                250,

                120,

                text="No expense data available",

                fill=self.MUTED,

                font=(
                    "Segoe UI",
                    11
                )
            )

            return


        maximum = max(

            amount

            for category, amount

            in data
        )


        y = 25


        for category, amount in data[:8]:

            canvas.create_text(

                10,

                y + 9,

                text=category,

                anchor="w",

                fill=self.TEXT,

                font=(
                    "Segoe UI",
                    9,
                    "bold"
                )
            )


            canvas.create_rectangle(

                125,

                y,

                400,

                y + 18,

                fill="#e5e7eb",

                outline=""
            )


            width = max(

                8,

                int(
                    275 * amount / maximum
                )
            )


            canvas.create_rectangle(

                125,

                y,

                125 + width,

                y + 18,

                fill=self.BLUE,

                outline=""
            )


            canvas.create_text(

                410,

                y + 9,

                text=format_money(amount),

                anchor="w",

                fill=self.TEXT,

                font=(
                    "Segoe UI",
                    9
                )
            )


            y += 38


    # ========================================================
    # EXPENSE PAGE
    # ========================================================

    def show_expenses(self):

        self.current_page = "expenses"

        self.set_active(
            self.expenses_button
        )

        self.clear_content()

        self.page_title(

            "Expenses",

            "Manage all your shopping expenses."
        )


        # Filter section
        filters = tk.Frame(

            self.content,

            bg=self.CARD,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )

        filters.pack(

            fill="x",

            padx=30,

            pady=(0, 12)
        )


        # Search
        tk.Label(

            filters,

            text="Search",

            bg=self.CARD,

            fg=self.MUTED,

            font=(
                "Segoe UI",
                9,
                "bold"
            )

        ).pack(

            side="left",

            padx=(15, 6)
        )


        self.search_var = tk.StringVar()


        search_entry = ttk.Entry(

            filters,

            textvariable=self.search_var,

            width=25
        )

        search_entry.pack(

            side="left",

            pady=12
        )


        search_entry.bind(

            "<KeyRelease>",

            lambda event:
                self.refresh_expense_table()
        )


        # Category
        tk.Label(

            filters,

            text="Category",

            bg=self.CARD,

            fg=self.MUTED,

            font=(
                "Segoe UI",
                9,
                "bold"
            )

        ).pack(

            side="left",

            padx=(15, 6)
        )


        self.category_var = tk.StringVar(
            value="All"
        )


        category_combo = ttk.Combobox(

            filters,

            textvariable=self.category_var,

            values=[
                "All"
            ] + CATEGORIES,

            state="readonly",

            width=16
        )

        category_combo.pack(

            side="left",

            pady=12
        )


        category_combo.bind(

            "<<ComboboxSelected>>",

            lambda event:
                self.refresh_expense_table()
        )


        # Month
        tk.Label(

            filters,

            text="Month",

            bg=self.CARD,

            fg=self.MUTED,

            font=(
                "Segoe UI",
                9,
                "bold"
            )

        ).pack(

            side="left",

            padx=(15, 6)
        )


        self.month_var = tk.StringVar(
            value="All"
        )


        months = [

            "All"

        ] + [

            month

            for month, total

            in get_monthly_summary()
        ]


        month_combo = ttk.Combobox(

            filters,

            textvariable=self.month_var,

            values=months,

            state="readonly",

            width=13
        )


        month_combo.pack(

            side="left",

            pady=12
        )


        month_combo.bind(

            "<<ComboboxSelected>>",

            lambda event:
                self.refresh_expense_table()
        )


        # Add button
        ttk.Button(

            filters,

            text="＋ Add Expense",

            command=self.open_add_expense

        ).pack(

            side="right",

            padx=15
        )


        # Table
        table_card = tk.Frame(

            self.content,

            bg=self.CARD,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )


        table_card.pack(

            fill="both",

            expand=True,

            padx=30,

            pady=(0, 10)
        )


        columns = (

            "id",

            "item",

            "category",

            "price",

            "quantity",

            "total",

            "payment",

            "date"
        )


        self.expense_tree = ttk.Treeview(

            table_card,

            columns=columns,

            show="headings"
        )


        headings = {

            "id": "ID",

            "item": "Item",

            "category": "Category",

            "price": "Price",

            "quantity": "Qty",

            "total": "Total",

            "payment": "Payment",

            "date": "Date"
        }


        widths = {

            "id": 50,

            "item": 180,

            "category": 120,

            "price": 90,

            "quantity": 60,

            "total": 100,

            "payment": 110,

            "date": 110
        }


        for column in columns:

            self.expense_tree.heading(

                column,

                text=headings[column]
            )

            self.expense_tree.column(

                column,

                width=widths[column],

                anchor="center"
            )


        self.expense_tree.column(

            "item",

            anchor="w"
        )


        scrollbar = ttk.Scrollbar(

            table_card,

            orient="vertical",

            command=self.expense_tree.yview
        )


        self.expense_tree.configure(

            yscrollcommand=scrollbar.set
        )


        self.expense_tree.pack(

            side="left",

            fill="both",

            expand=True
        )


        scrollbar.pack(

            side="right",

            fill="y"
        )


        self.expense_tree.bind(

            "<Double-1>",

            lambda event:
                self.edit_selected()
        )


        # Action buttons
        actions = tk.Frame(

            self.content,

            bg=self.BACKGROUND
        )


        actions.pack(

            fill="x",

            padx=30,

            pady=(0, 18)
        )


        ttk.Button(

            actions,

            text="✎ Edit Selected",

            command=self.edit_selected

        ).pack(

            side="left"
        )


        ttk.Button(

            actions,

            text="✕ Delete Selected",

            command=self.delete_selected

        ).pack(

            side="left",

            padx=8
        )


        ttk.Button(

            actions,

            text="⇩ Export CSV",

            command=self.export_csv

        ).pack(

            side="right"
        )


        self.refresh_expense_table()


    # ========================================================
    # REFRESH TABLE
    # ========================================================

    def refresh_expense_table(self):

        if not hasattr(
            self,
            "expense_tree"
        ):

            return


        for item in self.expense_tree.get_children():

            self.expense_tree.delete(
                item
            )


        rows = get_expenses(

            self.search_var.get(),

            self.category_var.get(),

            self.month_var.get()
        )


        for row in rows:

            self.expense_tree.insert(

                "",

                "end",

                values=(

                    row[0],

                    row[1],

                    row[2],

                    format_money(row[3]),

                    row[4],

                    format_money(
                        row[3] * row[4]
                    ),

                    row[5],

                    row[6]
                )
            )


    # ========================================================
    # GET SELECTED ID
    # ========================================================

    def get_selected_id(self):

        selected = self.expense_tree.selection()


        if not selected:

            messagebox.showwarning(

                "Select Expense",

                "Please select an expense first."
            )

            return None


        values = self.expense_tree.item(

            selected[0],

            "values"
        )


        return int(values[0])


    # ========================================================
    # ADD EXPENSE
    # ========================================================

    def open_add_expense(self):

        self.set_active(
            self.add_button
        )

        self.open_expense_form()


    # ========================================================
    # EXPENSE FORM
    # ========================================================

    def open_expense_form(
        self,
        expense=None
    ):

        window = tk.Toplevel(
            self
        )


        window.title(

            "Edit Shopping Expense"

            if expense

            else "Add Shopping Expense"
        )


        window.geometry(
            "570x700"
        )


        window.minsize(
            500,
            560
        )


        window.configure(
            bg=self.BACKGROUND
        )


        window.transient(
            self
        )


        # Header
        header = tk.Frame(

            window,

            bg=self.BACKGROUND
        )


        header.pack(

            fill="x",

            padx=25,

            pady=(22, 8)
        )


        tk.Label(

            header,

            text=(

                "Edit Shopping Expense"

                if expense

                else "Add Shopping Expense"
            ),

            bg=self.BACKGROUND,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                21,
                "bold"
            )

        ).pack(

            anchor="w"
        )


        tk.Label(

            header,

            text="Enter your shopping details below.",

            bg=self.BACKGROUND,

            fg=self.MUTED,

            font=(
                "Segoe UI",
                9
            )

        ).pack(

            anchor="w",

            pady=(3, 0)
        )


        # Scrollable area
        container = tk.Frame(

            window,

            bg=self.BACKGROUND
        )


        container.pack(

            fill="both",

            expand=True,

            padx=25,

            pady=5
        )


        canvas = tk.Canvas(

            container,

            bg=self.BACKGROUND,

            highlightthickness=0
        )


        scrollbar = ttk.Scrollbar(

            container,

            orient="vertical",

            command=canvas.yview
        )


        canvas.configure(

            yscrollcommand=scrollbar.set
        )


        canvas.pack(

            side="left",

            fill="both",

            expand=True
        )


        scrollbar.pack(

            side="right",

            fill="y"
        )


        form = tk.Frame(

            canvas,

            bg=self.CARD,

            padx=30,

            pady=25
        )


        canvas_window = canvas.create_window(

            (0, 0),

            window=form,

            anchor="nw"
        )


        def resize_form(event):

            canvas.itemconfigure(

                canvas_window,

                width=event.width
            )


        def update_scroll(event=None):

            canvas.configure(

                scrollregion=canvas.bbox(
                    "all"
                )
            )


        canvas.bind(

            "<Configure>",

            resize_form
        )


        form.bind(

            "<Configure>",

            update_scroll
        )


        def mouse_wheel(event):

            canvas.yview_scroll(

                int(
                    -1 * (
                        event.delta / 120
                    )
                ),

                "units"
            )


        canvas.bind(

            "<Enter>",

            lambda event:
                canvas.bind_all(
                    "<MouseWheel>",
                    mouse_wheel
                )
        )


        canvas.bind(

            "<Leave>",

            lambda event:
                canvas.unbind_all(
                    "<MouseWheel>"
                )
        )


        # ====================================================
        # FORM FIELD HELPER
        # ====================================================

        def create_label(text):

            tk.Label(

                form,

                text=text,

                bg=self.CARD,

                fg=self.TEXT,

                font=(
                    "Segoe UI",
                    10,
                    "bold"
                )

            ).pack(

                anchor="w",

                pady=(0, 5)
            )


        # Item
        create_label(
            "Item Name *"
        )


        item_entry = ttk.Entry(
            form
        )


        item_entry.pack(

            fill="x",

            pady=(0, 18)
        )


        # Category
        create_label(
            "Category *"
        )


        category_combo = ttk.Combobox(

            form,

            values=CATEGORIES,

            state="readonly"
        )


        category_combo.pack(

            fill="x",

            pady=(0, 18)
        )


        category_combo.set(
            "Groceries"
        )


        # Price
        create_label(
            "Price per Item (₹) *"
        )


        price_entry = ttk.Entry(
            form
        )


        price_entry.pack(

            fill="x",

            pady=(0, 18)
        )


        # Quantity
        create_label(
            "Quantity *"
        )


        quantity_entry = ttk.Entry(
            form
        )


        quantity_entry.pack(

            fill="x",

            pady=(0, 18)
        )


        quantity_entry.insert(
            0,
            "1"
        )


        # Payment
        create_label(
            "Payment Method *"
        )


        payment_combo = ttk.Combobox(

            form,

            values=PAYMENT_METHODS,

            state="readonly"
        )


        payment_combo.pack(

            fill="x",

            pady=(0, 18)
        )


        payment_combo.set(
            "UPI"
        )


        # Date
        create_label(
            "Purchase Date (YYYY-MM-DD) *"
        )


        date_entry = ttk.Entry(
            form
        )


        date_entry.pack(

            fill="x",

            pady=(0, 18)
        )


        date_entry.insert(

            0,

            date.today().strftime(
                "%Y-%m-%d"
            )
        )


        # Notes
        create_label(
            "Notes"
        )


        notes_text = tk.Text(

            form,

            height=5,

            font=(
                "Segoe UI",
                10
            ),

            relief="solid",

            borderwidth=1
        )


        notes_text.pack(

            fill="x",

            pady=(0, 20)
        )


        # ====================================================
        # LOAD DATA WHEN EDITING
        # ====================================================

        if expense:

            (

                expense_id,

                item,

                category,

                price,

                quantity,

                payment,

                purchase_date,

                notes

            ) = expense


            item_entry.insert(
                0,
                item
            )


            category_combo.set(
                category
            )


            price_entry.insert(

                0,

                str(price)
            )


            quantity_entry.delete(
                0,
                tk.END
            )


            quantity_entry.insert(

                0,

                str(quantity)
            )


            payment_combo.set(
                payment
            )


            date_entry.delete(
                0,
                tk.END
            )


            date_entry.insert(

                0,

                purchase_date
            )


            notes_text.insert(

                "1.0",

                notes or ""
            )


        # ====================================================
        # SAVE FUNCTION
        # ====================================================

        def save():

            item = item_entry.get().strip()

            category = category_combo.get()

            price = price_entry.get().strip()

            quantity = quantity_entry.get().strip()

            payment = payment_combo.get()

            purchase_date = date_entry.get().strip()

            notes = notes_text.get(
                "1.0",
                "end"
            ).strip()


            # Item validation
            if not item:

                messagebox.showerror(

                    "Validation Error",

                    "Please enter item name.",

                    parent=window
                )

                return


            # Price validation
            try:

                price = float(price)

                if price < 0:

                    raise ValueError

            except ValueError:

                messagebox.showerror(

                    "Validation Error",

                    "Please enter a valid price.",

                    parent=window
                )

                return


            # Quantity validation
            try:

                quantity = int(quantity)

                if quantity <= 0:

                    raise ValueError

            except ValueError:

                messagebox.showerror(

                    "Validation Error",

                    "Quantity must be a positive number.",

                    parent=window
                )

                return


            # Date validation
            if not valid_date(
                purchase_date
            ):

                messagebox.showerror(

                    "Validation Error",

                    "Date must be in YYYY-MM-DD format.",

                    parent=window
                )

                return


            if expense:

                update_expense(

                    expense[0],

                    item,

                    category,

                    price,

                    quantity,

                    payment,

                    purchase_date,

                    notes
                )


                message = (
                    "Expense updated successfully."
                )

            else:

                add_expense(

                    item,

                    category,

                    price,

                    quantity,

                    payment,

                    purchase_date,

                    notes
                )


                message = (
                    "Expense added successfully."
                )


            canvas.unbind_all(
                "<MouseWheel>"
            )


            window.destroy()


            messagebox.showinfo(

                "Success",

                message
            )


            if self.current_page == "expenses":

                self.refresh_expense_table()

            elif self.current_page == "dashboard":

                self.show_dashboard()

            elif self.current_page == "reports":

                self.show_reports()


        # ====================================================
        # FORM BUTTONS
        # ====================================================

        footer = tk.Frame(

            window,

            bg=self.BACKGROUND
        )


        footer.pack(

            fill="x",

            padx=25,

            pady=(5, 20)
        )


        tk.Button(

            footer,

            text="Cancel",

            command=lambda: window.destroy(),

            bg="#e5e7eb",

            fg=self.TEXT,

            relief="flat",

            font=(
                "Segoe UI",
                10,
                "bold"
            ),

            padx=20,

            pady=10,

            cursor="hand2"

        ).pack(

            side="right"
        )


        tk.Button(

            footer,

            text=(

                "Update Expense"

                if expense

                else "Save Expense"
            ),

            command=save,

            bg=self.BLUE,

            fg="white",

            activebackground="#1d4ed8",

            activeforeground="white",

            relief="flat",

            font=(
                "Segoe UI",
                10,
                "bold"
            ),

            padx=20,

            pady=10,

            cursor="hand2"

        ).pack(

            side="right",

            padx=(0, 10)
        )


        item_entry.focus()


    # ========================================================
    # EDIT
    # ========================================================

    def edit_selected(self):

        expense_id = self.get_selected_id()


        if expense_id is None:

            return


        expense = get_expense(
            expense_id
        )


        if expense:

            self.open_expense_form(
                expense
            )


    # ========================================================
    # DELETE
    # ========================================================

    def delete_selected(self):

        expense_id = self.get_selected_id()


        if expense_id is None:

            return


        confirm = messagebox.askyesno(

            "Delete Expense",

            "Are you sure you want to delete this expense?"
        )


        if confirm:

            delete_expense(
                expense_id
            )


            self.refresh_expense_table()


            messagebox.showinfo(

                "Deleted",

                "Expense deleted successfully."
            )


    # ========================================================
    # CSV EXPORT
    # ========================================================

    def export_csv(self):

        rows = get_expenses(

            self.search_var.get(),

            self.category_var.get(),

            self.month_var.get()
        )


        if not rows:

            messagebox.showinfo(

                "Export",

                "There are no expenses to export."
            )

            return


        file_path = filedialog.asksaveasfilename(

            title="Save Expense Report",

            defaultextension=".csv",

            filetypes=[
                (
                    "CSV Files",
                    "*.csv"
                )
            ]
        )


        if not file_path:

            return


        with open(

            file_path,

            "w",

            newline="",

            encoding="utf-8-sig"

        ) as file:

            writer = csv.writer(
                file
            )


            writer.writerow([

                "ID",

                "Item",

                "Category",

                "Price",

                "Quantity",

                "Total",

                "Payment Method",

                "Purchase Date",

                "Notes"
            ])


            for row in rows:

                writer.writerow([

                    row[0],

                    row[1],

                    row[2],

                    row[3],

                    row[4],

                    row[3] * row[4],

                    row[5],

                    row[6],

                    row[7]
                ])


        messagebox.showinfo(

            "Export Complete",

            f"Expense report saved successfully:\n\n{file_path}"
        )


    # ========================================================
    # REPORTS
    # ========================================================

    def show_reports(self):

        self.current_page = "reports"

        self.set_active(
            self.reports_button
        )

        self.clear_content()


        self.page_title(

            "Reports & Analytics",

            "Analyze your shopping expenses."
        )


        main = tk.Frame(

            self.content,

            bg=self.BACKGROUND
        )


        main.pack(

            fill="both",

            expand=True,

            padx=30,

            pady=(0, 25)
        )


        # Category chart
        left = tk.Frame(

            main,

            bg=self.CARD,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )


        left.pack(

            side="left",

            fill="both",

            expand=True,

            padx=(0, 10)
        )


        tk.Label(

            left,

            text="Category Breakdown",

            bg=self.CARD,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                15,
                "bold"
            )

        ).pack(

            anchor="w",

            padx=20,

            pady=18
        )


        chart = tk.Canvas(

            left,

            bg=self.CARD,

            highlightthickness=0
        )


        chart.pack(

            fill="both",

            expand=True,

            padx=15,

            pady=5
        )


        self.draw_chart(

            chart,

            get_category_summary()
        )


        # Monthly table
        right = tk.Frame(

            main,

            bg=self.CARD,

            width=420,

            highlightbackground=self.BORDER,

            highlightthickness=1
        )


        right.pack(

            side="right",

            fill="y",

            padx=(10, 0)
        )


        right.pack_propagate(
            False
        )


        tk.Label(

            right,

            text="Monthly Summary",

            bg=self.CARD,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                15,
                "bold"
            )

        ).pack(

            anchor="w",

            padx=20,

            pady=18
        )


        tree = ttk.Treeview(

            right,

            columns=(
                "month",
                "total"
            ),

            show="headings"
        )


        tree.heading(

            "month",

            text="Month"
        )


        tree.heading(

            "total",

            text="Spending"
        )


        tree.column(

            "month",

            width=170
        )


        tree.column(

            "total",

            width=170,

            anchor="e"
        )


        tree.pack(

            fill="both",

            expand=True,

            padx=15,

            pady=(0, 15)
        )


        for month, total in get_monthly_summary():

            tree.insert(

                "",

                "end",

                values=(

                    format_month(month),

                    format_money(total)
                )
            )


    # ========================================================
    # MONTHLY BUDGET
    # ========================================================

    def open_budget(self):

        window = tk.Toplevel(
            self
        )


        window.title(
            "Monthly Budget"
        )


        window.geometry(
            "420x280"
        )


        window.resizable(
            False,
            False
        )


        window.configure(
            bg=self.BACKGROUND
        )


        window.transient(
            self
        )


        tk.Label(

            window,

            text="Monthly Budget",

            bg=self.BACKGROUND,

            fg=self.TEXT,

            font=(
                "Segoe UI",
                20,
                "bold"
            )

        ).pack(

            pady=(30, 5)
        )


        tk.Label(

            window,

            text="Set your monthly shopping limit.",

            bg=self.BACKGROUND,

            fg=self.MUTED,

            font=(
                "Segoe UI",
                9
            )

        ).pack()


        budget_entry = ttk.Entry(

            window,

            justify="center",

            font=(
                "Segoe UI",
                12
            )
        )


        budget_entry.pack(

            fill="x",

            padx=55,

            pady=25
        )


        budget_entry.insert(

            0,

            str(
                get_budget()
            )
        )


        def save():

            try:

                value = float(
                    budget_entry.get()
                )


                if value <= 0:

                    raise ValueError

            except ValueError:

                messagebox.showerror(

                    "Validation",

                    "Please enter a valid positive budget.",

                    parent=window
                )

                return


            save_budget(
                value
            )


            window.destroy()


            if self.current_page == "dashboard":

                self.show_dashboard()


            messagebox.showinfo(

                "Budget Saved",

                f"Monthly budget set to {format_money(value)}."
            )


        tk.Button(

            window,

            text="Save Budget",

            command=save,

            bg=self.BLUE,

            fg="white",

            activebackground="#1d4ed8",

            activeforeground="white",

            relief="flat",

            font=(
                "Segoe UI",
                10,
                "bold"
            ),

            padx=25,

            pady=10,

            cursor="hand2"

        ).pack()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    initialize_database()

    application = ShoppingExpenseManager()

    application.mainloop()