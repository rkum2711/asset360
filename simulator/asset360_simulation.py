import numpy as np
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import random

today = datetime.now().date()
current_directory = os.getcwd()
data_folder = os.path.join(current_directory, 'data')
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

with open('./config.json', 'r') as file:
    config = json.load(file)

asset_types = config["asset_types"]
us_state_names = config["us_state_names"]
location_list = config["us_state_names"]
procedureAssetTypes = config["procedureAssetTypes"]
assetProductionLines = config["assetProductionLines"]
eli_lilly_global_locations = config["eli_lilly_global_locations"]
country_codes = config["country_codes"]
facility_types = config["facility_types"]
product_list = config["product_list"]
num_products = config["num_products"]
unitProcedureTypes = config["unitProcedureTypes"]
pharma_asset_suppliers = config["pharma_asset_suppliers"]

current_date = datetime.now()
countries = list(set(location["Country"] for location in eli_lilly_global_locations if "Country" in location))
sites = list(set(s["Plant Name"] for s in eli_lilly_global_locations if "Plant Name" in s))

def generate_region():
    region = list(set(r["Region"] for r in eli_lilly_global_locations if "Region" in r))
    num_regions = len(region)
    data = {
        'id': [f"R{i+1}" for i in range(num_regions)],
        'Name': [f"{r}" for r in region]
    }
    region = pd.DataFrame(data)
    return region

def generate_site():
    sites = list(set(s["Plant Name"] for s in eli_lilly_global_locations if "Plant Name" in s))
    num_sites = len(sites)
    site_regions = {}
    for site in sites:
        for location in eli_lilly_global_locations:
            if "Plant Name" in location and location["Plant Name"] == site and "Region" in location:
                site_regions[site] = location["Region"]
                break
    data = {
        'id': [f"S{i+1}" for i in range(num_sites)],
        'Name': [f"{s}" for s in sites],
        'Region': [site_regions.get(s, "Unknown") for s in sites]
    }
    sites = pd.DataFrame(data)
    return sites

def generate_facility(sites, region):
    facilities = []
    for index, site in sites.iterrows():
        site_facilities = []
        for count, facility_type in enumerate(facility_types, start=1):
            facility_unique_id = f"F-{count}-{site['id']}"
            facility_name = f"{site['Name']} {facility_type}"
            region_id = next((r['id'] for i,r in region.iterrows() if r['Name'] == site['Region']), 'Unknown_ID')
            site_facilities.append({
                "id": facility_unique_id,
                "Name": f"{facility_name}",
                "FType": facility_type,
                "SiteID": site['id'],
                "RegionID": region_id
            })
        facilities.extend(site_facilities)

    facilities_df = pd.DataFrame(facilities)
    return facilities_df

def generate_line(facility):
    capacities = np.arange(50, 101, 10)
    data = {'id': [], 'Name': [], 'FacilityID': [], 'LType': [], 'Capacity': [], "Floor": []}
    line_counter = 1
    
    for index, row in facility.iterrows():
        facility_id = row['id']
        facility_type = row['FType']
        floor_count = 1  # Default floor count
        
        if facility_type == "Quality Control and Assurance":
            line_type = "LIMS Line"  # Assign LIMS Line for Quality Control and Assurance
        elif facility_type in ["R&D", "Regulatory Compliance", "Warehousing and Distribution"]:
            line_type = facility_type  # Assign facility type as line type
        else:
            if facility_type == "Manufacturing":
                line_type = "Tier1-Production-Line" if line_counter % 2 != 0 else "Tier2-Production Line"  # Alternate between Tier1 and Tier2 production lines
            else:
                line_type = "Packaging Line"  # Assign Packaging Line for Warehousing and Distribution
        
        for floor_id in range(1, floor_count + 1):
            line_id = f"L{line_counter}"
            line_name = f"Line{line_type}-Type{facility_type}-{facility_id}"
            line_capacity = np.random.choice(capacities)
            data['id'].append(line_id)
            data['Name'].append(line_name)
            data['FacilityID'].append(facility_id)
            data['LType'].append(line_type)
            data['Capacity'].append(line_capacity) 
            data['Floor'].append(floor_id) 
            line_counter += 1
                
    line = pd.DataFrame(data)
    return line

