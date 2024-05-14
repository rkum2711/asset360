import numpy as np
import pandas as pd
import os
import json
from datetime import datetime, timedelta

today = datetime.now().date()
current_directory = os.getcwd()
data_folder = os.path.join(current_directory, 'data')
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

with open('./config.json', 'r') as file:
    config = json.load(file)

num_process_orders = config["num_process_orders"]
product_list = config["product_list"]
asset_types = config["asset_types"]
us_state_names = config["us_state_names"]
num_products = config["num_products"]
num_facilities = config["num_facilities"]
num_sites = config["num_sites"]
num_regions = config["num_regions"]
num_materials = num_products * 3
num_families = num_products // 3
num_suppliers = num_materials//4
num_materials_per_recipe_range = (2, 5)
Status = ["Planned", "In Progress", "Completed", "Cancelled", "On Hold"]
status_weights = [10, 30, 40, 5, 5] 
unitProcedureTypes = config["unitProcedureTypes"]
location_list = config["us_state_names"]
procedureAssetTypes = config["procedureAssetTypes"]
assetProductionLines = config["assetProductionLines"]

current_date = datetime.now()

def generate_family():
    data = {
        'id': [f"PF-{i+1}" for i in range(num_families)],
        'Name': [f"Family{i+1}" for i in range(num_families)]}
    family = pd.DataFrame(data)
    return family

def generate_products():
    products_per_family = 3
    product_names = [f"ProductX{i+1}" if i >= len(product_list) else product_list[i] for i in range(num_products)]
    facility_ids = [f"F{(i % num_facilities) + 1}" for i in range(num_products)]
    family_ids = [f"PF-{(i // products_per_family) + 1}" for i in range(num_products)]
    recipe_ids = [f"PMR-{i}" for i in range(1, num_products + 1)]
    batch_size_limit = np.random.randint(4, 10, size=num_products) *10
    data = {
        'id': [f"P100{i}" for i in range(1, num_products + 1)],
        'Name': product_names,
        'FacilityID': facility_ids,
        'FamilyID': family_ids,
        'RecipeID': recipe_ids,
        'BatchSizeLimit': batch_size_limit
    }
    products = pd.DataFrame(data)
    return products

