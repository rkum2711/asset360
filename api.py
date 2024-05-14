from pyvis.network import Network
import json

with open('./config.json', 'r') as file:
    config = json.load(file)

legend_mapping = config["legend_mapping"]

def generated_nodes_edges(data,graph,query_number):
    net = Network(
        notebook=False,
        cdn_resources="remote",
        bgcolor="white",
        font_color="black",
        height="750px",
        width="100%",
        select_menu=True,
        filter_menu=True
    )
    # net.show_buttons(filter_= ['nodes', 'edges'])
    added_nodes = set()
    for record in data:
        for item in record["T"]:
            for key, value in item.items():
                if isinstance(value, dict):
                    if "from_id" in value and "to_id" in value:
                        source_node_id = value["from_id"]
                        target_node_id = value["to_id"]
                        source_node_type = value["from_type"]
                        target_node_type = value["to_type"]
                        edge_id = key
                        edge_name = value["e_type"]
                        node_list = [{"id": source_node_id, "type": source_node_type},
                                    {"id": target_node_id, "type": target_node_type}]
                    if source_node_id is not None and target_node_id is not None:
                        for node in node_list:
                            if node["id"] not in added_nodes:
                                node_prop = graph.getVerticesById(vertexType = node["type"], vertexIds = node["id"])
                                node_property = node_prop[0]['attributes'] if node_prop else {}
                                # Adding Nodes
                                net.add_node(node["id"], label=node["type"].upper(), title=node_property)
                                added_nodes.add(node["id"])
                        # Adding edge
                        net.add_edge(source_node_id, target_node_id, title=f"Edge {edge_name}")
    for node in net.nodes:
        for key in legend_mapping.keys(): 
            if query_number in [1]:
                if node['label'] == key:
                    node['label'] += ":" + node['id'] 
                    node['color'] = legend_mapping[key]
        node['label'] += ":" + node['id'] 
        title_html_text = " Attributes:<br>"
        for key, value in node['title'].items():
            title_html_text += f"{key}:</b>{value}<br>"
            node['title'] = title_html_text
    return net

def save_graph_file(components,network,html_file_path):
    network.save_graph(html_file_path)
    with open(html_file_path, 'r', encoding='utf-8') as HtmlFile:
        source_code = HtmlFile.read() 
    components.html(source_code, height=1200, width=1000)

def display_legend(st):
    legend_html = "<h3>Legend</h3>"
    count = 0
    for key, value in legend_mapping.items():
        if count % 3 == 0:
            if count != 0:
                legend_html += "</div>"
            legend_html += "<div>"
        legend_html += f'<span style="color:{value}; font-weight:bold;">&#9632;</span> {key} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        count += 1
    if count % 3 != 0:
        legend_html += "</div>"
    st.sidebar.markdown(legend_html, unsafe_allow_html=True)
