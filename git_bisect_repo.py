import networkx as nx
import random
import math

def load_dag_from_git_log(path="commits.txt"):
    G = nx.DiGraph()
    with open(path, "r", encoding="utf-16") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            commit = parts[0]
            parents = parts[1:]

            G.add_node(commit)
            for p in parents:
                # parent -> child
                G.add_edge(p, commit)

    if not nx.is_directed_acyclic_graph(G):
        raise RuntimeError("Graf nije DAG (neočekivano za git).")

    return G


def ancestors_including_self(G, node):
    return set(nx.ancestors(G, node)) | {node}


def find_best_bisect_node(G, good, bad, visited=None):
    Abad = ancestors_including_self(G, bad)
    Agood = ancestors_including_self(G, good)

    C = Abad - Agood
    if visited:
        C = C - visited
    if not C:
        return None, 0, C 

    n = len(C)
    best = None
    best_w = float("inf")
    
    candidates_to_check = list(C)
    if len(C) > 200: 
        candidates_to_check = random.sample(list(C), 100)

    for x in candidates_to_check:
        k = len(ancestors_including_self(G, x) & C)
        w = max(k, n - k)

        if w < best_w:
            best_w = w
            best = x

    return best, best_w, C


def is_bug_present(G, current_node, secret_bad_commit):
    if current_node == secret_bad_commit:
        return True
    return nx.has_path(G, secret_bad_commit, current_node)

def run_single_simulation(G, good_start, bad_start, secret_bad_commit):
    current_good = good_start
    current_bad = bad_start
    steps = 0
    visited = set()
    MAX_STEPS = 90 
    
    while steps < MAX_STEPS:
        best_node, w, candidates = find_best_bisect_node(G, current_good, current_bad, visited)
        
        if len(candidates) <= 1:
            return steps
        
        if best_node is None:
            break

        steps += 1
        visited.add(best_node)
        
        if is_bug_present(G, best_node, secret_bad_commit):
            current_bad = best_node
        else:
            current_good = best_node
            
    return steps

def run_experiment_batch(filename, num_simulations=5):
    print(f"Učitavam graf iz {filename}...")
    G = load_dag_from_git_log(filename)
    
    if len(G) == 0: return None

    try:
        topo = list(nx.topological_sort(G))
        initial_good = topo[0]
        initial_bad = topo[-1]
    except:
        print("Graf sadrži cikluse (nije DAG). Nemoguće simulirati.")
        return None

    n = G.number_of_nodes()
    e = G.number_of_edges()
    if n > 1:
        density = e / (n * (n - 1))
    else:
        density = 0
    
    print(f"\n=== STRUKTURA GRAFA (Matematički parametri) ===")
    print(f"Broj čvorova |V|: {n}")
    print(f"Broj bridova |E|: {e}")
    print(f"Gustoća grafa D:  {density:.5f}")
    
    log_n = math.log2(n)
    print(f"Teorijski donji limit (log2 n): {log_n:.2f}")

    print(f"\n=== REZULTATI SIMULACIJE ===")
    print(f"{'Simulacija #':<15} | {'Broj kandidata':<15} | {'Koraci (Bisect)':<15} | {'Linearno (N/2)':<15}")
    print("-" * 75)

    targets = []
    potential_targets = list(nx.ancestors(G, initial_bad) - nx.ancestors(G, initial_good))
    if potential_targets:
        targets = random.sample(potential_targets, min(num_simulations, len(potential_targets)))

    total_bisect = 0
    
    for i, target in enumerate(targets):
        steps = run_single_simulation(G, initial_good, initial_bad, target)
        total_bisect += steps
        
        candidates_n = len(ancestors_including_self(G, initial_bad) - ancestors_including_self(G, initial_good))
        lin_steps = candidates_n // 2
        
        print(f"{i+1:<15} | {candidates_n:<15} | {steps:<15} | {lin_steps:<15}")

    return G, (total_bisect / len(targets))


if __name__ == "__main__":
    moj_file = "commits.txt"
    
    result = run_experiment_batch(moj_file, num_simulations=10)

    if result:
        G, avg_real_steps = result
        
        print("\n=== ANALIZA ODSTUPANJA OD TEORIJE ===")
        
        G_lin = nx.DiGraph()
        nodes = [str(i) for i in range(len(G))]
        for i in range(len(nodes)-1): 
            G_lin.add_edge(nodes[i], nodes[i+1])
        
        print("Simuliram pretragu na idealnom linearnom grafu iste veličine...")
        steps_ideal = run_single_simulation(G_lin, nodes[0], nodes[-1], nodes[len(nodes)//2])
        
        print(f"1. Idealni slučaj (Linearni niz): {steps_ideal} koraka")
        print(f"2. Stvarni slučaj (Tvoj DAG):     {avg_real_steps:.1f} koraka (prosjek)")
        
        diff = avg_real_steps - steps_ideal
        if steps_ideal > 0:
            overhead_pct = (diff / steps_ideal) * 100
        else:
            overhead_pct = 0
            
        print("-" * 50)
        print(f"TOPOLOŠKI PENAL (Utjecaj grananja): +{diff:.1f} koraka")
        print(f"ODSTUPANJE OD OPTIMUMA: {overhead_pct:.1f}%")
        
        if diff > 0.5:
            print("ZAKLJUČAK: Struktura DAG-a (grananja) mjerljivo degradira performanse u odnosu na linearni niz.")
        else:
            print("ZAKLJUČAK: Graf je topološki vrlo uredan, performanse su optimalne.")