def generate_material():
    start_date = datetime(2023, 1, 1)
    end_date = datetime.now()
    num_pass = int(num_materials * 0.95)
    num_fail = num_materials - num_pass
    data = {
        'id': [f"M{i+1}" for i in range(num_materials)],
        'Name': [f"Material{i+1}" for i in range(num_materials)],
        'Qty': np.random.randint(10, 100, size=num_materials) * 10,
        'SupplierID': np.tile(range(1, int(num_suppliers) + 1), int(num_materials // num_suppliers)),
        'Location': np.random.choice(location_list, size=num_materials),
        # 'Status': np.random.choice(["Passed", "Failed"], size=num_materials, p=[0.95, 0.05]),
        'BatchDate': [generate_random_batch_date(start_date, end_date) for _ in range(num_materials)],
    }
    material = pd.DataFrame(data)
    material['SupplierID'] = 'SUP' + material['SupplierID'].astype(str)
    material['Storage'] = 'STORAGE-' + material['Location'].astype(str).str[:2]
    material['ExpiryDate'] = material['BatchDate'].apply(lambda x: x + timedelta(days=int(np.random.choice([365, 365 * 2,365 * 3]))))
    material['Status'] = material['ExpiryDate'].apply(lambda expiry_date: "Passed" if pd.Timestamp(expiry_date) > pd.Timestamp(today) else "Failed")
    return material

def generate_random_batch_date(start_date, end_date):
    random_days = np.random.randint((end_date - start_date).days)
    return start_date + timedelta(days=random_days)

def generate_plant_material(facility, material):
    plant_material = pd.DataFrame(columns=['id', 'FacilityID', 'MaterialID', 'Qty', 'Status'])
    facility_ids = facility['id'].tolist()
    material_sample = material.sample(frac=1).reset_index(drop=True)
    for i, material_row in material_sample.iterrows():
        facility_id = facility_ids[i % len(facility_ids)] 
        plant_material = plant_material._append({
            'id': 'PM' + str(i + 1), 
            'Name': f"PM-{material_row['id']}-{facility_id}",
            'FacilityID': facility_id,
            'MaterialID': material_row['id'],
            'Qty': material_row['Qty'],
            'Status': material_row['Status'],
            'BatchDate': material_row['BatchDate'],
            'ExpiryDate': material_row['ExpiryDate'],
        }, ignore_index=True)
    return plant_material

def generate_recipe(material):
    recipe_data = {
        'id': [],
        'Name': [],
        'MaterialID': [],
        'Qty': []
    }
    for recipe_id in range(1, num_products + 1):
        recipe_name = f"Recipe{recipe_id}"
        materials = np.random.choice(material['id'], size=np.random.randint(3, 5), replace=False)
        for material_id in materials:
            qty = np.random.randint(2, 10) *10
            recipe_data['id'].append(f"PMR-{recipe_id}")
            recipe_data['Name'].append(recipe_name)
            recipe_data['MaterialID'].append(material_id)
            recipe_data['Qty'].append(qty)
    recipe = pd.DataFrame(recipe_data)
    return recipe

def generate_recipe_unitprocedure():
    unit_procedure_ids = {}
    for procedure_type, tasks in unitProcedureTypes.items():
        unit_procedure_ids[procedure_type] = [f"{procedure_type[:2].upper()}-{i+1}-{task.split()[0][:2].upper()}{task.split()[1][0].upper() if len(task.split()) > 1 else task[0].upper()}" for i, task in enumerate(tasks)]
    recipe_unitprocedure_mapping = {
        'RecipeID': [],
        'UnitProcedureID': []
    }
    for recipe_id in range(1, num_products + 1):
        # Mixing ingredients task is always included
        recipe_unitprocedure_mapping['RecipeID'].append(f"PMR-{recipe_id}")
        recipe_unitprocedure_mapping['UnitProcedureID'].append(unit_procedure_ids["Production-stage1"][0])
        production_tasks = np.random.choice(unit_procedure_ids["Production-stage1"][1:], size=2, replace=False)
        recipe_unitprocedure_mapping['RecipeID'].extend([f"PMR-{recipe_id}"] * len(production_tasks))
        recipe_unitprocedure_mapping['UnitProcedureID'].extend(production_tasks)
        # Inspection task is always included
        recipe_unitprocedure_mapping['RecipeID'].append(f"PMR-{recipe_id}")
        recipe_unitprocedure_mapping['UnitProcedureID'].append(unit_procedure_ids["Production-stage2"][-1])
        quality_task = np.random.choice(unit_procedure_ids["Production-stage2"][:-1], size=2, replace=False)
        recipe_unitprocedure_mapping['RecipeID'].extend([f"PMR-{recipe_id}"] * len(quality_task))
        recipe_unitprocedure_mapping['UnitProcedureID'].extend(quality_task)
        for procedure_type in ["Maintenance", "Cleaning", "QMS", "LIMS", "Packaging"]:
            tasks = unit_procedure_ids[procedure_type]
            recipe_unitprocedure_mapping['RecipeID'].extend([f"PMR-{recipe_id}"] * len(tasks))
            recipe_unitprocedure_mapping['UnitProcedureID'].extend(tasks)
    recipe_unitprocedure_mapping['UnitProcedureID'] = [proc_id.replace(" ", "_") for proc_id in recipe_unitprocedure_mapping['UnitProcedureID']]
    recipe_unitprocedure = pd.DataFrame(recipe_unitprocedure_mapping)
    return recipe_unitprocedure

def generate_unitprocedure():
    unit_procedure_ids = {}
    unit_procedure_name = {}
    data = {
        'id': [],
        'Name': [],
        'Type': [],
        'Task': [],
        'AssetType': [],
    }
    for procedure_type, tasks in unitProcedureTypes.items():
        unit_procedure_ids[procedure_type] = [f"{procedure_type[:2].upper()}-{i+1}-{task.split()[0][:2].upper()}{task.split()[1][0].upper() if len(task.split()) > 1 else task[0].upper()}" for i, task in enumerate(tasks)]
        unit_procedure_name[procedure_type] = [f"{procedure_type}-{i+1}-{task.replace(' ', '_')}" for i, task in enumerate(tasks)]
        for i, task in enumerate(tasks):
            data['id'].append(unit_procedure_ids[procedure_type][i])
            data['Name'].append(unit_procedure_name[procedure_type][i])
            data['Type'].append(procedure_type)
            data['Task'].append(task)
            asset_type = procedureAssetTypes.get(task)
            data['AssetType'].append(asset_type)
    unit_procedure = pd.DataFrame(data)
    return unit_procedure

def generate_po(product, num_BOMs=10):
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
    for i in range(num_process_orders):
        productIDs = np.random.choice(product['id'], size=np.random.randint(1, 4), replace=False)
        quantities = np.random.randint(1, 10, size=len(productIDs)) * 10
        BOMID = [f"BOM00{i}" for i in range(1, num_process_orders + 1)]
        for productID, qty in zip(productIDs, quantities):
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

def generate_batch(po, product):
    batch_data = {
        'id': [],
        'Name': [],
        'POID': [],
        'ProductID': [],
        'FacilityID': [],
        'RecipeID': [],
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
        recipe_id = product.loc[product['id'] == product_id, 'RecipeID'].iloc[0]
        facility_id = product.loc[product['id'] == product_id, 'FacilityID'].iloc[0]
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
            batch_data['FacilityID'].append(facility_id)
            batch_data['RecipeID'].append(recipe_id)
            batch_data['Qty'].append(batch_qty)
            batch_data['Status'].append(status) 
            batch_data['StartDate'].append(start_date + timedelta(days=1))
            batch_data['EndDate'].append(start_date)
            remaining_qty -= batch_qty
            i+1
    batch = pd.DataFrame(batch_data)
    return batch

def generate_wo(batch, recipe_unitprocedure_mapping, up, asset):
    workorder_data = {
            'id': [],
            'Name': [],
            'Type': [],
            'Task': [],
            'POID': [],
            'ProductID': [],
            'BatchID': [],
            'AssetType': [],
            'AssetID': [],
            'Status':[],
            'StartDate': [],
            'EndDate': [],
            'FacilityID': [],
            'UnitProcedureID': []}
    for index, batch_row in batch.iterrows():
        batch_id = batch_row['id']
        facility_id = batch_row['FacilityID']
        poid = batch_row['POID']
        bstart = batch_row['StartDate']
        bend = batch_row['EndDate']
        product_id = batch_row['ProductID']
        recipe_id = batch_row['RecipeID']
        floor_choice = np.random.choice([0, 1])
        unit_procedures = recipe_unitprocedure_mapping.loc[recipe_unitprocedure_mapping["RecipeID"] == recipe_id]["UnitProcedureID"].tolist()
        for unit_procedure in unit_procedures:
            asset_type = up.loc[up['id'] == unit_procedure, 'AssetType'].values[0]
            wo_type = up.loc[up['id'] == unit_procedure, 'Type'].values[0]
            wo_task = up.loc[up['id'] == unit_procedure, 'Task'].values[0]
            filtered_assets = asset[(asset['Type'] == asset_type) & (asset['LineFloor'] == floor_choice) & (asset['FacilityID'] == facility_id)]
            if not filtered_assets.empty:
                selected_asset = filtered_assets.sample(n=1)
                asset_id = selected_asset['id'].values[0]
            else:
                asset_id = None
            status = np.random.choice(["Planned", "In Progress", "Completed", "Cancelled", "On Hold"])
            start_date = bstart + timedelta(days=np.random.randint(1, 2))
            if status == "In Progress":
                end_date = datetime.now()
            else:
                end_date = start_date
            workorder_id = f"WO-{batch_id}-{unit_procedure}"
            workorder_name = f"{batch_id}-{unit_procedure}-{product_id}-{facility_id}"
            workorder_data['id'].append(workorder_id) 
            workorder_data['Name'].append(workorder_name)
            workorder_data['Type'].append(wo_type)
            workorder_data['Task'].append(wo_task)
            workorder_data['POID'].append(poid)
            workorder_data['ProductID'].append(product_id)
            workorder_data['BatchID'].append(batch_id)
            workorder_data['AssetType'].append(asset_type)
            workorder_data['AssetID'].append(asset_id)
            workorder_data['Status'].append(status)
            workorder_data['StartDate'].append(start_date)
            workorder_data['EndDate'].append(end_date)
            workorder_data['FacilityID'].append(facility_id)
            workorder_data['UnitProcedureID'].append(unit_procedure)
    wo = pd.DataFrame(workorder_data)
    return wo

def generate_site():
    data = {
        'id': [f"S{i+1}" for i in range(num_sites)],
        'Name': [f"SITE00{i+1}" for i in range(num_sites)]
    }
    sites = pd.DataFrame(data)
    return sites

def generate_region():
    data = {
        'id': [f"R{i+1}" for i in range(num_regions)],
        'Name': [f"REGION00{i+1}" for i in range(num_regions)]
    }
    region = pd.DataFrame(data)
    return region

def generate_facility():
    num_facilities_per_site = 2
    num_sites_per_region = 2
    data = {
        'id': [f"F{i+1}" for i in range(num_facilities)],
        'Name': [f"Facility{i+1}" for i in range(num_facilities)],
        'SiteID': [f"S{i // num_facilities_per_site + 1}" for i in range(num_facilities)],
        'RegionID': [f"R{i // (num_facilities_per_site*num_sites_per_region) + 1}" for i in range(num_facilities)]
    }
    facility = pd.DataFrame(data)
    return facility

def generate_line(facility):
    # lines_per_facility = len(assetProductionLines)
    line_dublicate = 2
    capacities = np.arange(50, 101, 10)
    data = {'id': [], 'Name': [], 'FacilityID': [], 'Type': [], 'Capacity': [], "Floor": []}
    line_counter = 1
    for facility_id in facility['id']:
        for i in range(0,line_dublicate):
            floor_id = i
            for lines, line_type in enumerate(assetProductionLines):
                # for i in range(lines_per_facility):
                line_id = f"L{lines+1}-{line_counter}-{floor_id}"
                line_type_name = line_type['name']
                line_name = f"Line{lines+1}-{line_type_name}-{facility_id}"
                line_capacity = np.random.choice(capacities)
                data['id'].append(line_id)
                data['Name'].append(line_name)
                data['FacilityID'].append(facility_id)
                data['Type'].append(line_type_name)
                data['Capacity'].append(line_capacity) 
                data['Floor'].append(floor_id) 
            i+1  
        line_counter = line_counter+1
    line = pd.DataFrame(data)
    return line

def generate_asset(line):
    asset_id_counter = 1
    data = {'id': [], 'Name': [], 'Type': [], 'FacilityID': [], 'LineID': [], 'LineFloor': []}
    for index, row in line.iterrows():
        line_id = row['id']
        line_type = row['Type']
        line_floor = row['Floor']
        facility_id = row['FacilityID']
        for line_info in assetProductionLines:
            if line_info['name'] == line_type:
                # types.extend(line_info['assets'])
                assets = line_info['assets']
                for i in assets:
                    data['id'].append(f"A{asset_id_counter}")
                    data['Name'].append(f"{i}-{line_id}-{facility_id}")
                    data['Type'].append(i)
                    data['LineID'].append(line_id)  
                    data['FacilityID'].append(facility_id)
                    data['LineFloor'].append(line_floor)   
                    asset_id_counter = asset_id_counter + 1
    asset = pd.DataFrame(data)
    return asset

def generate_supplier():
    data = {
        'id': [f"SUP{i+1}" for i in range(num_suppliers)],
        'Name': [f"Supplier{i+1}" for i in range(num_suppliers)],
        'Address': [f"Address{i+1}" for i in range(num_suppliers)],
        'Email': [f"supplier{i+1}@example.com" for i in range(num_suppliers)],
        'Phone': [f"123-456-{i+1000}" for i in range(num_suppliers)]
    }
    supplier_df = pd.DataFrame(data)
    return supplier_df

def generate_qms(wo,batch,recipe,material):
    qms_wo = wo[wo['Type'] == 'QMS']
    num_samples = len(qms_wo)
    qms_data = {
        'id': [f"QMS-{i+1}" for i in range(num_samples)],
        'name': [f"QMS-{row['BatchID']}-{row['id']}" for index, row in qms_wo.iterrows()],
        'ChangeRequestID': [f"CR-{i+1}" for i in range(num_samples)],
        'BatchID': qms_wo['BatchID'].tolist(),
        'AssetID': qms_wo['AssetID'].tolist(),
        'WOID': qms_wo['id'].tolist(),
        'FacilityID': qms_wo['FacilityID'].tolist()
    }
    qms_data['RecipeID'] = [batch.loc[batch['id'] == row['BatchID'], 'RecipeID'].iloc[0] for index, row in qms_wo.iterrows()]
    materialIDs_by_recipeID = get_materialIDs_by_recipeID(recipe)
    qms_data['MaterialID'] = [materialIDs_by_recipeID[recipeID] for recipeID in qms_data['RecipeID']]
    status = []
    for material_ids in qms_data['MaterialID']:
        material_status = "Passed"  # Default status
        for material_id in material_ids:
            # Get expiry date for current material
            expiry_date = material.loc[material['id'] == material_id, 'ExpiryDate'].iloc[0]
            expiry_date = pd.Timestamp(expiry_date)
            if expiry_date > pd.Timestamp(today):
                material_status = "Passed"
            else:
                material_status = "Failed"
                break
        status.append(material_status)
    qms_data['Status'] = status
    qms = pd.DataFrame(qms_data)
    return qms

def get_materialIDs_by_recipeID(recipe):
    # Group material DataFrame by recipeID and aggregate materialIDs into a list for each group
    materialIDs_by_recipeID = recipe.groupby('id')['MaterialID'].agg(list).to_dict()
    return materialIDs_by_recipeID

def generate_lims(wo):
    lims_wo = wo[wo['Type'] == 'LIMS']
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
        'name': [f"LIMS-{row['BatchID']}-{row['id']}" for index, row in lims_wo.iterrows()],
        'SampleID': [f"SMP-{i+1}" for i in range(num_samples)],
        'BatchID': lims_wo['BatchID'].tolist(),
        'Test': lims_wo['Task'].tolist(),
        'Result': results,
        'AssetID': lims_wo['AssetID'].tolist(),
        'WOID': lims_wo['id'].tolist(),
        'Status': statuses,
        'FacilityID': lims_wo['FacilityID'].tolist()
    }
    lims = pd.DataFrame(lims_data)
    return lims

def generate_batch_asset_rel(wo):
    rel_data = wo[['BatchID', 'AssetID']].drop_duplicates()
    return rel_data

def generate_upt(wo):
    upt_data = wo[['BatchID', 'UnitProcedureID']].drop_duplicates()
    upt_data['id'] = ['UPT-' + str(i+1) for i in range(len(upt_data))]
    upt_data['StartDate'] = pd.to_datetime('now')
    upt_data['EndDate'] = pd.to_datetime('now')
    upt_data['OperatorID'] = np.random.randint(1, 100, size=len(upt_data))
    upt_data['Status'] = np.random.choice(['InProgress', 'Completed', 'Failed'], size=len(upt_data))
    upt_data['Notes'] = ['' for _ in range(len(upt_data))]
    return upt_data

def generate_recipe_pm_rel(recipe):
    rel_data = recipe[['id', 'MaterialID']].drop_duplicates()
    return rel_data

family = generate_family()
products = generate_products()
po = generate_po(products, num_BOMs=100)
batch = generate_batch(po, products)
region = generate_region()
site = generate_site()
facility = generate_facility()
line = generate_line(facility)
material = generate_material()
supplier = generate_supplier()
recipe = generate_recipe(material)
plant_material = generate_plant_material(facility, material)
asset = generate_asset(line)
recipe_unitprocedure_mapping = generate_recipe_unitprocedure()
up = generate_unitprocedure()
wo = generate_wo(batch, recipe_unitprocedure_mapping,up,asset)
qms = generate_qms(wo,batch,recipe,material)
lims = generate_lims(wo)
batch_asset_rel = generate_batch_asset_rel(wo)
upt = generate_upt(wo)
recipe_pm = generate_recipe_pm_rel(recipe)

print(family.head())
print(products.head())
print(po.head())
print(batch.head())
print(region.head())
print(site.head())
print(facility.head())
print(line.head())
print(material.head())
print(supplier.head())
print(recipe.head())
print(plant_material.head())
print(asset.head())
print(recipe_unitprocedure_mapping.head())
print(up.head())
print(wo.head())
print(qms.head())
print(lims.head())
print(batch_asset_rel.head()) 
print(upt.head())
print(recipe_pm.head())

family.to_csv(os.path.join(data_folder, 'family.csv'), index=False)
products.to_csv(os.path.join(data_folder, 'products.csv'), index=False)
po.to_csv(os.path.join(data_folder, 'po.csv'), index=False)
batch.to_csv(os.path.join(data_folder, 'batch.csv'), index=False)
region.to_csv(os.path.join(data_folder, 'region.csv'), index=False)
site.to_csv(os.path.join(data_folder, 'site.csv'), index=False)
facility.to_csv(os.path.join(data_folder, 'facility.csv'), index=False)
line.to_csv(os.path.join(data_folder, 'line.csv'), index=False)
material.to_csv(os.path.join(data_folder, 'material.csv'), index=False)
supplier.to_csv(os.path.join(data_folder, 'supplier.csv'), index=False)
recipe.to_csv(os.path.join(data_folder, 'recipe.csv'), index=False)
plant_material.to_csv(os.path.join(data_folder, 'plant_material.csv'), index=False)
asset.to_csv(os.path.join(data_folder, 'asset.csv'), index=False)
recipe_unitprocedure_mapping.to_csv(os.path.join(data_folder, 'recipe_up_mapping.csv'), index=False)
up.to_csv(os.path.join(data_folder, 'up.csv'), index=False)
wo.to_csv(os.path.join(data_folder, 'wo.csv'), index=False)
qms.to_csv(os.path.join(data_folder, 'qms.csv'), index=False)
lims.to_csv(os.path.join(data_folder, 'lims.csv'), index=False)
batch_asset_rel.to_csv(os.path.join(data_folder, 'batch_asset_rel.csv'), index=False)
upt.to_csv(os.path.join(data_folder, 'upt.csv'), index=False)
recipe_pm.to_csv(os.path.join(data_folder, 'recipe_pm.csv'), index=False)