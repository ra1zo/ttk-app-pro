# parse_pdf.py
import sys
from PyPDF2 import PdfReader
import re  #regular expression module
import csv
from io import StringIO
import os
import json
from datetime import datetime


    
def preprocess_text(text):
    # Remove newline and tab characters
    text = text.replace('\n', ' ').replace('\t', ' ')
    # Insert space between words and numbers (e.g., "Recovery4.24" -> "Recovery 4.24")
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    # Insert space between numbers and words (e.g., "998599Collection" -> "998599 Collection")
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    # Remove any extra spaces created by previous replacements
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_table_objects_icn(pdf_path,filename,state_data):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    formatted_text = preprocess_text(text)
    # print(formatted_text)
    # return 0
    table_objects = []    

    pattern = r"([A-Za-z ]+?)\s*BILLED FROM:"

    match = re.search(pattern, text, re.DOTALL)    

    if match:
        #status could be DEBITNOTE or CREDITNOTE
        status_try = match.group(1) 

        # Check if the first character is followed by an uppercase letter
        if len(status_try) > 1 and status_try[1].isupper():
            status = status_try[1:]
        else:
            status = status_try
    else:
        print("Status Error")

    #it takes last words till space = r"Note #:\s*(\S+) and storing 
    credit_note_pattern = re.compile(rf'{status.split()[-1].title() } #:\s*(\S+)')
    invoice_date_pattern = re.compile(rf'{status.split()[-1].title() } Date:\s*(\d{{2}}-\d{{2}}-\d{{4}})')
    #state_code_pattern = re.compile(r'Place of Supply/State Code:\s*([\w\s]+?),\s*(IN-\w+)') #output IN-KA-KARNATAKA
    state_code_pattern = re.compile(r'Place of Supply/State Code:\s*([\w\s]+?),\s*IN-(\w+)') 
      

    # Search for matches in the text
    credit_note_match = credit_note_pattern.search(text)
    invoice_date_match = invoice_date_pattern.search(text)
    state_code_match = state_code_pattern.search(text)

    # Process the matches
    credit_note_number = credit_note_match.group(1) if credit_note_match else 'Unknown'
    invoice_date = datetime.strptime(invoice_date_match.group(1), '%d-%m-%Y').strftime('%Y%m%d') if invoice_date_match else 'Unknown'
    if state_code_match:
        state_name = state_code_match.group(1).strip()  # Clean up the state name
        state_code_suffix = state_code_match.group(2)  # Capture only the suffix part of the state code
        state_code = f"{state_code_suffix}-{state_name}"
    else:
        state_code = 'Unknown'
    #state_code = f"{state_code_match.group(2)}-{state_code_match.group(1)}" if state_code_match else 'Unknown'
    posting_date = datetime.now().strftime('%Y%m%d')
    # Pattern to match individual fee items
    pattern = re.compile(r"Net Amount 1(.*?)\s(\d+\.\d{1,2})", re.DOTALL) #has to be change dynamically
    # Pattern to match the Total row
    total_pattern = re.compile(r"Total\s+(\d+\.\d+)")


    gst_type = 'SGST-9'
    vendor_code="NA"

    for match in pattern.finditer(formatted_text):
        description, net_value = match.groups()

        gst_type_text = gst_type.split('-')[0]
        if state_name in state_data:
            for state_info in state_data[state_name]:
                if gst_type_text.endswith(state_info["GSTType"].split('/')[-1]):
                    vendor_code = state_info["VendorCode"]
                    break

        #storing inside dictionary which inside a list 
        table_objects.append({
            "Vendor": vendor_code,
            "Transaction Type": "CR",
            "Settlement ID": credit_note_number,
            "Seller Invoice No./Invoice Ref. No.": credit_note_number,
            "Seller Invoice Date": invoice_date,
            "Document Amount": net_value,
            "Transaction Status": status.replace(" ", ""),
            "BANK UTR" : "NA",
            "Posting Date": posting_date,
            "Posting G/L": "NA",
            "Transaction Description": description.strip(),
            "GST Type": gst_type,
            "HSN Code": " ",
            "State Code": state_code
        })        

