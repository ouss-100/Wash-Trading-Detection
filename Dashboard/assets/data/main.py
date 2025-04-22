import pandas as pd
import networkx as nx
from collections import defaultdict

# Load dataset
df = pd.read_csv('nft_transactions.csv')

# STEP 1: Build transaction graph per NFT
graphs = {}
for _, row in df.iterrows():
    token_id = row['token_id']
    from_acc = row['from_account']
    to_acc = row['to_account']
    price = row['price']
    tx_time = row['tx_timestamp']
    
    if token_id not in graphs:
        graphs[token_id] = nx.DiGraph()
    graphs[token_id].add_edge(from_acc, to_acc, timestamp=tx_time, price=price)

# Storage for all detections
detections = {
    "self_trades": [],
    "zero_risk": [],
    "common_funder": [],
    "common_exit": [],
    "repeated_scc": []
}

past_sccs = set()  # To track past suspicious components

# STEP 2: Analyze each graph
for token_id, G in graphs.items():
    sccs = list(nx.strongly_connected_components(G))
    
    for scc in sccs:
        subG = G.subgraph(scc)
        scc_id = f"{token_id}_{hash(frozenset(scc))}"

        # 1. Self-Trades
        for node in subG.nodes:
            if subG.has_edge(node, node):
                detections["self_trades"].append((token_id, node))
        
        # 2. Zero-Risk Position: Check if all accounts end with 0 ETH gain
        total_gains = df[(df['token_id'] == token_id) & 
                         (df['from_account'].isin(scc) | df['to_account'].isin(scc))]
        
        balances = defaultdict(float)
        for _, row in total_gains.iterrows():
            balances[row['from_account']] -= row['price']
            balances[row['to_account']] += row['price']
        
        nonzero_accounts = [acc for acc, val in balances.items() if round(val, 8) != 0]
        if len(nonzero_accounts) == 0:
            detections["zero_risk"].append((token_id, list(scc)))

        # 3. Common Funder
        funder_counts = defaultdict(set)
        for _, row in total_gains.iterrows():
            funder_counts[row['from_account']].add(row['to_account'])
        
        for funder, targets in funder_counts.items():
            if len(targets.intersection(scc)) >= 2:
                detections["common_funder"].append((token_id, funder, list(targets)))
        
        # 4. Common Exit
        receivers = defaultdict(int)
        for _, row in total_gains.iterrows():
            receivers[row['to_account']] += 1
        
        sorted_receivers = sorted(receivers.items(), key=lambda x: x[1], reverse=True)
        if sorted_receivers and sorted_receivers[0][0] in scc:
            detections["common_exit"].append((token_id, sorted_receivers[0][0]))

        # 5. Repeated SCC Participants (same as before)
        key = frozenset(scc)
        if key in past_sccs:
            detections["repeated_scc"].append((token_id, list(scc)))
        else:
            past_sccs.add(key)

# STEP 3: Summary
print("Wash Trading Detection Summary:")
for category, items in detections.items():
    print(f"{category}: {len(items)} detected")

# Optional: Save to CSV
for category, items in detections.items():
    pd.DataFrame(items).to_csv(f"{category}.csv", index=False)
