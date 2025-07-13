import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
import datetime
import math
import os
from PIL import Image as PILImage

# Function to calculate owner's title insurance premium (kept as is)
def calculate_title_premium(selling_price):
    amount = selling_price + 200  # As per user instruction
    if amount <= 20000:
        premium = 400
    elif amount <= 100000:
        premium = 400 + math.ceil((amount - 20000) / 1000 * 6)
    elif amount <= 200000:
        premium = 880 + math.ceil((amount - 100000) / 1000 * 4.25)
    elif amount <= 300000:
        premium = 1305 + math.ceil((amount - 200000) / 1000 * 3.5)
    elif amount <= 1000000:
        premium = 1655 + math.ceil((amount - 300000) / 1000 * 3)
    else:
        premium = 3755 + math.ceil((amount - 1000000) / 1000 * 2.5)
    return float(premium)  # Ensure float type to match step

# App title
st.title("Seller's Cash Proceeds Generator")

# Form inputs based on the document
with st.form("seller_form"):
    # Seller info (blank by default)
    name = st.text_input("Name", value="")
    property = st.text_input("Property", value="")

    # Selling price (blank by default, but set to 0.0 for number input)
    selling_price = st.number_input("Selling Price", value=0.0, step=1000.0)

    # Mortgage balances (subtract if any)
    mortgage_balances = st.number_input("Mortgage Balances (subtract if any)", value=0.0, step=1000.0)

    # Commissions (default to 3%, auto-calculate but editable)
    listing_agent_pct = st.number_input("Listing Agent Commission %", value=3.0, step=0.25)
    listing_commission = st.number_input("Listing Agent Commission Amount (auto-calculated, editable)",
                                         value=selling_price * (listing_agent_pct / 100), step=100.0)

    buyers_agent_pct = st.number_input("Buyers Agent Commission %", value=3.0, step=0.25)
    buyers_commission = st.number_input("Buyers Agent Commission Amount (auto-calculated, editable)",
                                        value=selling_price * (buyers_agent_pct / 100), step=100.0)

    # Other expenses
    title_insurance = st.number_input("Owner's Title Insurance Policy", value=calculate_title_premium(selling_price), step=50.0)
    
    transfer_tax_rate = st.number_input("MI Transfer Tax Rate (per $1,000)", value=8.60, step=0.10)
    transfer_tax = st.number_input("MI Transfer Tax Amount (auto-calculated, editable)",
                                   value=(selling_price / 1000) * transfer_tax_rate, step=50.0)

    pest_inspection = st.number_input("Pest Inspection", value=0.0, step=50.0)
    city_certifications = st.number_input("City Certifications", value=0.0, step=50.0)
    well_septic = st.number_input("Well & Septic Inspection", value=0.0, step=50.0)
    well_septic_note = st.text_input("Well & Septic Note", value="")
    home_warranty = st.number_input("Home Warranty", value=0.0, step=50.0)
    seller_concessions = st.number_input("Seller Concessions", value=0.0, step=100.0)
    transaction_fee = st.number_input("Transaction Fee", value=0.0, step=50.0)
    survey = st.number_input("Survey (splitting costs)", value=0.0, step=50.0)

    # Adjustments
    use_occupancy_escrow = st.number_input("Use and Occupancy Escrow (-)", value=0.0, step=50.0)
    taxes_escrow_rebate = st.number_input("Taxes and Escrow Rebate (+)", value=0.0, step=50.0)

    # Signatures (blank by default)
    agent = st.text_input("Agent", value="")
    seller = st.text_input("Seller", value="")
    date = st.date_input("Date", value=datetime.date.today())

    submit = st.form_submit_button("Generate PDF")