def generate_oems():
    oem_list = []
    num_oems = len(pharma_asset_suppliers)
    for i in range(num_oems):
        oem = {
            'id': f"MFR{i+1}",
            'ManufacturerName': f"{pharma_asset_suppliers[i]}",
        }
        oem_list.append(oem)
    oem_df = pd.DataFrame(oem_list)
    return oem_df

def generate_asset(line,oem,unitProcedure):
    mfr_ids = oem['id'].tolist()
    asset_id_counter = 1
    data = {'id': [], 'Name': [], 'AType': [], 'FacilityID': [], 'LineID': [], 'LineFloor': [], 'ManufacturerID': [], 'unitProcedureID': []}
    for index, row in line.iterrows():
        line_id = row['id']
        line_type = row['LType']
        line_floor = row['Floor']
        facility_id = row['FacilityID']
        for line_info in assetProductionLines:
            if line_info['name'] == line_type:
                # types.extend(line_info['assets'])
                assets = line_info['assets']
                for i in assets:
                    data['id'].append(f"A{asset_id_counter}")
                    data['Name'].append(f"A{asset_id_counter}:{i}")
                    data['AType'].append(i)
                    data['LineID'].append(line_id)  
                    data['FacilityID'].append(facility_id)
                    data['LineFloor'].append(line_floor)
                    oem_id = random.choice(mfr_ids)
                    data['ManufacturerID'].append(oem_id)
                    if i in unitProcedure['AssetType'].values:
                        unitprocedure_id = unitProcedure.loc[unitProcedure['AssetType'] == i, 'id'].values[0]
                    else:
                        unitprocedure_id = None
                    data['unitProcedureID'].append(unitprocedure_id)
                    asset_id_counter = asset_id_counter + 1
    asset = pd.DataFrame(data)
    return asset

def generate_asset_info(asset):
    assetIDs = asset['id'].tolist()
    amc_years = [np.random.randint(1, 5) for _ in range(len(assetIDs))]
    warranty_years = [np.random.randint(1, 5) for _ in range(len(assetIDs))]
    today = datetime.today()
    commission_dates = [today - timedelta(days=np.random.randint(365 * min(i, i - 1), 365 * max(i, i - 1))) for i in range(1, 6)]
    asset_info_ids = ['AI' + str(i+1).zfill(3) for i in range(len(assetIDs))]
    data = {
        'id': asset_info_ids,
        'AssetID': assetIDs,
        'AMCYears': amc_years,
        'WarrantyYears': warranty_years,
        'HasInsurance': random.choices(["YES", "NO"], k=len(assetIDs)),
        'CommissionDate': random.choices(commission_dates, k=len(assetIDs))
    }
    asset_info_df = pd.DataFrame(data)
    return asset_info_df

def generate_asset_operation(asset):
    assetIDs = asset['id'].tolist()
    columns = ['id', 'AssetID', 'ProductionQuantity', 'Downtime']
    num_operations = len(assetIDs)
    total_production_qty = np.random.randint(500, 1000, size=num_operations)
    good_qty_percentage = np.random.uniform(0.8, 0.9)
    downtime = np.random.uniform(10, 20, size=num_operations) 
    performance = np.random.uniform(85, 100, size=num_operations)
    good_qty = total_production_qty * good_qty_percentage
    
    quality = good_qty / total_production_qty
    asset_oper_ids = ['AO' + str(i+1).zfill(3) for i in range(len(assetIDs))]
    asset_operations = pd.DataFrame({
        'id': asset_oper_ids,
        'AssetID': np.random.choice(assetIDs, size=num_operations),
        'ProductionQuantity': total_production_qty,
        'Downtime': downtime
    }, columns=columns)
    asset_operations['Performance'] = performance
    asset_operations['Availability'] = 100 - asset_operations['Downtime']
    asset_operations['Quality'] = quality * 100
    #asset_operations['OEE'] = (asset_operations['Availability']/100) * (asset_operations['Performance']/100) * (asset_operations['Quality']/100)
    return asset_operations

def generate_oee(asset_operations):
    asset_oee = pd.DataFrame()
    asset_oee['AssetID'] = asset_operations['AssetID']
    asset_oee['OEE'] = (asset_operations['Availability']/100) * (asset_operations['Performance']/100) * (asset_operations['Quality']/100)
    asset_oee['OEE'] =  asset_oee['OEE'] *100
    asset_oee['id'] = ['OEE' + str(i+1).zfill(3) for i in range(len(asset_oee))]
    return asset_oee

