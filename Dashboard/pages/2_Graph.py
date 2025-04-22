import streamlit as st
import pandas as pd
import networkx as nx
from streamlit_agraph import agraph, Node, Edge, Config
from utils.data_loader import load_data


def create_network_graph(df):
    G = nx.Graph()

    for _, row in df.iterrows():
        from_account = str(row['from_account'])
        to_account = str(row['to_account'])
        seller_account = str(row['seller_account'])
        winner_account = str(row['winner_account']) if pd.notna(row['winner_account']) else None
        collection_name = str(row['collection_name'])

        G.add_node(from_account, type='account')
        G.add_node(to_account, type='account')
        G.add_node(seller_account, type='seller')
        if winner_account:
            G.add_node(winner_account, type='winner')
        G.add_node(collection_name, type='collection')

        G.add_edge(from_account, to_account,
                   weight=row['usd_price'],
                   token=row['token'],
                   price=row['price'])

        G.add_edge(from_account, collection_name)
        G.add_edge(to_account, collection_name)

    return G


def visualize_with_agraph(graph):
    nodes = []
    edges = []

    for node in graph.nodes():
        node_type = graph.nodes[node].get('type', 'account')
        node_id = str(node)
        label = node[:10] + "..." if isinstance(node, str) and len(node) > 10 else str(node)

        if node_type == 'collection':
            nodes.append(Node(id=node_id, label=label, size=25, color="#FFA500", shape="diamond"))
        elif node_type == 'seller':
            nodes.append(Node(id=node_id, label=label, size=20, color="#FF6347", shape="square"))
        elif node_type == 'winner':
            nodes.append(Node(id=node_id, label=label, size=20, color="#32CD32", shape="triangle"))
        else:
            nodes.append(Node(id=node_id, label=label, size=15, color="#6495ED", shape="dot"))

    for edge in graph.edges():
        edge_data = graph.get_edge_data(*edge)
        source = str(edge[0])
        target = str(edge[1])
        edges.append(Edge(
            source=source,
            target=target,
            width=edge_data.get('weight', 1) / 10,
            label=f"{edge_data.get('price', 0)} {edge_data.get('token', '')}",
            color="#888888"
        ))

    config = Config(
        width="100%",
        height=800,
        directed=False,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=True,
        node={'labelProperty': 'label'},
        link={'highlightColor': '#8BD3E6'},
        physics_config={
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -2000,   # Stronger repulsion
                "centralGravity": 0.05,           # Less central pull
                "springLength": 500,              # Much more distance between connected nodes
                "springConstant": 0.001,          # Weaker pull between connected nodes
                "damping": 0.1,                   # Slower motion settling
                "avoidOverlap": 2                 # Avoid overlaps aggressively
            }
        }
)


    selected_node = agraph(nodes=nodes, edges=edges, config=config)
    return selected_node


def main():
    st.set_page_config(layout="wide")
    st.title("💸 Transaction Network Visualization")

    df = load_data()
    st.write("This graph shows connections between accounts based on NFT transactions.")

    min_usd = st.slider("Minimum USD Value",
                        min_value=0,
                        max_value=int(df['usd_price'].max()),
                        value=10)

    filtered_df = df[df['usd_price'] >= min_usd]

    if len(filtered_df) == 0:
        st.warning("No transactions meet the selected criteria.")
        return

    G = create_network_graph(filtered_df)
    selected_node = visualize_with_agraph(G)

    st.subheader("📊 Network Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Nodes", len(G.nodes()))
    col2.metric("Total Edges", len(G.edges()))
    col3.metric("Average Degree", f"{sum(dict(G.degree()).values()) / len(G.nodes()):.2f}")

    st.subheader("⭐ Most Influential Accounts")

    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)

    top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]

    col1, col2 = st.columns(2)
    with col1:
        st.write("**By Number of Connections (Degree Centrality)**")
        for node, score in top_degree:
            st.write(f"- `{node}`: {score:.4f}")

    with col2:
        st.write("**By Bridge Potential (Betweenness Centrality)**")
        for node, score in top_betweenness:
            st.write(f"- `{node}`: {score:.4f}")

    # Node Info Card
    if selected_node:
        st.subheader("📌 Selected Node Information")
        node_id = selected_node  # It's a string
        node_type = G.nodes[node_id].get('type', 'Unknown')
        connections = list(G.neighbors(node_id))
        degree = G.degree(node_id)

        with st.expander("🔍 Node Details", expanded=True):
            st.markdown(f"**ID:** `{node_id}`")
            st.markdown(f"**Type:** `{node_type}`")
            st.markdown(f"**Degree (Connections):** `{degree}`")
            st.markdown("**Connections:**")
            for conn in connections:
                st.markdown(f"- `{conn}`")

            st.markdown("**Edges Info:**")
            for neighbor in connections:
                edge_data = G.get_edge_data(node_id, neighbor)
                if edge_data:
                    price = edge_data.get('price', 0)
                    token = edge_data.get('token', '')
                    st.markdown(f"- `{node_id}` → `{neighbor}`: **{price} {token}**")


if __name__ == "__main__":
    main()
