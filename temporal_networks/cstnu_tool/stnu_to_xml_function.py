import random
import xml.etree.ElementTree as ET
from xml.dom import minidom


def prettify(element):
    """Return a pretty-printed XML string for the Element, excluding the first element."""
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    # Skip the xml declaration from minidom and the root element
    pretty_xml_as_string = reparsed.toprettyxml(indent="")
    lines = pretty_xml_as_string.split('\n')
    # Remove the first line which contains the XML declaration and empty lines
    return '\n'.join([line for line in lines[2:]])


def write_graphml(filename, ncontingent, networktype, nedges, nvertices, name, edges, nodes):
    # Note: The namespace and schemaLocation are set manually in the header, not here
    graphml = ET.Element("graphml")

    # Adding key elements
    keys = [
        ("nContingent", "graph", "Number of contingents in the graph", "0"),
        ("NetworkType", "graph", "Network Type", "CSTNU"),
        ("nEdges", "graph", "Number of edges in the graph", "0"),
        ("nVertices", "graph", "Number of vertices in the graph", "0"),
        ("Name", "graph", "Graph Name", " "),
        ("x", "node", "The x coordinate for the visualization. A positive value.", "0"),
        ("y", "node", "The y coordinate for the visualization. A positive value.", "0"),
        ("Type", "edge", "Type: Possible values: contingent|requirement|derived|internal.", "requirement"),
        ("Value", "edge", "Value for STN edge. Format: 'integer'", " "),
        ("LabeledValue", "edge", "Case Value. Format: 'LC(NodeName):integer' or 'UC(NodeName):integer'", " ")
    ]

    for key_id, key_for, desc_text, default_value in keys:
        key_element = ET.SubElement(graphml, "key", id=key_id)
        key_element.set("for", key_for)
        desc = ET.SubElement(key_element, "desc")
        desc.text = desc_text
        default = ET.SubElement(key_element, "default")
        default.text = default_value

    # Add data elements to the graph
    graph = ET.SubElement(graphml, "graph", edgedefault="directed")
    data_items = [
        ("nContingent", str(ncontingent)),
        ("NetworkType", str(networktype)),
        ("nEdges", str(nedges)),
        ("nVertices", str(nvertices)),
        ("Name", f'{name}.stnu'),
    ]

    for key, value in data_items:
        data_element = ET.SubElement(graph, "data", key=key)
        data_element.text = value

    for node_id, x, y in nodes:
        node = ET.SubElement(graph, "node", id=node_id)
        ET.SubElement(node, "data", key="x").text = x
        ET.SubElement(node, "data", key="y").text = y

    for edge_id, source, target, type_, value in edges:
        edge = ET.SubElement(graph, "edge", id=edge_id, source=source, target=target)
        ET.SubElement(edge, "data", key="Type").text = type_

        if type_ == "requirement":
            ET.SubElement(edge, "data", key="Value").text = value
        elif type_ == "contingent":
            ET.SubElement(edge, "data", key="LabeledValue").text = value

    # Get pretty XML string for elements after the root
    pretty_xml_as_string = prettify(graphml)

    # Manually format the first three lines as specified and write everything to file
    with open(filename, "w", encoding="UTF-8") as file:
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns/graphml"\n')
        file.write('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
        file.write('xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns/graphml">\n')
        file.write(pretty_xml_as_string)


def stnu_to_xml(stnu, name_graph, directory):
    edges = []
    for node_from in stnu.nodes:
        for node_to in stnu.nodes:
            if node_to in stnu.edges[node_from]:
                edge = stnu.edges[node_from][node_to]
                node_from_str = stnu.translation_dict[node_from]
                node_to_str = stnu.translation_dict[node_to]
                if edge.weight is not None:
                    edges.append((f'e{node_from_str}-{node_to_str}', node_from_str, node_to_str, "requirement", str(edge.weight)))
                if edge.uc_weight is not None:
                    label = edge.uc_label
                    edges.append((f'e{node_from_str}-{node_to_str}', node_from_str, node_to_str, "contingent", f'UC({label}):{edge.uc_weight}'))
                if edge.lc_weight is not None:
                    label = edge.lc_label
                    edges.append((f'e{node_from_str}-{node_to_str}', node_from_str, node_to_str, "contingent", f'LC({label}):{edge.lc_weight}'))

    nodes = []
    for node in stnu.nodes:
        node_str = stnu.translation_dict[node]
        nodes.append((node_str, str(random.randint(40, 200)), str(random.randint(40, 200))))

    ncontingent = len(stnu.contingent_links)
    networktype = "STNU"
    nedges = len(edges)
    nvertices = len(stnu.nodes)
    write_graphml(f"{directory}/{name_graph}.stnu", ncontingent, networktype, nedges, nvertices, name_graph, edges, nodes)