def generate_products(product_list, num_products, sites):
    site_ids = sites['id'].tolist()
    product_names = [f"ProductX{i+1}" if i >= len(product_list) else product_list[i] for i in range(num_products)]
    batch_size_limit = np.random.randint(4, 10, size=num_products) *10
    site_assignments = [random.choice(site_ids) for _ in range(num_products)]
    data = {
        'id': [f"P100{i}" for i in range(1, num_products + 1)],
        'Name': product_names,
        'SiteID': site_assignments,
        'BatchSizeLimit': batch_size_limit
    }
    products = pd.DataFrame(data)
    return products

def generate_unitprocedure():
    unit_procedure_ids = {}
    unit_procedure_name = {}
    data = {
        'id': [],
        'Name': [],
        'UPType': [],
        'Task': [],
        'AssetType': []
    }
    for procedure_type, tasks in unitProcedureTypes.items():
        unit_procedure_ids[procedure_type] = [f"{procedure_type[:2].upper()}-{i+1}-{task.split()[0][:2].upper()}{task.split()[1][0].upper() if len(task.split()) > 1 else task[0].upper()}" for i, task in enumerate(tasks)]
        unit_procedure_name[procedure_type] = [f"{procedure_type}-{i+1}-{task.replace(' ', '_')}" for i, task in enumerate(tasks)]
        for i, task in enumerate(tasks):
            data['id'].append(unit_procedure_ids[procedure_type][i])
            data['Name'].append(unit_procedure_name[procedure_type][i])
            data['UPType'].append(procedure_type)
            data['Task'].append(task)
            asset_type = procedureAssetTypes.get(task)
            data['AssetType'].append(asset_type)
    unit_procedure = pd.DataFrame(data)
    return unit_procedure

def generate_po(product, num_BOMs=10):
    Status = ["Planned", "In Progress", "Completed", "Failed", "On Hold"]
    status_weights = [8, 25, 60, 5, 2] 
    num_process_orders = len(product['id'])
    data = {
        'id': [],
        'Name': [],
        'ProductID': [],
        'Qty': [],
        'BOMID': [],
        'Status':[],
        'StartDate': [],
        'EndDate': []
    }
    BOMIDs = [f"BOM00{i}" for i in range(1, num_BOMs + 1)]
    for i in range(num_process_orders):
        productID = np.random.choice(product['id'])
        qty = np.random.randint(50, 100) * 10
        BOMID = np.random.choice(BOMIDs)
        data['id'].append(f"PO{i + 1}")
        data['Name'].append(f"PO{i + 1}")
        data['ProductID'].append(productID)
        data['Qty'].append(qty)
        data['BOMID'].append(BOMID)
        status = np.random.choice(Status, p=[weight / sum(status_weights) for weight in status_weights])
        data['Status'].append(status)
        start_date = current_date - timedelta(days=i)
        end_date = start_date + timedelta(days=np.random.randint(1, 2))
        data['StartDate'].append(start_date)
        data['EndDate'].append(end_date)
    po = pd.DataFrame(data)
    return po

def generate_batch(po, product, facility):
    batch_data = {
        'id': [],
        'Name': [],
        'POID': [],
        'ProductID': [],
        'SiteID': [],
        'FacilityID': [],
        'Qty': [],
        'Status':[],
        'StartDate': [],
        'EndDate': []
    }
    for index, row in po.iterrows():
        product_id = row['ProductID']
        poid = row['id']
        qty = row['Qty']
        status = row['Status']
        start_date = row['StartDate'] 
        end_date = row['EndDate'] 
        batch_size = product.loc[product['id'] == product_id, 'BatchSizeLimit'].iloc[0]
        site_id = product.loc[product['id'] == product_id, 'SiteID'].iloc[0]
        manufacturing_facility= facility[(facility['SiteID'] == site_id) & (facility['FType'] == 'Manufacturing')]
        facility_id = manufacturing_facility['id'].tolist()[0]
        if batch_size > qty:
            num_batches = 1
        else:
            num_batches = int(np.ceil(qty / batch_size))
        remaining_qty = qty
        for i in range(num_batches):
            if num_batches > 1:
                batch_qty = min(batch_size, remaining_qty)
            else:
                batch_qty = qty
            batch_id = f"B{poid}-{index+1}-{i+1}"
            batch_name = f"Batch-{batch_id}-{product_id}-{batch_qty}"
            batch_data['id'].append(batch_id)
            batch_data['Name'].append(batch_name)
            batch_data['POID'].append(poid)
            batch_data['ProductID'].append(product_id)
            batch_data['SiteID'].append(site_id)
            batch_data['FacilityID'].append(facility_id)
            batch_data['Qty'].append(batch_qty)
            batch_data['Status'].append(status) 
            batch_data['StartDate'].append(start_date + timedelta(days=1))
            batch_data['EndDate'].append(start_date)
            remaining_qty -= batch_qty
            i+1
    batch = pd.DataFrame(batch_data)
    return batch