if submit:
    # Calculate totals
    total_selling_expense = (
        listing_commission + buyers_commission + title_insurance + transfer_tax +
        pest_inspection + city_certifications + well_septic + home_warranty +
        seller_concessions + transaction_fee + survey
    )
    approximate_proceeds = (
        selling_price - mortgage_balances - total_selling_expense -
        use_occupancy_escrow + taxes_escrow_rebate
    )

    # Generate PDF with adjusted margins to prevent cutoff
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = []

    # Add logo in upper left if the file exists (no error if missing), scale to fit
    logo_path = 'logo.png'
    if os.path.exists(logo_path):
        try:
            with PILImage.open(logo_path) as img:
                orig_width, orig_height = img.size
                scale = min(280 / orig_width, 70 / orig_height)  # 40% larger max dimensions
                new_width = orig_width * scale
                new_height = orig_height * scale
            logo = Image(logo_path, width=new_width, height=new_height, hAlign='LEFT')
            elements.append(logo)
        except Exception:
            pass  # Silently skip if any issue loading the image
    elements.append(Spacer(1, 12))  # Increased spacer for better spacing

    # Title with smaller font to save space
    title_style = styles['Title']
    title_style.fontSize = 14
    elements.append(Paragraph("SELLER'S CASH PROCEEDS WORKSHEET", title_style))
    elements.append(Spacer(1, 18))  # Increased spacer

    # Data table with no grid lines for a cleaner, blank-like look
    data = [
        ['Name:', name],
        ['Property:', property],
        ['Selling Price', f"${selling_price:,.2f}"],
        ['Mortgage Balances', f"${mortgage_balances:,.2f}"],
        [f'Commission - Listing Agent {listing_agent_pct}%', f"${listing_commission:,.2f}"],
        [f'Commission - Buyers Agent {buyers_agent_pct}%', f"${buyers_commission:,.2f}"],
        ["Owner's Title Insurance Policy", f"${title_insurance:,.2f}"],
        [f'MI Transfer Tax (${transfer_tax_rate} per $1,000)', f"${transfer_tax:,.2f}"],
        ['Pest Inspection', f"${pest_inspection:,.2f}"],
        ['City Certifications', f"${city_certifications:,.2f}"],
        ['Well & Septic Inspection', f"${well_septic:,.2f}", well_septic_note],
        ['Home Warranty', f"${home_warranty:,.2f}"],
        ['Seller Concessions', f"${seller_concessions:,.2f}"],
        ['Transaction Fee', f"${transaction_fee:,.2f}"],
        ['Survey, splitting costs', f"${survey:,.2f}"],
        ['Total Selling Expense', f"${total_selling_expense:,.2f}"],
        ['Approximate Proceeds to Seller', f"${approximate_proceeds:,.2f}"],
        [],
        ['Use and Occupancy Escrow', f"- ${use_occupancy_escrow:,.2f}"],
        ['Taxes and Escrow Rebate', f"+ ${taxes_escrow_rebate:,.2f}"],
        [],
        ['Agent', agent, 'Seller', seller],
        [],
        ['Date', str(date), 'Seller', seller]
    ]

    # Table without any grid lines or backgrounds, adjusted widths to fit within margins (sum ~450 pt)
    col_widths = [250, 100, 100]  # Reduced widths to prevent overflow/cutoff
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Labels left-aligned
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Values right-aligned
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),  # Notes left-aligned
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # No GRID style to remove all lines
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),  # Helvetica font
        ('FONTSIZE', (0, 0), (-1, -1), 9),  # Smaller font to fit on one page
        ('LEFTPADDING', (0, 0), (-1, -1), 4),  # Reduced padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),  # Slightly increased bottom padding for spacing
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    # Add disclaimer from uploaded blank PDF
    elements.append(Spacer(1, 18))  # Increased spacer for better distribution
    disclaimer_style = styles['Normal']
    disclaimer_style.alignment = 0  # Left align
    disclaimer_style.fontSize = 9  # Smaller font
    disclaimer_style.leading = 10
    disclaimer_style.fontName = 'Helvetica'
    elements.append(Paragraph("The above figures are approximate and are to be used as a guide only. Final Statements are prepared prior to closing. This will signify that I have seen the approximate cash proceeds on the sale of my home.", disclaimer_style))

    # Tax note centered
    elements.append(Spacer(1, 12))  # Increased spacer
    note_style = styles['Italic']
    note_style.fontSize = 9
    note_style.fontName = 'Helvetica-Oblique'
    note_style.alignment = 1  # Center align
    elements.append(Paragraph("*Ask your Accountant or Financial Advisor about any tax liability*", note_style))

    doc.build(elements)
    buffer.seek(0)

    # Download button
    st.download_button(
        label="Download PDF",
        data=buffer,
        file_name=f"Seller_Cash_Proceeds_{name.replace(' ', '_')}.pdf" if name else "Seller_Cash_Proceeds.pdf",
        mime="application/pdf"
    )