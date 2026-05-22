#%%
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

import time
import pandas as pd, io
from datetime import datetime

JS_WAIT_DT = "return (typeof $ !== 'undefined' && $('#expAgencyTable').length && !!$('#expAgencyTable').DataTable());"
JS_EXPORT = """
var dt = $('#expAgencyTable').DataTable();
var e = dt.buttons.exportData();
var rows = [e.header].concat(e.body);
var csv = rows.map(function(r){ return r.map(function(c){ return '"' + String(c).replace(/"/g,'""') + '"'; }).join(','); }).join('\\n');
return csv;
"""

def grab_year(year, driver, timeout=20, type = 't', retries=2):
    
    AGCY = 426
    url = (
        "https://illinoiscomptroller.gov/financial-reports-data/expenditures-state-spending/agency"
        f"?AgcySel={AGCY}&AgcyGrpSel=0&AgcyCatSel=0&AgcyTypeSel=0&GroupBy=Obj{type}&FY={year%100:02d}&Type=A&ShowMo=Yes&submitted="
    )
    for attempt in range(retries + 1):
        driver.get(url)
        try:
            WebDriverWait(driver, timeout).until(lambda d: d.execute_script(JS_WAIT_DT))
            csv_text = driver.execute_script(JS_EXPORT)
            df = pd.read_csv(io.StringIO(csv_text))
            money_col = next((c for c in df.columns if 'Expended' in c or 'YTD' in c), None)
            if money_col:
                df[money_col] = df[money_col].replace(r'[\$,]', '', regex=True).astype(float)
            df['Year'] = year
            return df
        except TimeoutException:
            if attempt < retries:
                time.sleep(2)
                driver.refresh()
                continue
            else:
                # return empty dataframe for this year and continue processing others
                return pd.DataFrame(columns=["Code", "Object of Expenditure", "Expended YTD", "Year"])

# create driver once and reuse
service = Service(ChromeDriverManager().install())
opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-gpu")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(service=service, options=opts)

categories = {
    "Personnel": [
        "REGULAR POSITIONS",
        "SOC SEC/MEDICARE CONTRIBUTIONS",
        "STATE EMPLOYEE RETIREMENT",
        "STUDENT MEMBER/INMATE COMPENS",
        "CONTRACTUAL PAYROLL EMPLOYEES",
        "PAYMENTS TO LOC GOV EMPLOYEES",
        "EMPLOYER  CONTRB GRP INSURANCE",
        "BONUS PAYMENTS",
        "PERSONAL SRV-DEC EMPLOYEE COMP",
        "CONTRACT REIMBURSE TO EMPLOYEE",
        "OP OF AUTO REIMB EMPLOYEES",
        "COMMODITIES REIMB EMPLOYEES",
        "EMPLOYEE TUITION AND FEES",
    ],

    "Medical & Health": [
        "HOSPITAL AND MEDICAL SERVICES",
        "MEDICAL SERV,PUBL ASSIST RECIP",
        "MEDICAL CONSULTANT FEES",
        "MEDICAL & LABORATORY SUPPLIES",
        "MEDICAL/LAB EQUIP NOT OVR $100",
        "INSTITUTIONAL BURIAL SERVICES",
        "STATE MEDICARE CONTRB CONTR PY",
    ],

    "Utilities & Fuel": [
        "ELECTRICITY",
        "GAS",
        "WATER",
        "UTILITIES, N.E.C.",
        "UTILITIES",
        "GASOLINE, OIL AND ANTIFREEZE",
        "FUEL OIL AND BOTTLED GAS",
        "OFF-ROAD EQUIP GAS AND OIL",
        "COAL AND COKE",
        "ROCK SALT & ROAD USE ABRASIVES",
    ],

    "Supplies & Materials": [
        "FOOD SUPPLIES",
        "INDUSTRIAL AND SHOP MATERIALS",
        "HOUSEHOLD & CLEANING SUPPLIES",
        "HOUSEHOLD EQUIPMENT/FURNISHING",
        "MECHANICAL SUPPLIES",
        "OFFICE AND LIBRARY SUPPLIES",
        "OFFICE FURNITURE AND EQUIPMENT",
        "OFFICE EQUIP LESS THAN $100",
        "EDP SUPPLIES",
        "FORAGE FARM & GARDEN SUPPLIES",
        "WEARING APPAREL",
        "SMALL TOOLS NOT EXCEEDING $100",
        "PARTS AND FITTINGS, AUTOS",
        "PARTS/SUPPLIES,TELEPHONE EQUIP",
        "MACHINE IMPLEMENTS/MAJR  TOOLS",
        "FIXED EQUIPMENT",
        "CLEANING EQUIP, NOT OVER $100",
        "EQUIPMENT N.E.C. NOT OVER $100",
        "SCIENTIFIC INSTRUMENTS",
        "EDUC & INSTRUCTIONAL  SUPPLIES",
        "LIBRARY BOOKS",
    ],

    "Contractual & Services": [
        "PROFESSIONAL/ARTISTIC SERV NEC",
        "STATISTICAL & TABULATING SERV",
        "IN-HOUSE REPAIR & MAINTENANCE",
        "BUILDING & GROUND MAINTENANCE",
        "REPAIR & MAINT, REAL PROPERTY",
        "REPAIR AND MAINTENANCE AUTOS",
        "REPAIR & MAINT,MACHINERY",
        "REPAIR & MAINT,FURNITURE/EQUIP",
        "REPAIR AND MAINTENANCE, N.E.C.",
        "REPAIR/MAINT,TELEPHONE & OTHER",
        "REPAIR & MAINT OF EDP  EQUIP",

        "AUDITING & MANAGEMENT SERVICE",
        "COURT  REPORTING & FILING SERV",
        "COPYING/PHOTO/PRINTING SERV",
        "PRINTING",

        "CONTRACTUAL SERVICES, N.E.C.",
        "ASBESTOS ABATEMENT COST",
        "FIRE PROTECTION SERVICES",

        "ATTORNEY FEES",
        "LEGAL FEES",
        "COMBINED SETTLEMENT/ATTORNEY",

        "ADVERTISING",

        "SUBSCRIPTION/INFORMATION  SERV",
        "ASSOCIATION DUES",

        "REG/CONF EXP, VENDOR PAYMENTS",
        "REGISTRATION FEES/CONF EXPENSE",
        "TRAINING MATERIALS & EXHIBITS",

        "EXPENSE REIMBURSE CP EMPLOYEES",

        "TRAVEL,MILEAGE REIMBURSEMENTS",
        "IN-STATE TRAVEL,EMPLOYEE REIMB",
        "OUT-OF-STATE TRAVEL, EMPLOYEES",
        "OUT-OF-STATE TRAVEL,VENDORS",
        "IN-STATE TRAVEL, VENDORS",
        "NON-EMPLOYEE TRAVEL-VENDOR PMT",
        "TRAVEL - NON/STATE EMPLOYEES",
        "TRAVEL/ALLOWANCE, PRISONERS",
        "TRAVL&OTHR EXP-CONTRCT PAY EMP",

        "FREIGHT, EXPRESS AND DRAYAGE",

        "RENTAL, REAL PROPERTY",
        "RENTAL, TELEPHONE SERV & EQUIP",
        "RENTAL, OFFICE EQUIPMENT",
        "RENTAL, MACHINERY & MECH EQUIP",
        "RENTAL,OTHER COMMUNICATION SRV",
        "RENTAL,RADIO COMMUNICATION SRV",
        "RENTAL, N.E.C.",
        "RENTAL, MOTOR VEHICLES",
        "RENTL DATA PROCESSING FACILITY",
        "RENTAL DATA PROCESSING EQUIP",
        "RENTAL, DATA PROCESSING EQUIP",
        "RENTAL,DATA COMMUNICATION SERV",

        "PASSENGER AUTOMOBILES",
        "OTHER MOTOR VEHICLES",
        "AUTOMOTIVE SERVICES, NEC",
        "AUTOMOTIVE EXPENSE, N.E.C.",

        "OPERATING TAXES AND LICENSES",

        "STRUCTURES DEMOLITION/REMOVAL",
        "SITE IMPROVEMENTS",
        "REMODELING AND RENOVATION",

        "EQUIPMENT, N.E.C.",
        "EDP EQUIPMENT",
        "COMPUTER SOFTWARE",

        "TELEPHONE/COMMUNICATION EQUIP",
        "TELECOMMUNICATION SERVICES,NEC",
        "VIDEO CONFERENCING",

        "STATE GARAGE REV FND PAYMNTS",
        "FACILITIES MGT REVOL FUND PAY",
        "GATA REVOLVING CENTRLIZED PMTS",

        "POSTAGE AND POSTAL CHARGES",
    ],

    "Other": [
        "INTERFUND CASH TRANSFERS",
        "REIMBUR TO GOVERNMENTAL  UNITS",
        "TORT CLAIMS",
        "REFUNDS OF OTHER GRANTS",
        "REFUNDS, N.E.C.",
        "REFUNDS OF FEDERAL GRANTS",
        "INTEREST-PROMPT PAYMENT CY",
        "OTHER, N.E.C.",
        "STAT SERVICES CONSOL PAYS",
        "NONTAXABLE GRANTS/AWARDS NEC",
        "TORT,STTLMNTS&SIMLR PYMNT TAX",
    ],
}