def get_random_unit_procedures(unit_procedure_df, up_type, num_tasks):
    filtered_df = unit_procedure_df[unit_procedure_df['UPType'] == up_type]
    random_tasks = filtered_df.sample(n=num_tasks)
    return random_tasks['id'].tolist()

def generate_wo(batch, up, asset):
    workorder_data = {
            'id': [],
            'Name': [],
            'WOType': [],
            'Task': [],
            # 'POID': [],
            'ProductID': [],
            # 'BatchID': [],
            'AssetType': [],
            'AssetID': [],
            'Status':[],
            # 'StartDate': [],
            # 'EndDate': [],
            'FacilityID': [],
            'SiteID': [],
            'UnitProcedureID': [],
            'BatchQty': []}
    for index, batch_row in batch.iterrows():
        batch_id = batch_row['id']
        site_id = batch_row['SiteID']
        facility_id = batch_row['FacilityID']
        # poid = batch_row['POID']
        bstart = batch_row['StartDate']
        bend = batch_row['EndDate']
        product_id = batch_row['ProductID']
        BatchQty = batch_row['Qty']
        floor_choice = np.random.choice([0, 1])
        unit_procedure_ids_stage1 = get_random_unit_procedures(up, 'Production-stage1', 3)
        unit_procedure_ids_stage2 = get_random_unit_procedures(up, 'Production-stage2', 2)
        unit_procedure_ids_cleaning = get_random_unit_procedures(up, 'Cleaning', 1)
        unit_procedure_ids_Qms = get_random_unit_procedures(up, 'QMS', 1)
        unit_procedure_ids_lims = get_random_unit_procedures(up, 'LIMS', 3)
        unit_procedure_ids_combined = unit_procedure_ids_stage1 + unit_procedure_ids_stage2
        # print(unit_procedure_ids_combined)
        for unit_procedure in unit_procedure_ids_combined:
            asset_type = up.loc[up['id'] == unit_procedure, 'AssetType'].values[0]
            wo_type = up.loc[up['id'] == unit_procedure, 'UPType'].values[0]
            wo_task = up.loc[up['id'] == unit_procedure, 'Task'].values[0]
            filtered_assets = asset[(asset['AType'] == asset_type) & (asset['FacilityID'] == facility_id)]
            if not filtered_assets.empty:
                # selected_asset = filtered_assets.sample(n=1)
                asset_id = filtered_assets['id'].values[0]
            else:
                asset_id = None

            status = np.random.choice(["Planned", "In Progress", "Completed", "Cancelled", "On Hold"])
            start_date = bstart + timedelta(days=np.random.randint(1, 2))
            if status == "In Progress":
                end_date = datetime.now()
            else:
                end_date = start_date
            workorder_id = f"WO-{batch_id}-{wo_type}"
            workorder_name = f"{batch_id}-{wo_type}-{product_id}-{facility_id}"
            workorder_data['id'].append(workorder_id) 
            workorder_data['Name'].append(workorder_name)
            workorder_data['WOType'].append(wo_type)
            workorder_data['Task'].append(wo_task)
            # workorder_data['POID'].append(poid)
            workorder_data['ProductID'].append(product_id)
            # workorder_data['BatchID'].append(batch_id)
            workorder_data['AssetType'].append(asset_type)
            workorder_data['AssetID'].append(asset_id)
            workorder_data['Status'].append(status)
            # workorder_data['StartDate'].append(start_date)
            # workorder_data['EndDate'].append(end_date)
            workorder_data['FacilityID'].append(facility_id)
            workorder_data['SiteID'].append(site_id)
            workorder_data['UnitProcedureID'].append(unit_procedure)
            workorder_data['BatchQty'].append(BatchQty)
    wo = pd.DataFrame(workorder_data)
    return wo

