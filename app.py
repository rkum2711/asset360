import streamlit as st
import pyTigerGraph as tg
from pyvis.network import Network
from layout import footer
import streamlit.components.v1 as components
import api
import json
import re

with open('./config.json', 'r') as file:
    config = json.load(file)

html_file_path = config["html_file_path"]
chatgpt_icon = config["chatgpt_icon"]

question_dict = config["question_dict"]
options_list = config["options_list"]
question_list = [key for key in question_dict.keys()]
question_list2 = question_list

graph = tg.TigerGraphConnection(
    host=st.secrets["host"],
    graphname=st.secrets["graphname"],
    gsqlSecret=st.secrets["apiToken"])

# authToken = graph.getToken(st.secrets["apiToken"], "10000000")
authToken = graph.getToken(st.secrets["apiToken"])
authToken = authToken[0]
graph.echo()

generated_nodes_edges =  api.generated_nodes_edges
save_graph_file =  api.save_graph_file
display_legend =  api.display_legend

@st.cache_data
def get_asset_data():
    with st.spinner("Connecting GraphDB"):
        asset_ids_raw = graph.runInstalledQuery("get_assetid")
        list_asset_ids = sorted([row["id"] for row in asset_ids_raw[0]["T"]])
        facility_ids_raw = graph.runInstalledQuery("get_facility")
        list_facility = sorted([row["Name"] for row in facility_ids_raw[0]["T"]])
        site_ids_raw = graph.runInstalledQuery("get_sites")
        list_site = sorted([row["Name"] for row in site_ids_raw[0]["T"]])
        rigion_ids_raw = graph.runInstalledQuery("get_region")
        list_region = sorted([row["Name"] for row in rigion_ids_raw[0]["T"]])
        return list_asset_ids,list_facility,list_site, list_region
    
