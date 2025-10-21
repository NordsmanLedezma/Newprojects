import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
import re
from datetime import datetime

# Create a new workbook for the properly formatted data
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Valores_ISIN"

# Style definitions
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
center_alignment = Alignment(horizontal="center", vertical="center")

# Headers matching our import format
headers = ["Código ISIN", "Código Latinex", "Descripción del Valor", "Cupón", "Fecha de Emisión", "Fecha de Vencimiento"]
ws.append(headers)

# Style headers
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center_alignment

# Data from the extracted file - converting to our format
panama_bonds = [
    # Local bonds (PAL codes)
    ("PAL634445TA1", "RPMA0375000426A", "República de Panamá - PANOTA 3 3/4%", "3.75%", "2016-04-17", "2026-04-17"),
    ("PAL634445VA7", "RPMA0285000627A", "República de Panamá - PANOTA 2.85%", "2.85%", "2017-06-27", "2027-06-27"),
    ("PAL63444D5A7", "RPMA0700000429A", "República de Panamá - PANOTA 7%", "7.00%", "2019-04-19", "2029-04-19"),
    ("PAL63444C5A8", "RPMA0650001228A", "República de Panamá - PANOTA 6 1/2%", "6.50%", "2018-12-28", "2028-12-28"),
    ("PAL634445WA5", "RPMA0300001229A", "República de Panamá - PABONT 3%", "3.00%", "2019-12-27", "2029-12-27"),
    ("PAL63444E5A6", "RPMA0662500829A", "República de Panamá - PANOTA 6 5/8%", "6.625%", "2019-08-23", "2029-08-23"),
    ("PAL634445XA3", "RPMA0336200631A", "República de Panamá - PABONT 3.362%", "3.362%", "2021-06-30", "2031-06-30"),
    ("PAL63444A5A0", "RPMA0520000734A", "República de Panamá - PABONT 5.2%", "5.20%", "2024-07-05", "2034-07-05"),
    ("PAL63444B5A9", "RPMA0637500733A", "República de Panamá - PABONT 6 3/8%", "6.375%", "2023-07-25", "2033-07-25"),
    
    # International bonds (US codes)
    ("US698299AV61", "RPME0712500126A", "República de Panamá - PANAMA 7 1/8%", "7.125%", "1996-01-29", "2026-01-29"),
    ("US698299AD63", "", "República de Panamá - PANAMA 8 7/8%", "8.875%", "1997-09-30", "2027-09-30"),
    ("US698299BF03", "", "República de Panamá - PANAMA 3 7/8%", "3.875%", "2018-03-17", "2028-03-17"),
    ("US698299AK07", "RPME0937500429A", "República de Panamá - PANAMA 9 3/8%", "9.375%", "2019-04-01", "2029-04-01"),
    ("US698299BK97", "RPME0316000130A", "República de Panamá - PANAMA 3.16%", "3.16%", "2020-01-23", "2030-01-23"),
    ("US698299BX19", "", "República de Panamá - PANAMA 7 1/2%", "7.50%", "2021-03-01", "2031-03-01"),
    ("US698299BN37", "", "República de Panamá - PANAMA 2.252%", "2.252%", "2022-09-29", "2032-09-29"),
    ("US698299BR41", "", "República de Panamá - PANAMA 3.298%", "3.298%", "2023-01-19", "2033-01-19"),
    ("US698299AT16", "RPME0812500434A", "República de Panamá - PANAMA 8 1/8%", "8.125%", "2004-04-28", "2034-04-28"),
    ("US698299BT07", "", "República de Panamá - PANAMA 6.4%", "6.40%", "2025-02-14", "2035-02-14"),
    ("US698299AW45", "RPME0670000136A", "República de Panamá - PANAMA 6.7%", "6.70%", "2006-01-26", "2036-01-26"),
    ("US698299BW36", "", "República de Panamá - PANAMA 6 7/8%", "6.875%", "2016-01-31", "2036-01-31"),
    ("US698299BY91", "", "República de Panamá - PANAMA 8%", "8.00%", "2008-03-01", "2038-03-01"),
    ("US698299BG85", "", "República de Panamá - PANAMA 4 1/2%", "4.50%", "2017-05-15", "2047-05-15"),
    ("US698299BH68", "", "República de Panamá - PANAMA 4 1/2%", "4.50%", "2020-04-16", "2050-04-16"),
    ("US698299BB98", "", "República de Panamá - PANAMA 4.3%", "4.30%", "2023-04-29", "2053-04-29"),
    ("US698299BV52", "", "República de Panamá - PANAMA 6.853%", "6.853%", "2024-03-28", "2054-03-28"),
    ("US698299BM53", "", "República de Panamá - PANAMA 4 1/2%", "4.50%", "2026-04-01", "2056-04-01"),
    ("US698299BZ66", "", "República de Panamá - PANAMA 7 7/8%", "7.875%", "2027-03-01", "2057-03-01"),
    ("US698299BL70", "", "República de Panamá - PANAMA 3.87%", "3.87%", "2030-07-23", "2060-07-23"),
    ("US698299BS24", "", "República de Panamá - PANAMA 4 1/2%", "4.50%", "2033-01-19", "2063-01-19"),
    
    # Treasury bills (PAL codes with 0% coupon)
    ("PAL634445ZY8", "RPMA0421871125Y", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2024-11-14", "2025-11-14"),
    ("PAL634445ZZ5", "RPMA0421970226Z", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-02-13", "2026-02-13"),
    ("PAL63444F5A5", "RPMA0399360326A", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-03-13", "2026-03-13"),
    ("PAL950025FB4", "RPMA0384980426B", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-04-24", "2026-04-24"),
    ("PAL950025FC2", "RPMA0396550526C", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-05-15", "2026-05-15"),
    ("PAL950025FD0", "RPMA0407300626D", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-06-12", "2026-06-12"),
    ("PAL950025FE8", "RPMA0397650726E", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-07-17", "2026-07-17"),
    ("PAL950025FF5", "RPMA0382230826F", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-08-21", "2026-08-21"),
    ("PAL950025FG3", "RPMA0360730926G", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-09-11", "2026-09-11"),
    ("PAL950025FH1", "RPMA0359421026H", "República de Panamá - PANTB Letra del Tesoro", "0.00%", "2025-10-16", "2026-10-16"),
]

# Add data to worksheet
for bond in panama_bonds:
    ws.append(bond)

# Auto-adjust column widths
for column in ws.columns:
    max_length = 0
    column_letter = column[0].column_letter
    for cell in column:
        try:
            if len(str(cell.value)) > max_length:
                max_length = len(str(cell.value))
        except:
            pass
    adjusted_width = min(max_length + 2, 40)
    ws.column_dimensions[column_letter].width = adjusted_width

# Save the file
wb.save('/app/panama_bonds_formatted.xlsx')
print(f"Created formatted Excel file with {len(panama_bonds)} Panama government bonds")
print("File saved as: /app/panama_bonds_formatted.xlsx")