def generate_maintenance(asset,oee_df):
    data = {'id': [],
            'AssetID': [],
            'MaintenanceSchedule': [],
            'LastMaintenanceDate': [],
            'NextMaintenanceDate': [],
            'MaintenancePerformedBy': [],
            'MaintenanceRecords': []}
    asset_ids = asset['id'].tolist()
    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    
    for asset_id in asset_ids:
        if asset_id in oee_df['AssetID'].values:
            oee_value = oee_df.loc[oee_df['AssetID'] == asset_id, 'OEE'].values[0]
            if oee_value < 70:
                num_records = int(np.random.uniform(6, 10) * oee_value)
            else:
                num_records = int(np.random.uniform(1, 5) * oee_value)
        else:
            oee_value = 90
            num_records = 1
        for _ in range(num_records):
            maintenance_schedule = 'On REPAIR'
            last_maintenance_date = np.random.choice(pd.date_range(start=one_year_ago, end=today))
            next_maintenance_date = last_maintenance_date + pd.DateOffset(months=1)
            maintenance_performed_by = np.random.choice(['John', 'Jane Smith', 'Tony'])
            maintenance_records = 'Replaced filter and checked lubrication'
            # Append data to the dictionary
            data['id'].append(f"MaintenanceRecord{_ + 1}")
            data['AssetID'].append(asset_id)
            data['MaintenanceSchedule'].append(maintenance_schedule)
            data['LastMaintenanceDate'].append(last_maintenance_date)
            data['NextMaintenanceDate'].append(next_maintenance_date)
            data['MaintenancePerformedBy'].append(maintenance_performed_by)
            data['MaintenanceRecords'].append(maintenance_records)
    maintenance_df = pd.DataFrame(data)
    return maintenance_df

def generate_calibration(asset):
    data = {'id': [],
            'AssetID': [],
            'CalibrationSchedule': [],
            'LastCalibrationDate': [],
            'NextCalibrationDate': [],
            'CalibrationPerformedBy': [],
            'CalibrationRecords': []}
    asset_ids = asset['id'].tolist()

    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    num_records = len(asset_ids)
    
    for _ in range(num_records):
        asset_id = np.random.choice(asset_ids)
        calibration_schedule = 'Quaterly'
        last_calibration_date = np.random.choice(pd.date_range(start=one_year_ago, end=today))
        next_calibration_date = last_calibration_date + pd.DateOffset(months=2)
        calibration_performed_by = np.random.choice(['Smith', 'Jackie', 'Snow'])
        calibration_records = 'Calibration records details...'
        data['id'].append(f"CalibrationRecord{_ + 1}")
        data['AssetID'].append(asset_id)
        data['CalibrationSchedule'].append(calibration_schedule)
        data['LastCalibrationDate'].append(last_calibration_date)
        data['NextCalibrationDate'].append(next_calibration_date)
        data['CalibrationPerformedBy'].append(calibration_performed_by)
        data['CalibrationRecords'].append(calibration_records)
    calibration_df = pd.DataFrame(data)
    return calibration_df

def generate_compliance(asset):
    data = {'id': [],
            'AssetID': [],
            'ComplianceStatus': [],
            'RegulatoryReferences': [],
            'Documentation': []}
    asset_ids = asset['id'].tolist()
    for asset_id in asset_ids:
        compliance_status = np.random.choice(['Compliant', 'Non-Compliant'], p=[0.7, 0.3])
        regulatory_references = 'Regulatory references details...'
        documentation = 'Documentation details...'
        
        data['id'].append(f"ComplianceRecord_{asset_id}")
        data['AssetID'].append(asset_id)
        data['ComplianceStatus'].append(compliance_status)
        data['RegulatoryReferences'].append(regulatory_references)
        data['Documentation'].append(documentation)
    
    compliance_df = pd.DataFrame(data)
    return compliance_df
    
