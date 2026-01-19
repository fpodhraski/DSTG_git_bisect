import networkx as nx

def load_dag_from_git_log(path="commits.txt"):
    G = nx.DiGraph()

    with open(path, "r", encoding="utf-8") as f:
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


def find_best_bisect_node(G, good, bad):
    Abad = ancestors_including_self(G, bad)
    Agood = ancestors_including_self(G, good)

    C = Abad - Agood
    if not C:
        raise RuntimeError("Skup kandidata je prazan – good nije predak bad-a.")

    n = len(C)
    best = None
    best_w = float("inf")

    for x in C:
        k = len(ancestors_including_self(G, x) & C)
        w = max(k, n - k)

        if w < best_w:
            best_w = w
            best = x

    return best, best_w, C


if __name__ == "__main__":
    #UNOS HASHEVA
    GOOD = "e293f998a163db78cfea0f3b3f121d91807920d0"
    BAD  = "704c34e21f7468fc72c33aa843051c7949ebeccd"

    G = load_dag_from_git_log("commitsReact.txt")
    best, w, C = find_best_bisect_node(G, GOOD, BAD)

    print("=== Git bisect (real repo) ===")
    print(f"Good commit: {GOOD}")
    print(f"Bad commit:  {BAD}")
    print(f"|C| = {len(C)}")
    print(f"Preporučeni sljedeći test: {best}")
    print(f"W(best) = {w}")