try:
    year = 2022
    data = []
    current_year = datetime.now().year
    while year <= current_year:
        print("Processing", year)
        df = grab_year(year, driver, timeout=30, retries=2)
        data.append(df)
        year += 1
        time.sleep(1)  # polite pause between requests
finally:
    driver.quit()

# -----------------------------------------------------
# transpose the data and clean
# -----------------------------------------------------

df = pd.concat(data)

# 1) build label -> category dict from your categories dict of lists
label_to_cat = {
    label: cat
    for cat, labels in categories.items()
    for label in labels
}

# 2) classify the Object column
df["Object_cat"] = df["Object"].map(label_to_cat).fillna("Other")

# identify id / meta columns and month columns
id_cols = df.columns[:3].tolist()      # adjust if you have different id columns
year_col = df.columns[-2]              # last column is year
month_cols = df.columns[3:-1].tolist() # columns between ids and year

# melt months into rows
m = df.melt(id_vars=id_cols + [year_col] + ['Object_cat'],
            value_vars=month_cols,
            var_name='month',
            value_name='amount')

# clean amount (remove $ and commas, convert to numeric)
m['amount'] = (m['amount'].astype(str)
               .str.replace(r'[\$,]', '', regex=True)
               .str.replace(r'^\(([-\d.]+)\)$', r'-\1', regex=True)
               .replace({'nan': None, 'None': None, '': None})
               .astype(float))

# create datetime column from month name and year
# try abbreviated month names (Jan, Feb) first; if you have full names use '%B %Y'
try:
    m['dt'] = pd.to_datetime(m['month'].str.strip() + ' ' + m[year_col].astype(str),
                             format='%b %Y')
except ValueError:
    m['dt'] = pd.to_datetime(m['month'].str.strip() + ' ' + m[year_col].astype(str),
                             format='%B %Y')

# result
m = m.sort_values(id_cols + ['Object_cat'] + ['dt']).reset_index(drop=True)

m.to_csv('C:\\Users\\jackm\\Downloads\\test\\data_download.csv', index = False)

# %%