def generate_lims(wo):
    lims_wo = wo[wo['WOType'] == 'LIMS']
    num_samples = len(lims_wo)
    # Define thresholds and proportions
    passed_threshold = 90
    inprogress_threshold = 80
    passed_prop = 0.90
    inprogress_prop = 0.07
    passed_count = int(num_samples * passed_prop)
    inprogress_count = int(num_samples * inprogress_prop)
    failed_count = num_samples - passed_count - inprogress_count
    passed_results = np.random.randint(passed_threshold + 1, 101, size=passed_count)
    inprogress_results = np.random.randint(inprogress_threshold + 1, passed_threshold, size=inprogress_count)
    failed_results = np.random.randint(60, inprogress_threshold, size=failed_count)
    results = np.concatenate((passed_results, inprogress_results, failed_results))
    np.random.shuffle(results)
    statuses = []
    for result in results:
        if result >= passed_threshold:
            statuses.append('Passed')
        elif result >= inprogress_threshold:
            statuses.append('InProgress')
        else:
            statuses.append('Failed')
    lims_data = {
        'id': [f"LIMS-{i+1}" for i in range(num_samples)],
        'name': [f"LIMS-{row['AssetID']}-{row['id']}" for index, row in lims_wo.iterrows()],
        'Test': lims_wo['Task'].tolist(),
        'Result': results,
        'AssetID': lims_wo['AssetID'].tolist(),
        'WOID': lims_wo['id'].tolist(),
        'Status': statuses,
        'FacilityID': lims_wo['FacilityID'].tolist(),
        'SiteID': lims_wo['SiteID'].tolist()
    }
    lims = pd.DataFrame(lims_data)
    return lims

region_df = generate_region()
site_df = generate_site()
facility_df = generate_facility(site_df,region_df)
line_df = generate_line(facility_df)
oem_df = generate_oems()
up_df = generate_unitprocedure()
asset_df = generate_asset(line_df,oem_df,up_df)
asset_info_df = generate_asset_info(asset_df)
products_df = generate_products(product_list, num_products,site_df)
po_df = generate_po(products_df, num_BOMs=10)
batch_df = generate_batch(po_df, products_df, facility_df)
wo_df = generate_wo(batch_df, up_df, asset_df)
lims_df = generate_lims(wo_df)
asset_oper_df = generate_asset_operation(asset_df)
asset_oee_df = generate_oee(asset_oper_df)
maintenance_df = generate_maintenance(asset_df, asset_oee_df)
calibration_df = generate_calibration(asset_df)
compliance_df = generate_compliance(asset_df)

print(region_df.head())
print(site_df.head())
print(facility_df.head())
print(line_df.head())
print(oem_df.head())
print(up_df.head())
print(asset_df.head())
print(asset_info_df.head())
print(products_df.head())
print(po_df.head())
print(batch_df.head())
print(wo_df.head())
print(lims_df.head())
print(asset_oper_df.head())
print(asset_oee_df.head())
print(maintenance_df.head())
print(calibration_df.head())
print(compliance_df.head())

region_df.to_csv(os.path.join(data_folder, 'region.csv'), index=False)
site_df.to_csv(os.path.join(data_folder, 'site.csv'), index=False)
facility_df.to_csv(os.path.join(data_folder, 'facility.csv'), index=False)
line_df.to_csv(os.path.join(data_folder, 'line.csv'), index=False)
oem_df.to_csv(os.path.join(data_folder, 'oem.csv'), index=False)
asset_df.to_csv(os.path.join(data_folder, 'asset.csv'), index=False)
asset_info_df.to_csv(os.path.join(data_folder, 'asset_info.csv'), index=False)
products_df.to_csv(os.path.join(data_folder, 'product.csv'), index=False)
up_df.to_csv(os.path.join(data_folder, 'up.csv'), index=False)
po_df.to_csv(os.path.join(data_folder, 'po.csv'), index=False)
batch_df.to_csv(os.path.join(data_folder, 'batch.csv'), index=False)
wo_df.to_csv(os.path.join(data_folder, 'wo.csv'), index=False)
lims_df.to_csv(os.path.join(data_folder, 'lims.csv'), index=False)
asset_oper_df.to_csv(os.path.join(data_folder, 'asset_oper.csv'), index=False)
asset_oee_df.to_csv(os.path.join(data_folder, 'asset_oee.csv'), index=False)
maintenance_df.to_csv(os.path.join(data_folder, 'maintenance.csv'), index=False)
calibration_df.to_csv(os.path.join(data_folder, 'calibration.csv'), index=False)
compliance_df.to_csv(os.path.join(data_folder, 'compliance.csv'), index=False)