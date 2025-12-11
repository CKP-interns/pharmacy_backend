import pdfplumber

def extract_purchase_items_from_pdf(file_path):
    items = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            for row in table:
                # Skip header rows
                if "Item Description" in row[1]:
                    continue

                try:
                    code = row[1]
                    name = row[2]
                    qty = row[5]
                    pack = row[6]
                    batch = row[7]
                    expiry = row[9]
                    mrp = row[10]
                    cost = row[12]
                    net = row[15]

                    items.append({
                        "product_code": code,
                        "name": name,
                        "qty": float(qty or 0),
                        "pack": pack,
                        "batch_no": batch,
                        "expiry": expiry,
                        "mrp": float(mrp or 0),
                        "cost": float(cost or 0),
                        "net_value": float(net or 0),
                    })

                except:
                    continue

    return items


import openpyxl
from decimal import Decimal
import re
import csv

def extract_items_from_csv(path):
    items = []

    # Try to read using normal CSV first
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read()

    # Normalize spacing → convert multiple spaces/tabs into single comma
    normalized = ",".join(
        part for part in lines.replace("\t", " ").split(" ") if part.strip() != ""
    )

    rows = normalized.split("\n")

    if len(rows) < 2:
        return []

    # Parse header
    header = rows[0].split(",")

    # Build index map safely
    idx = {col.strip(): i for i, col in enumerate(header)}

    required_cols = ["ItemName", "InvQty", "SaleRate"]

    for col in required_cols:
        if col not in idx:
            print("Missing column:", col)
            return []   # cannot parse this CSV

    items = []
    for row in rows[1:]:
        if not row.strip():
            continue

        parts = row.split(",")

        try:
            name = parts[idx["ItemName"]].strip().strip('"')
            qty = parts[idx["InvQty"]].strip()
            rate = parts[idx["SaleRate"]].strip()
        except Exception:
            continue

        if name == "":
            continue

        items.append({
            "product_code": "",
            "name": name,
            "qty": qty,
            "rate": rate,
            "net_value": "0",
        })

    return items


def extract_items_from_excel(path):
    """
    Extract purchase items from Excel (.xlsx)
    Expected same columns as CSV.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    # Read header row
    headers = [str(cell.value).strip().lower() for cell in ws[1]]

    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        values = dict(zip(headers, row))

        items.append({
            "product_code": values.get("product_code", ""),
            "name": values.get("name", ""),
            "qty": values.get("qty", "0"),
            "rate": values.get("rate", "0"),
            "net_value": values.get("net_value", "0"),
        })

    return items