# Extract and add the Total row

    total_match = total_pattern.search(formatted_text)
    if total_match:
        net_value = total_match.group(1)
        table_objects.append({
            "Vendor": vendor_code,
            "Transaction Type": "DR",
            "Settlement ID": credit_note_number,
            "Seller Invoice No./Invoice Ref. No.": credit_note_number,
            "Seller Invoice Date": invoice_date,
            "Document Amount": net_value,
            "Transaction Status": status.replace(" ", ""),
            "BANK UTR" : "NA",
            "Posting Date": posting_date,
            "Posting G/L": "NA",
            "Transaction Description": "",
            "GST Type": gst_type,
            "HSN Code": "",
            "State Code": state_code
        }) 

    # print(table_objects)
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    header = [
        "Vendor", "Transaction Type", "Settlement ID", "Seller Invoice No./Invoice Ref. No.",
        "Seller Invoice Date", "Document Amount", "Transaction Status", "Bank UTR", "Posting Date"
        , "Posting G/L", "Transaction Description", "GST Type", "HSN Code",
        "State Code"
    ]
    table_objects.insert(0, table_objects.pop()) #Moving last item to First
    csv_writer.writerow(header)
    for row in table_objects:
     csv_writer.writerow([
        row.get("Vendor", "NA"),
        row.get("Transaction Type", "NA"),
        row.get("Settlement ID", "NA"),
        row.get("Seller Invoice No./Invoice Ref. No.", "NA"),
        row.get("Seller Invoice Date", "NA"),
        row.get("Document Amount", "NA"),
        row.get("Transaction Status", "NA"),
        row.get("Bank UTR", "NA"),
        row.get("Posting Date", "NA"),
        row.get("Posting G/L", "NA"),
        row.get("Transaction Description", "NA"),
        row.get("GST Type", "NA"),
        row.get("HSN Code", "NA"),
        row.get("State Code", "NA")
     ])

    # Extract base name and append .csv extension
    csv_file_path = os.path.join("generated", f"{filename}.csv")
    with open(csv_file_path, 'w', newline='') as file:
        file.write(csv_file.getvalue())



