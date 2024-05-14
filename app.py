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
        return list_asset_ids

def app():
    footer()
    st.title("Asset 360- Accelerator")
    # st.image(gdm_image, caption='', width=1000)
    list_asset_ids = get_asset_data()
    col1, col2, col3 = st.columns(3)
    option = st.sidebar.radio("Select Option", options_list)
    display_legend(st)
    if option == options_list[0]:
        with col1:
            st.info(f"Total Assets: {len(list_asset_ids)}")
        # with col2:
        #     st.success(f"Total Successful Batches : {}")
        asset_identifier = st.selectbox("Select Asset", list_asset_ids)
        # question_list.remove(question_list[1])
        query_type = st.selectbox("Select Questions? ", question_list)
        if st.button("Search"):
            for q in question_list:
                if query_type == q:
                    st.subheader(query_type)
                    with st.spinner("Executing query..."):
                        try:
                            with st.spinner("Data Loading ...."):
                                graphData = graph.runInstalledQuery(question_dict[q], params={"Asset_id": asset_identifier})
                            with st.spinner("Converting into Graph ..."):
                                if query_type == question_list[0]:
                                    query_number = 1
                                    network = generated_nodes_edges(graphData,graph,query_number)
                                else:
                                    st.error(f"Error executing query:{query_type}")
                                save_graph_file(components,network,html_file_path)
                        except Exception as e:
                            st.error(f"Error executing query:{query_type}: {e}")
                        st.write("Query execution complete")
    elif option == options_list[1]:
        with col1:
            st.info(f"Total Assets: {len(list_asset_ids)}")
        # with col2:
        #     st.success(f"Total Successful Batches : {len(list_passs_batch_ids)}")
        # with col3:
        #     st.error(f"Total Batches Failed: {len(list_failed_batch_ids)}")
        st.subheader(options_list[1])
        with st.spinner("Executing query..."):
            try:
                with st.spinner("Data Loading ...."):
                    graphData = graph.runInstalledQuery("all_asset_lineage")
                with st.spinner("Converting into Graph ..."):
                    query_number = 1
                    network = generated_nodes_edges(graphData,graph,query_number)
                    save_graph_file(components,network,html_file_path)
            except Exception as e:
                st.error(f"Error executing query: {e}")
            st.write("Query execution complete")
if __name__ == "__main__":
    app()