def app():
    footer()
    st.title("Asset 360 - Accelerator")
    # st.image(gdm_image, caption='', width=1000)
    list_asset_ids,list_facility,list_site, list_region = get_asset_data()
    col1, col2, col3, col4 = st.columns(4)
    option = st.sidebar.radio("Select Option", options_list)
    display_legend(st)
    if option == options_list[0]:
        with col1:
            st.success(f"Total Assets: {len(list_asset_ids)}")
        with col2:
            st.info(f"Total Facilities : {len(list_facility)}")
        with col3:
            st.info(f"Total Sites : {len(list_site)}")
        with col4:
            st.info(f"Total Region : {len(list_region)}")
        st.subheader(options_list[0])
        query_type = st.selectbox("Select Questions? ", question_list)
        if st.button("Search"):
            for q in question_list:
                if query_type == q:
                    st.subheader(query_type)
                    with st.spinner("Executing query..."):
                        try:
                            with st.spinner("Data Loading ...."):
                                if q == question_list[0]:
                                    graphData = graph.runInstalledQuery(question_dict[q])
                                elif q == question_list[1]:
                                    graphData = graph.runInstalledQuery(question_dict[q], 
                                                                        params= {"years": 2})
                                elif q == question_list[2]:
                                    graphData = graph.runInstalledQuery(question_dict[q])
                                elif q == question_list[3]:
                                    graphData = graph.runInstalledQuery(question_dict[q])
                                elif q == question_list[4]:
                                    graphData = graph.runInstalledQuery(question_dict[q])
                                with st.spinner("Converting into Graph ..."):
                                    query_number = 1
                                    network = generated_nodes_edges(graphData,graph,query_number)
                                    save_graph_file(components,network,html_file_path)
                        except Exception as e:
                            st.error(f"Error executing query: {e}")
                        st.write("Query execution complete")
    elif option == options_list[1]:
        st.subheader(options_list[1])
        with col1:
            st.success(f"Total Assets: {len(list_asset_ids)}")
        with col2:
            st.info(f"Total Facilities : {len(list_facility)}")
        with col3:
            st.info(f"Total Sites : {len(list_site)}")
            site_identifier = st.selectbox("Select Sites", list_site)
        with col4:
            st.info(f"Total Region : {len(list_region)}")
        if st.button("Search"):
            with st.spinner("Executing query..."):
                try:
                    with st.spinner("Data Loading ...."):
                        graphData = graph.runInstalledQuery("assets_filters", 
                                                            params= {"sitename": site_identifier})
                        with st.spinner("Converting into Graph ..."):
                            query_number = 1
                            network = generated_nodes_edges(graphData,graph,query_number)
                            save_graph_file(components,network,html_file_path)
                except Exception as e:
                    st.error(f"Error executing query: {e}")
                st.write("Query execution complete")

    elif option == options_list[2]:
        st.subheader(options_list[2])
        with col1:
            st.success(f"Total Assets: {len(list_asset_ids)}")
            asset_identifier = st.selectbox("Select assets", list_asset_ids)
        with col2:
            st.info(f"Total Facilities : {len(list_facility)}")
        with col3:
            st.info(f"Total Sites : {len(list_site)}")
        with col4:
            st.info(f"Total Region : {len(list_region)}")
        if st.button("Search"):
            with st.spinner("Executing query..."):
                try:
                    with st.spinner("Data Loading ...."):
                        graphData = graph.runInstalledQuery("Asset_lineage", 
                                                            params= {"Asset_id": asset_identifier})
                        with st.spinner("Converting into Graph ..."):
                            query_number = 1
                            network = generated_nodes_edges(graphData,graph,query_number)
                            save_graph_file(components,network,html_file_path)
                except Exception as e:
                    st.error(f"Error executing query: {e}")
                st.write("Query execution complete")
    elif option == options_list[3]:
        st.subheader(options_list[3])
        with col1:
            st.success(f"Total Assets: {len(list_asset_ids)}")
        with col2:
            st.info(f"Total Facilities : {len(list_facility)}")
        with col3:
            st.info(f"Total Sites : {len(list_site)}")
        with col4:
            st.info(f"Total Region : {len(list_region)}")
        if st.button("Search"):
            with st.spinner("Executing query..."):
                try:
                    with st.spinner("Data Loading ...."):
                        graphData = graph.runInstalledQuery("Asset_maintenance")
                        with st.spinner("Converting into RESULT ..."):
                            features = []
                            for item in data:
                                for vs_item in item["VS_XXX"]:
                                    features.append({
                                        "Asset": vs_item["attributes"]["a"],
                                        "QMS Count": vs_item["attributes"]["qmsCount"],
                                        "Spare Replacement Count": vs_item["attributes"]["spareReplacementCount"],
                                        "Total Calibration": len(vs_item["attributes"]["totalCalibration"]),
                                        "Total Workorder": len(vs_item["attributes"]["totalWorkorder"]),
                                        "Total Maintenance": len(vs_item["attributes"]["totalmaintenance"])
                                    })
                        st.table(features)
                except Exception as e:
                    st.error(f"Error executing query: {e}")
                st.write("Query execution complete")
    elif option == options_list[4]:
        st.image(chatgpt_icon, width=50)
        ai_search = st.text_input("AI CHATBOT", "")
        with col1:
            st.success(f"Total Assets: {len(list_asset_ids)}")
        with col2:
            st.info(f"Total Facilities : {len(list_facility)}")
        with col3:
            st.info(f"Total Sites : {len(list_site)}")
        with col4:
            st.info(f"Total Region : {len(list_region)}")
        if st.button("RUN"):
            query_number = 1
            with st.spinner("Executing query..."):
                try:
                    with st.spinner("Data Loading ...."):
                        downtime = re.findall(r'Throughput?', ai_search, flags=re.IGNORECASE)
                        high = re.findall(r'high?', ai_search, flags=re.IGNORECASE)
                        low = re.findall(r'low?', ai_search, flags=re.IGNORECASE)
                        asset = re.findall(r'asset(?:es|s)?', ai_search, flags=re.IGNORECASE)
                        if downtime:
                            if high:
                                graphData = graph.runInstalledQuery("high_throughput")
                            elif low:
                                graphData = graph.runInstalledQuery("low_throughput")
                            else:
                                graphData = graph.runInstalledQuery("high_throughput")
                            with st.spinner("Converting into RESULT ..."):
                                data = []
                                for item in graphData[0]["T"]:
                                    asset_value = item["a"]
                                    throughput_value = item["Throughput"]
                                    data.append({"asset": asset_value, "Throughput": throughput_value})
                            st.table(data)
                        elif asset:
                            asset_id = re.findall(r'A\d+', ai_search)[0]
                            try:
                                graphData = graph.runInstalledQuery("Asset_viewer", params={"AssetID": asset_id})
                                with st.spinner("Converting into Graph ..."):
                                    network = generated_nodes_edges(graphData,graph,query_number)
                                    save_graph_file(components,network,html_file_path)
                            except Exception as e:
                                st.error(f"Error executing query:{query_type}: {e}")
                            st.write("Query execution complete")
                        else:
                            st.error("Please Try Again")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
                st.write("Query execution complete")
if __name__ == "__main__":
    app()