def extract_table_objects(pdf_path,filename,state_data):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    formatted_text = preprocess_text(text)
    table_objects = []

    pattern = r"([A-Z ]+?)BILLED FROM:"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        #status could be DEBITNOTE or CREDITNOTE
        status = match.group(1) 
    else:
        status = "TAX INVOICE"


    #it takes last words till space = r"Note #:\s*(\S+) and storing 
    credit_note_pattern = re.compile(rf'{status.split()[-1].title() } #:\s*(\S+)')
    invoice_date_pattern = re.compile(rf'{status.split()[-1].title() } Date:\s*(\d{{2}}-\d{{2}}-\d{{4}})')
    #state_code_pattern = re.compile(r'Place of Supply/State Code:\s*(\w+),\s*(IN-\w+)')
    state_code_pattern = re.compile(r'Place of Supply/State Code:\s*([\w\s]+?),\s*IN-(\w+)') 

    # Search for matches in the text
    credit_note_match = credit_note_pattern.search(text)
    invoice_date_match = invoice_date_pattern.search(text)
    state_code_match = state_code_pattern.search(text)

    # Process the matches
    credit_note_number = credit_note_match.group(1) if credit_note_match else 'Unknown'
    invoice_date = datetime.strptime(invoice_date_match.group(1), '%d-%m-%Y').strftime('%Y%m%d') if invoice_date_match else 'Unknown'
    if state_code_match:
        state_name = state_code_match.group(1).strip()  # Clean up the state name
        state_code_suffix = state_code_match.group(2)  # Capture only the suffix part of the state code
        state_code = f"{state_code_suffix}-{state_name}"
    else:
        state_code = 'Unknown'
    #state_code = f"{state_code_match.group(2)}-{state_code_match.group(1)}" if state_code_match else 'Unknown'
    posting_date = datetime.now().strftime('%Y%m%d')
    # Pattern to match individual fee items
    pattern = re.compile(r"(\d{6})\s+([\w\s-]+)\s+(\d+\.\d+)\s+(\d+\.\d+)")
    # Pattern to match the Total row
    total_pattern = re.compile(r"Total\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)")

    vendor_code = "NA"
    gst_type="";
    for match in pattern.finditer(formatted_text):
        service_code, description, net_value, igst_rate = match.groups()
        if igst_rate == '18.0':
            gst_type = 'IGST-18'
        else:
            gst_type = 'SGST-9'

        gst_type_text = gst_type.split('-')[0]
        if state_name in state_data:
            for state_info in state_data[state_name]:
                if gst_type_text.endswith(state_info["GSTType"].split('/')[-1]):
                    vendor_code = state_info["VendorCode"]
                    break

        #storing inside dictionary which inside a list 
        table_objects.append({
            "Vendor": vendor_code,
            "Transaction Type": "CR",
            "Settlement ID": credit_note_number,
            "Seller Invoice No./Invoice Ref. No.": credit_note_number,
            "Seller Invoice Date": invoice_date,
            "Document Amount": net_value,
            "Transaction Status": status.replace(" ", ""),
            "BANK UTR" : "NA",
            "Posting Date": posting_date,
            "Posting G/L": "NA",
            "Transaction Description": description.strip(),
            "GST Type": gst_type,
            "HSN Code": service_code,
            "State Code": state_code
        })

          # Extract and add the Total row

    total_match = total_pattern.search(formatted_text)
    if total_match:
        net_value, igst_amount, total = total_match.groups()
        table_objects.append({
            "Vendor": vendor_code,
            "Transaction Type": "DR",
            "Settlement ID": credit_note_number,
            "Seller Invoice No./Invoice Ref. No.": credit_note_number,
            "Seller Invoice Date": invoice_date,
            "Document Amount": net_value,
            "Transaction Status": status.replace(" ", ""),
            "BANK UTR" : "NA",
            "Posting Date": posting_date,
            "Posting G/L": "NA",
            "Transaction Description": "",
            "GST Type": gst_type,
            "HSN Code": "",
            "State Code": state_code
        })

   
    # print(table_objects)
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    header = [
        "Vendor", "Transaction Type", "Settlement ID", "Seller Invoice No./Invoice Ref. No.",
        "Seller Invoice Date", "Document Amount", "Transaction Status", "Bank UTR", "Posting Date",
        "Posting G/L", "Transaction Description", "GST Type", "HSN Code","State Code"
    ]
    table_objects.insert(0, table_objects.pop())
    csv_writer.writerow(header)
    for row in table_objects:
     csv_writer.writerow([
        row.get("Vendor", "NA"),
        row.get("Transaction Type", "NA"),
        row.get("Settlement ID", "NA"),
        row.get("Seller Invoice No./Invoice Ref. No.", "NA"),
        row.get("Seller Invoice Date", "NA"),
        row.get("Document Amount", "NA"),
        row.get("Transaction Status", "NA"),
        row.get("Bank UTR", "NA"),
        row.get("Posting Date", "NA"),
        row.get("Posting G/L", "NA"),
        row.get("Transaction Description", "NA"),
        row.get("GST Type", "NA"),
        row.get("HSN Code", "NA"),
        row.get("State Code", "NA")
     ])

    csv_file_path = os.path.join("generated", f"{filename}.csv")
    with open(csv_file_path, 'w', newline='') as file:
        file.write(csv_file.getvalue())




if __name__ == "__main__":
    pdf_path = sys.argv[1]  # Get PDF path from arguments
    filename = sys.argv[2]
    state_data_json = os.environ.get('STATE_DATA')
    if state_data_json:
        state_data = json.loads(state_data_json)
    # Determine which function to call based on the filename prefix
    if filename.startswith("Flipkart_ICN"):
        extract_table_objects_icn(pdf_path,filename,state_data)
    else:
        extract_table_objects(pdf_path,filename,state_data)


